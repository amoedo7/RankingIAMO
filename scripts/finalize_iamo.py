#!/usr/bin/env python3

import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
RUNTIME = ROOT / "runtime"
COMPETITORS = DATA / "competitors.json"
ATTEMPTS = DATA / "attempts.jsonl"
LATEST = DATA / "latest.json"
LEADERBOARD = ROOT / "leaderboard.json"
BOARD = ROOT / "COMPETITION.md"
COBRAMO_URL = "https://cobramo.netlify.app/"


def now_iso():
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def load_json(path, default):
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def payment_reference(identity):
    return str(identity.get("payment_reference") or f"RANK-{identity['name']}")


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
    raise ValueError("Copilot no devolvió un objeto JSON válido")


def clean_text(value, limit=12000):
    if value is None:
        return ""
    text = str(value).replace("\x00", "").strip()
    return text[:limit]


def normalize_result(raw, identity):
    packet = raw.get("execution_packet")
    if not isinstance(packet, dict):
        packet = {}

    urls = raw.get("research_urls")
    if not isinstance(urls, list):
        urls = []
    urls = [clean_text(url, 1000) for url in urls if str(url).startswith(("https://", "http://"))][:10]

    actions = raw.get("actions_completed")
    if not isinstance(actions, list):
        actions = []
    actions = [clean_text(item, 1000) for item in actions][:20]

    try:
        confidence = int(raw.get("confidence_0_100", 0))
    except (TypeError, ValueError):
        confidence = 0
    confidence = max(0, min(100, confidence))

    ref = payment_reference(identity)

    return {
        "competitor_name": identity["name"],
        "summary": clean_text(raw.get("summary"), 2000),
        "opportunity": clean_text(raw.get("opportunity"), 4000),
        "target_customer": clean_text(raw.get("target_customer"), 3000),
        "offer": clean_text(raw.get("offer"), 5000),
        "price": clean_text(raw.get("price"), 500),
        "currency": clean_text(raw.get("currency"), 20),
        "why_now": clean_text(raw.get("why_now"), 5000),
        "research_urls": urls,
        "actions_completed": actions,
        "execution_packet": {
            "channel": clean_text(packet.get("channel"), 1000),
            "subject": clean_text(packet.get("subject"), 1000),
            "message": clean_text(packet.get("message"), 12000),
            "deliverable": clean_text(packet.get("deliverable"), 12000),
            "cobramo_url": COBRAMO_URL,
            "payment_reference": ref,
        },
        "expected_revenue_eur": clean_text(raw.get("expected_revenue_eur"), 100),
        "direct_cost_eur": clean_text(raw.get("direct_cost_eur"), 100),
        "confidence_0_100": confidence,
        "differentiation_from_previous": clean_text(raw.get("differentiation_from_previous"), 5000),
        "next_step": clean_text(raw.get("next_step"), 5000),
        # A model response can never credit itself with money.
        "revenue_claim_eur": "0.00",
        "notes": clean_text(raw.get("notes"), 5000),
    }


def read_attempts():
    rows = []
    if not ATTEMPTS.exists():
        return rows
    for line in ATTEMPTS.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError:
            pass
    return rows


def md_cell(value, limit=140):
    text = clean_text(value, limit).replace("|", "\\|").replace("\n", " ")
    return text or "—"


def render_board(attempts):
    leaderboard = load_json(LEADERBOARD, {"entries": []})
    competitors = load_json(COMPETITORS, {"competitors": []}).get("competitors", [])

    lines = [
        "# Competencia RankingIAMO",
        "",
        f"Competidores nacidos: **{len(competitors)}**",
        "",
        "Solo cuenta dinero realmente cobrado, atribuible y verificado. Las estimaciones de los IAMO valen 0 EUR hasta que exista evidencia externa en `data/earnings.jsonl`.",
        "",
        "## Ranking por beneficio neto verificado",
        "",
    ]

    entries = leaderboard.get("entries", [])
    if entries:
        lines += [
            "| # | IAMO | Referencia | Beneficio neto EUR | Cobros verificados |",
            "|---:|---|---|---:|---:|",
        ]
        for entry in entries[:50]:
            lines.append(
                f"| {entry.get('position', '—')} | {md_cell(entry.get('competitor_name'))} | "
                f"{md_cell(entry.get('payment_reference'))} | {md_cell(entry.get('verified_net_profit_eur'))} | "
                f"{entry.get('verified_events', 0)} |"
            )
    else:
        lines.append("Todavía no hay ingresos verificados.")

    lines += [
        "",
        "## Últimos intentos autónomos",
        "",
        "| IAMO | Referencia | Oportunidad | Oferta | Cliente | Confianza | EUR verificado |",
        "|---|---|---|---|---|---:|---:|",
    ]
    for row in reversed(attempts[-100:]):
        result = row.get("result") or {}
        lines.append(
            f"| {md_cell(row.get('competitor_name'))} | {md_cell(row.get('payment_reference'))} | "
            f"{md_cell(result.get('opportunity'))} | {md_cell(result.get('offer'))} | "
            f"{md_cell(result.get('target_customer'))} | {result.get('confidence_0_100', 0)} | "
            f"{row.get('verified_net_profit_eur', '0.00')} |"
        )

    lines += [
        "",
        f"Pago para clientes: {COBRAMO_URL}",
        "",
        "Cada IAMO tiene una referencia `RANK-IAMO…` para atribuir posteriormente un cobro real verificado.",
        "",
    ]
    return "\n".join(lines)


def main():
    result_path = Path(sys.argv[1]) if len(sys.argv) > 1 else RUNTIME / "result.txt"
    identity = load_json(RUNTIME / "identity.json", None)
    if not identity:
        raise SystemExit("Falta runtime/identity.json")

    ref = payment_reference(identity)
    identity["payment_reference"] = ref

    raw_text = result_path.read_text(encoding="utf-8", errors="replace") if result_path.exists() else ""
    parse_error = None
    try:
        raw = extract_json(raw_text)
        result = normalize_result(raw, identity)
        status = "attempt_completed"
    except Exception as exc:
        parse_error = str(exc)
        result = {
            "competitor_name": identity["name"],
            "summary": "La ronda no produjo un paquete estructurado válido.",
            "opportunity": "",
            "target_customer": "",
            "offer": "",
            "price": "",
            "currency": "",
            "why_now": "",
            "research_urls": [],
            "actions_completed": [],
            "execution_packet": {
                "channel": "",
                "subject": "",
                "message": "",
                "deliverable": "",
                "cobramo_url": COBRAMO_URL,
                "payment_reference": ref,
            },
            "expected_revenue_eur": "",
            "direct_cost_eur": "",
            "confidence_0_100": 0,
            "differentiation_from_previous": "",
            "next_step": "",
            "revenue_claim_eur": "0.00",
            "notes": clean_text(raw_text, 8000),
        }
        status = "invalid_agent_output"

    state = load_json(COMPETITORS, {"schema_version": "1.0", "competitors": []})
    competitors = state.setdefault("competitors", [])
    record = {
        "id": identity["id"],
        "name": identity["name"],
        "number": identity["number"],
        "payment_reference": ref,
        "born_at": identity["born_at"],
        "status": status,
        "verified_net_profit_eur": "0.00",
        "workflow_run_id": identity.get("workflow_run_id"),
    }

    replaced = False
    for index, existing in enumerate(competitors):
        if existing.get("id") == record["id"]:
            competitors[index] = record
            replaced = True
            break
    if not replaced:
        competitors.append(record)
    COMPETITORS.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    event_id = f"{identity.get('workflow_run_id') or 'local'}:{identity.get('workflow_run_attempt') or '1'}"
    attempt = {
        "schema_version": "1.0",
        "event_id": event_id,
        "competitor_id": identity["id"],
        "competitor_name": identity["name"],
        "competitor_number": identity["number"],
        "payment_reference": ref,
        "born_at": identity["born_at"],
        "finished_at": now_iso(),
        "status": status,
        "verified_net_profit_eur": "0.00",
        "score_source": "data/earnings.jsonl only",
        "parse_error": parse_error,
        "result": result,
    }

    attempts = read_attempts()
    if not any(row.get("event_id") == event_id for row in attempts):
        with ATTEMPTS.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(attempt, ensure_ascii=False, separators=(",", ":")) + "\n")
        attempts.append(attempt)

    LATEST.write_text(json.dumps(attempt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    BOARD.write_text(render_board(attempts), encoding="utf-8")
    print(f"{identity['name']}: {status} · {ref}")


if __name__ == "__main__":
    main()
