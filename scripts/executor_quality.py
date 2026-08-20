#!/usr/bin/env python3

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RUNS = ROOT / "executor" / "runs"
OUTBOX = ROOT / "executor" / "outbox"
PRODUCTS = ROOT / "products"
OFFERS = ROOT / "offers"

CORE_EXTENSIONS = {".csv", ".json", ".html", ".css", ".js", ".py", ".yml", ".yaml", ".xml", ".svg"}
CORE_KEYWORDS = {
    "template", "plantilla", "script", "dashboard", "generator", "generador",
    "automation", "automatización", "automacion", "app", "tool", "herramienta",
    "spreadsheet", "google sheet", "hoja de cálculo", "code", "código"
}


def load(path, default=None):
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def save(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def needs_core_asset(run, offer_html):
    text = " ".join([
        str(run.get("publication_copy") or ""),
        str(run.get("notes") or ""),
        offer_html,
    ]).lower()
    return any(keyword in text for keyword in CORE_KEYWORDS)


def has_core_asset(ref):
    directory = PRODUCTS / ref
    if not directory.exists():
        return False
    return any(
        path.is_file() and path.suffix.lower() in CORE_EXTENSIONS
        for path in directory.rglob("*")
    )


def normalize_primary_cta(html_text, blocked):
    if blocked:
        replacement = '<a class="primary" href="#" aria-disabled="true" style="pointer-events:none;opacity:.58">⏳ Producto en validación · pago deshabilitado</a>'
    else:
        replacement = '<a class="primary" href="https://cobramo.netlify.app/" target="_blank" rel="noreferrer">💸 Comprar / coordinar pago</a>'
    return re.sub(
        r'<a class="primary"[^>]*>.*?</a>',
        replacement,
        html_text,
        count=1,
        flags=re.I | re.S,
    )


def process(run_path):
    run = load(run_path, {}) or {}
    ref = str(run.get("payment_reference") or run_path.stem)
    if not ref.startswith("RANK-IAMO"):
        return False

    offer_path = OFFERS / ref / "index.html"
    offer_html = offer_path.read_text(encoding="utf-8") if offer_path.exists() else ""
    requires = needs_core_asset(run, offer_html)
    has_asset = has_core_asset(ref)
    blocked = requires and not has_asset

    previous = run.get("quality_status")
    run["quality_requires_core_asset"] = requires
    run["quality_has_core_asset"] = has_asset
    run["quality_status"] = "blocked_missing_core_asset" if blocked else "ready_to_sell"

    if blocked:
        run["status"] = "materialized_incomplete"
        run["outreach_sendable"] = 0
    elif run.get("status") == "materialized_incomplete":
        run["status"] = "materialized"

    save(run_path, run)

    outbox_path = OUTBOX / f"{ref}.json"
    outbox = load(outbox_path, None)
    if isinstance(outbox, dict):
        for item in outbox.get("items", []):
            if not isinstance(item, dict):
                continue
            item["quality_blocked"] = blocked
            if blocked and item.get("status") == "pending":
                item["status"] = "blocked_incomplete_product"
            elif not blocked and item.get("status") == "blocked_incomplete_product":
                item["status"] = "pending"
        save(outbox_path, outbox)

    if offer_path.exists():
        new_html = normalize_primary_cta(offer_html, blocked)
        if blocked and "Producto incompleto" not in new_html:
            marker = '<div class="ref">'
            warning = '<p style="color:#ffd35a;font-weight:800">Producto incompleto: esta oferta todavía no acepta pagos.</p>\n'
            new_html = new_html.replace(marker, warning + marker, 1)
        offer_path.write_text(new_html, encoding="utf-8")

    if blocked:
        print(f"{ref}: BLOCKED — core asset missing")
    else:
        print(f"{ref}: READY")
    return previous != run["quality_status"]


def main():
    if not RUNS.exists():
        print("No executor runs yet.")
        return
    count = 0
    for path in sorted(RUNS.glob("RANK-IAMO*.json")):
        process(path)
        count += 1
    print(f"Quality gate checked {count} executor runs")


if __name__ == "__main__":
    main()
