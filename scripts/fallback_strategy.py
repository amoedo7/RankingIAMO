#!/usr/bin/env python3

import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

from mentor_context import build_mentor_context
from prepare_iamo import select_playbook_seeds

ROOT = Path(__file__).resolve().parents[1]
RUNTIME = ROOT / "runtime"
DATA = ROOT / "data"
PLAYBOOK = DATA / "monetization_playbook.json"
SYSTEM_STATUS = DATA / "system_status.json"
COBRAMO = "https://cobramo.netlify.app/"


def now_iso():
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def load_json(path, default):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except Exception:
        return default


def extract_object(text):
    text = (text or "").strip()
    if not text:
        return None
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text, count=1, flags=re.I)
        text = re.sub(r"\s*```$", "", text, count=1)
    decoder = json.JSONDecoder()
    for i, ch in enumerate(text):
        if ch != "{":
            continue
        try:
            value, _ = decoder.raw_decode(text[i:])
            if isinstance(value, dict):
                return value
        except json.JSONDecodeError:
            continue
    return None


def price_for(category, number):
    table = {
        "SaaS": (19, "EUR/month"),
        "Developer tools": (29, "EUR"),
        "Digital products": (19, "EUR"),
        "Productized services": (79, "EUR"),
        "Commerce": (17, "EUR"),
        "Mobile apps": (4, "EUR"),
        "Bots": (19, "EUR/month"),
        "Media": (15, "EUR"),
        "Newsletter": (7, "EUR/month"),
        "Memberships": (9, "EUR/month"),
        "Affiliate": (0, "commission"),
        "Freelance": (60, "EUR"),
        "B2B direct": (99, "EUR"),
        "Crypto/Web3": (39, "EUR or stablecoin equivalent"),
        "Licensing": (149, "EUR"),
    }
    base, unit = table.get(category, (39, "EUR"))
    # Small deterministic variance means fallback IAMOs do not all test the same price.
    value = base + ((int(number) % 3) * max(1, base // 5))
    return value, unit


def target_for(category, title):
    mapping = {
        "SaaS": "small businesses or independent professionals still doing this workflow manually",
        "Developer tools": "independent developers and small engineering teams with repeated setup or data-processing work",
        "Digital products": "freelancers and small-business operators who want an immediately usable asset instead of building it themselves",
        "Productized services": "small businesses with a visible public workflow or website problem that can be fixed in a bounded engagement",
        "Commerce": "buyers already searching for a narrow digital solution with instant delivery",
        "Mobile apps": "mobile users with a repeated utility problem that can be solved in seconds",
        "Bots": "online communities or small teams repeating a narrow messaging-platform workflow",
        "Media": "a high-intent niche audience repeatedly searching for how to solve or buy around one problem",
        "Newsletter": "professionals who benefit from recurring filtered information that saves time or helps a decision",
        "Memberships": "a niche audience that needs fresh reusable assets or intelligence every month",
        "Affiliate": "buyers with explicit purchase intent comparing products or services in one narrow category",
        "Freelance": "companies publicly asking for a bounded deliverable that DesarrollAMO can produce remotely",
        "B2B direct": "small businesses where a concrete revenue, operations or conversion problem is publicly observable",
        "Crypto/Web3": "Web3 teams buying legitimate software, data, automation or content services; no speculation or trading",
        "Licensing": "agencies or operators that can resell a working DesarrollAMO asset under license or white-label terms",
    }
    return mapping.get(category, f"external buyers with an existing need for {title.lower()}")


def channel_for(category, route):
    channels = route.get("channels") or []
    if category in {"Productized services", "Freelance", "B2B direct", "Licensing"}:
        return "personalized outreach to verified public business contacts, then CobrAMO for payment"
    if category in {"Digital products", "Developer tools", "Commerce"}:
        return "publish a working demo/product and use an authorized marketplace or CobrAMO payment path"
    if category in {"Mobile apps", "Bots"}:
        return "publish through an authorized app/bot channel and expose a paid upgrade or direct purchase"
    if category in {"Media", "Newsletter", "Memberships", "Affiliate"}:
        return "publish useful niche content and attach the relevant authorized monetization channel"
    return "authorized public distribution plus a direct payment path"


def main():
    result_path = Path(sys.argv[1]) if len(sys.argv) > 1 else RUNTIME / "result.txt"
    error_path = Path(sys.argv[2]) if len(sys.argv) > 2 else RUNTIME / "copilot_error.txt"

    current_text = result_path.read_text(encoding="utf-8", errors="replace") if result_path.exists() else ""
    if extract_object(current_text) is not None:
        SYSTEM_STATUS.write_text(json.dumps({
            "schema_version": "1.0",
            "brain": "copilot",
            "status": "ok",
            "fallback_active": False,
            "checked_at": now_iso()
        }, indent=2) + "\n", encoding="utf-8")
        print("Copilot devolvió JSON válido; fallback no necesario.")
        return

    error_text = error_path.read_text(encoding="utf-8", errors="replace") if error_path.exists() else ""
    quota = "exceeded your monthly quota" in error_text.lower()
    reason = "copilot_monthly_quota_exhausted" if quota else "model_unavailable_or_invalid_output"

    identity = load_json(RUNTIME / "identity.json", {})
    if not identity:
        raise SystemExit("Falta runtime/identity.json")
    number = int(identity["number"])
    name = str(identity["name"])
    ref = str(identity.get("payment_reference") or f"RANK-{name}")

    playbook = load_json(PLAYBOOK, {"routes": []})
    seeds = select_playbook_seeds(playbook.get("routes", []), number)
    route = seeds[(number - 1) % len(seeds)] if seeds else {
        "id": 0,
        "category": "Fallback",
        "title": "Productized digital service",
        "first_test": "Build one useful deliverable and validate a buyer before expanding.",
        "channels": ["CobrAMO"],
    }

    mentors = build_mentor_context(number)
    cases = mentors.get("mentor_cases", [])
    mentor = cases[0] if cases else {}
    category = str(route.get("category") or "Fallback")
    title = str(route.get("title") or "Useful digital offer")
    first_test = str(route.get("first_test") or "Validate one buyer and one useful deliverable.")
    price_value, price_unit = price_for(category, number)
    target = target_for(category, title)
    channel = channel_for(category, route)
    mentor_source = mentor.get("source") or ""
    mentor_name = mentor.get("name") or "the real-AI-money case library"
    mentor_lesson = mentor.get("lesson") or "validate demand before automating execution"

    packet = {
        "competitor_name": name,
        "summary": f"Fallback brain: test route #{route.get('id')} ({title}) while Copilot is unavailable.",
        "opportunity": f"Turn {title.lower()} into a small, concrete offer whose first sale can be validated before scaling.",
        "target_customer": target,
        "offer": f"A working MVP of '{title}' with a narrow promise, demo/deliverable and simple purchase path. First test: {first_test}",
        "price": str(price_value),
        "currency": price_unit,
        "why_now": f"The normal model provider is unavailable, so this competitor is using a deterministic monetization route plus the lesson from {mentor_name}: {mentor_lesson}. Fresh market evidence is still required before outreach.",
        "research_urls": [mentor_source] if mentor_source else [],
        "external_evidence_urls": [],
        "actions_completed": [
            f"Loaded monetization route #{route.get('id')}: {title}",
            f"Loaded money mentor: {mentor_name}",
            "Prepared a bounded execution packet with the local fallback engine instead of emitting an empty ERROR card"
        ],
        "execution_packet": {
            "channel": channel,
            "subject": f"{title}: propuesta concreta de DesarrollAMO",
            "message": f"Te escribo desde DesarrollAMO. Estamos validando una solución muy concreta: {title}. La propuesta se materializa solo después de comprobar que encaja con una necesidad real. Referencia: {ref}. Pago, si se acuerda una compra, mediante {COBRAMO}.",
            "deliverable": f"EjecutorIAMO debe construir un MVP funcional de {title}, comprobar calidad, encontrar demanda externa real y solo entonces publicar/contactar compradores permitidos.",
            "cobramo_url": COBRAMO,
            "payment_reference": ref,
        },
        "expected_revenue_eur": f"first-sale target around {price_value} {price_unit}; estimate only",
        "direct_cost_eur": "0.00",
        "confidence_0_100": 35 + (number % 4) * 5,
        "differentiation_from_previous": f"Uses rotating playbook route #{route.get('id')} and mentor {mentor_name}; does not repeat the empty Copilot-quota failure mode.",
        "next_step": "EjecutorIAMO must validate fresh external demand, materialize the smallest working offer and attempt a legitimate first sale.",
        "revenue_claim_eur": "0.00",
        "notes": f"BRAIN_MODE=quota_fallback; reason={reason}; no external demand evidence was fabricated. This strategy remains research-incomplete until real market evidence is found."
    }

    result_path.parent.mkdir(parents=True, exist_ok=True)
    result_path.write_text(json.dumps(packet, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    SYSTEM_STATUS.write_text(json.dumps({
        "schema_version": "1.0",
        "brain": "local_fallback",
        "status": reason,
        "fallback_active": True,
        "last_competitor": name,
        "checked_at": now_iso(),
        "copilot_error_excerpt": error_text.strip()[:500]
    }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"{name}: fallback activo · ruta #{route.get('id')} · {reason}")


if __name__ == "__main__":
    main()
