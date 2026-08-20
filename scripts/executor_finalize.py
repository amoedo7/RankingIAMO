#!/usr/bin/env python3

import html
import json
import re
import sys
import zipfile
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
RUNTIME = ROOT / "runtime"
RUNS = ROOT / "executor" / "runs"
OUTBOX = ROOT / "executor" / "outbox"
OFFERS = ROOT / "offers"
PRODUCTS = ROOT / "products"
ARTIFACTS = ROOT / "artifacts"
POLICY_PATH = ROOT / "executor" / "policy.json"
COBRAMO = "https://cobramo.netlify.app/"
PUBLIC_PRODUCT_BASE = "https://raw.githubusercontent.com/amoedo7/RankingIAMO/main/artifacts/"
ALLOWED_EXTENSIONS = {
    ".md", ".txt", ".csv", ".json", ".html", ".css", ".js", ".py",
    ".yml", ".yaml", ".xml", ".svg"
}
EMAIL_RE = re.compile(r"^[A-Z0-9._%+\-]+@[A-Z0-9.\-]+\.[A-Z]{2,}$", re.I)


def now_iso():
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def load_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def clean(value, limit=12000):
    if value is None:
        return ""
    return str(value).replace("\x00", "").strip()[:limit]


def extract_json(text):
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text, count=1, flags=re.I)
        text = re.sub(r"\s*```$", "", text, count=1)
    decoder = json.JSONDecoder()
    for index, char in enumerate(text):
        if char != "{":
            continue
        try:
            value, _ = decoder.raw_decode(text[index:])
            if isinstance(value, dict):
                return value
        except json.JSONDecodeError:
            continue
    raise ValueError("EjecutorIAMO no devolvió un objeto JSON válido")


def valid_http_url(value):
    try:
        parsed = urlparse(str(value))
    except Exception:
        return False
    return parsed.scheme in {"http", "https"} and bool(parsed.hostname)


def external_url(value):
    if not valid_http_url(value):
        return False
    host = (urlparse(str(value)).hostname or "").lower()
    if host in {"cobramo.netlify.app", "desarrollamo.com.ar", "www.desarrollamo.com.ar"}:
        return False
    if host in {"github.com", "www.github.com", "raw.githubusercontent.com", "raw.githack.com"}:
        path = urlparse(str(value)).path.lower()
        if "/amoedo7/" in path:
            return False
    return True


def safe_product_path(value):
    raw = clean(value, 180).replace("\\", "/")
    path = PurePosixPath(raw)
    if not raw or path.is_absolute() or ".." in path.parts or len(path.parts) > 4:
        return None
    if path.suffix.lower() not in ALLOWED_EXTENSIONS:
        return None
    return path


def normalize_benefits(value):
    if not isinstance(value, list):
        return []
    return [clean(item, 300) for item in value if clean(item, 300)][:6]


def normalize_product_files(value):
    if not isinstance(value, list):
        return []
    rows = []
    total = 0
    for item in value[:12]:
        if not isinstance(item, dict):
            continue
        path = safe_product_path(item.get("path"))
        content = clean(item.get("content"), 50000)
        if not path or not content:
            continue
        total += len(content.encode("utf-8"))
        if total > 300000:
            break
        rows.append({"path": str(path), "content": content})
    return rows


def normalize_prospects(value, offer_url, ref, max_count):
    if not isinstance(value, list):
        return []
    result = []
    seen = set()

    for item in value:
        if len(result) >= max_count or not isinstance(item, dict):
            break

        company = clean(item.get("company"), 160)
        website = clean(item.get("website"), 1000)
        contact_url = clean(item.get("contact_url"), 1000)
        evidence_url = clean(item.get("evidence_url"), 1000)
        email = clean(item.get("contact_email"), 320).lower()

        if not company or not external_url(evidence_url):
            continue
        if website and not external_url(website):
            website = ""
        if contact_url and not external_url(contact_url):
            contact_url = ""
        if email and not EMAIL_RE.fullmatch(email):
            email = ""
        if not email and not contact_url:
            continue

        identity = email or contact_url
        if identity in seen:
            continue
        seen.add(identity)

        subject = clean(item.get("subject"), 180) or f"Idea concreta para {company}"
        message = clean(item.get("message"), 6000)
        why_fit = clean(item.get("why_fit"), 1500)

        if "desarrollamo" not in message.lower():
            message = "Te escribo desde DesarrollAMO, el equipo de desarrollo y automatización.\n\n" + message
        if offer_url not in message:
            message += f"\n\nPodés ver la propuesta acá: {offer_url}"
        if ref not in message:
            message += f"\nReferencia de esta propuesta: {ref}"
        if "no te escribamos" not in message.lower() and "no te escriba" not in message.lower():
            message += "\n\nSi preferís que no te escribamos de nuevo, decímelo y listo."

        result.append({
            "company": company,
            "website": website,
            "contact_email": email,
            "contact_url": contact_url,
            "evidence_url": evidence_url,
            "why_fit": why_fit,
            "subject": subject,
            "message": message,
            "payment_reference": ref,
            "offer_url": offer_url,
            "channel": "email" if email else "contact_url",
            "status": "pending" if email else "prepared_not_sendable",
            "created_at": now_iso(),
            "sent_at": None,
            "gmail_message_id": None,
        })

    return result


def render_landing(name, ref, offer, product_url):
    headline = html.escape(clean(offer.get("headline"), 220) or f"Oferta {name}")
    subheadline = html.escape(clean(offer.get("subheadline"), 700))
    price = html.escape(clean(offer.get("price"), 80))
    currency = html.escape(clean(offer.get("currency"), 20))
    deliverable = html.escape(clean(offer.get("deliverable"), 2200))
    cta = html.escape(clean(offer.get("cta"), 180) or "Quiero esta solución")
    benefits = normalize_benefits(offer.get("benefits"))
    benefits_html = "".join(f"<li>{html.escape(item)}</li>" for item in benefits)
    price_html = f"<div class=\"price\">{price} {currency}</div>" if price else ""

    return f'''<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="theme-color" content="#0b1020">
<title>{headline} · DesarrollAMO</title>
<style>
*{{box-sizing:border-box}}body{{margin:0;background:radial-gradient(circle at 15% 0,#1c2e58,transparent 35%),#080b12;color:#f7f8ff;font:16px/1.55 system-ui,-apple-system,Segoe UI,sans-serif}}main{{width:min(880px,calc(100% - 32px));margin:auto;padding:70px 0}}.tag{{color:#67e8a8;text-transform:uppercase;letter-spacing:.16em;font-weight:800;font-size:12px}}h1{{font-size:clamp(42px,8vw,76px);line-height:.98;letter-spacing:-.055em;margin:16px 0}}.lead{{font-size:20px;color:#aeb7cc;max-width:720px}}.card{{margin-top:34px;padding:28px;border:1px solid #2b3349;border-radius:22px;background:linear-gradient(180deg,#151b2b,#0d111c);box-shadow:0 30px 80px #0008}}.price{{font-size:38px;font-weight:900;margin:4px 0 18px}}ul{{padding-left:22px}}li{{margin:9px 0}}.deliverable{{color:#cbd3e4;margin:22px 0}}.actions{{display:flex;gap:10px;flex-wrap:wrap;margin-top:24px}}a{{display:inline-block;padding:12px 16px;border-radius:12px;text-decoration:none;font-weight:800;border:1px solid #343d55;color:#fff}}a.primary{{background:#f8fafc;color:#0b1020;border-color:#f8fafc}}.ref{{margin-top:24px;color:#7f8aa4;font:12px ui-monospace,monospace}}footer{{margin-top:42px;color:#77839f;font-size:12px}}@media(max-width:520px){{main{{padding-top:42px}}.card{{padding:20px}}}}
</style>
</head><body><main>
<div class="tag">DesarrollAMO · propuesta generada por {html.escape(name)}</div>
<h1>{headline}</h1>
<p class="lead">{subheadline}</p>
<section class="card">
{price_html}
<ul>{benefits_html}</ul>
<div class="deliverable">{deliverable}</div>
<div class="actions">
<a class="primary" href="{COBRAMO}" target="_blank" rel="noreferrer">💸 {cta}</a>
<a href="{html.escape(product_url)}">📦 Ver producto</a>
</div>
<div class="ref">Referencia de pago: {html.escape(ref)}</div>
</section>
<footer>Solo cuentan pagos reales verificados. La referencia debe conservarse al coordinar el pago.</footer>
</main></body></html>'''


def main():
    result_path = Path(sys.argv[1]) if len(sys.argv) > 1 else RUNTIME / "executor_result.txt"
    context = load_json(RUNTIME / "executor_input.json")
    policy = load_json(POLICY_PATH)

    name = str(context["competitor_name"])
    ref = str(context["payment_reference"])
    expected_ref = f"RANK-{name}"
    if ref != expected_ref:
        raise SystemExit(f"Referencia inconsistente: {ref} != {expected_ref}")

    RUNS.mkdir(parents=True, exist_ok=True)
    OUTBOX.mkdir(parents=True, exist_ok=True)
    OFFERS.mkdir(parents=True, exist_ok=True)
    PRODUCTS.mkdir(parents=True, exist_ok=True)
    ARTIFACTS.mkdir(parents=True, exist_ok=True)

    raw_text = result_path.read_text(encoding="utf-8", errors="replace") if result_path.exists() else ""
    try:
        raw = extract_json(raw_text)
    except Exception as exc:
        record = {
            "schema_version": "1.0",
            "competitor_name": name,
            "payment_reference": ref,
            "status": "invalid_executor_output",
            "error": str(exc),
            "finished_at": now_iso(),
        }
        (RUNS / f"{ref}.json").write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"{ref}: invalid_executor_output")
        return

    offer = raw.get("offer") if isinstance(raw.get("offer"), dict) else {}
    product = raw.get("product") if isinstance(raw.get("product"), dict) else {}
    product_files = normalize_product_files(product.get("files"))

    if not product_files:
        product_files = [{
            "path": "README.md",
            "content": "# " + (clean(product.get("title"), 180) or name) + "\n\n" +
                       (clean(product.get("summary"), 4000) or clean(offer.get("deliverable"), 4000)) + "\n",
        }]

    product_dir = PRODUCTS / ref
    product_dir.mkdir(parents=True, exist_ok=True)
    for item in product_files:
        destination = product_dir / item["path"]
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(item["content"], encoding="utf-8")

    zip_path = ARTIFACTS / f"{ref}-product.zip"
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(product_dir.rglob("*")):
            if path.is_file():
                archive.write(path, arcname=path.relative_to(product_dir))

    offer_url = str(context["official_offer_url"])
    product_url = PUBLIC_PRODUCT_BASE + zip_path.name
    offer_dir = OFFERS / ref
    offer_dir.mkdir(parents=True, exist_ok=True)
    (offer_dir / "index.html").write_text(render_landing(name, ref, offer, product_url), encoding="utf-8")

    prospects = normalize_prospects(
        raw.get("prospects"),
        offer_url,
        ref,
        int(policy.get("max_prospects_per_iamo", 3)),
    )
    outbox = {
        "schema_version": "1.0",
        "competitor_name": name,
        "payment_reference": ref,
        "offer_url": offer_url,
        "product_url": product_url,
        "items": prospects,
        "created_at": now_iso(),
    }
    (OUTBOX / f"{ref}.json").write_text(json.dumps(outbox, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    record = {
        "schema_version": "1.0",
        "competitor_name": name,
        "competitor_number": context.get("competitor_number"),
        "payment_reference": ref,
        "status": "materialized",
        "offer_url": offer_url,
        "product_url": product_url,
        "product_zip": str(zip_path.relative_to(ROOT)),
        "product_files": [item["path"] for item in product_files],
        "outreach_total": len(prospects),
        "outreach_sendable": sum(1 for item in prospects if item["status"] == "pending"),
        "publication_copy": clean(raw.get("publication_copy"), 5000),
        "notes": clean(raw.get("notes"), 5000),
        "finished_at": now_iso(),
        "verified_net_profit_eur": "0.00",
    }
    (RUNS / f"{ref}.json").write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"{ref}: materialized · {len(product_files)} product files · {len(prospects)} prospects")


if __name__ == "__main__":
    main()
