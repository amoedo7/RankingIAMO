#!/usr/bin/env python3

import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
EXECUTOR = ROOT / "executor"
ATTEMPTS = DATA / "attempts.jsonl"
COMPETITORS = DATA / "competitors.json"
LEADERBOARD = ROOT / "leaderboard.json"
OUTPUT = ROOT / "proximity.json"


def now_iso():
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def load_json(path, default):
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


def load_jsonl(path):
    if not path.exists():
        return []
    rows = []
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if not line.strip():
            continue
        try:
            item = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(item, dict):
            rows.append(item)
    return rows


def load_json_dir(path):
    rows = []
    if not path.exists():
        return rows
    for file in sorted(path.glob("*.json")):
        item = load_json(file, None)
        if isinstance(item, dict):
            item = dict(item)
            item["_file"] = str(file.relative_to(ROOT))
            rows.append(item)
    return rows


def ref_of(item):
    return str(
        item.get("payment_reference")
        or item.get("reference")
        or item.get("rank_reference")
        or ""
    )


def latest_attempts():
    latest = {}
    for row in load_jsonl(ATTEMPTS):
        ref = ref_of(row)
        if ref:
            latest[ref] = row
    return latest


def sent_rows():
    data = load_json(EXECUTOR / "sent.json", {"records": []})
    rows = data.get("records", []) if isinstance(data, dict) else []
    return [x for x in rows if isinstance(x, dict)]


def response_rows():
    # Optional future-compatible ledger. The score automatically starts using it
    # when outreach automation persists replies/interested/negotiation events.
    data = load_json(EXECUTOR / "responses.json", {"records": []})
    rows = data.get("records", []) if isinstance(data, dict) else []
    return [x for x in rows if isinstance(x, dict)]


def verified_map():
    board = load_json(LEADERBOARD, {"entries": []})
    result = {}
    for entry in board.get("entries", []):
        ref = ref_of(entry)
        name = str(entry.get("competitor_name") or "")
        if ref:
            result[ref] = entry
        elif name:
            result[f"RANK-{name}"] = entry
    return result


def stage(score, flags):
    if flags.get("verified"):
        return "VERIFICADO"
    if flags.get("provider_payment_candidate"):
        return "CONFIRMACION DE PROVEEDOR — REVISAR CUENTA"
    if flags.get("payment_candidate"):
        return "EVIDENCIA DE PAGO — REVISAR CUENTA"
    if flags.get("buyer_signal"):
        return "RESPUESTA / INTERES"
    if flags.get("sent"):
        return "OUTREACH ENVIADO"
    if flags.get("ready"):
        return "LISTO PARA VENDER"
    if flags.get("materialized"):
        return "PRODUCTO / OFERTA MATERIALIZADA"
    if flags.get("valid_strategy"):
        return "ESTRATEGIA UTIL"
    if score > 0:
        return "SEÑALES INICIALES"
    return "SIN AVANCE COMERCIAL"


def score_one(competitor, attempt, run, sent, responses, candidates, verified):
    ref = str(competitor.get("payment_reference") or f"RANK-{competitor.get('name')}")
    score = 0
    signals = []
    flags = {
        "valid_strategy": False,
        "materialized": False,
        "ready": False,
        "sent": False,
        "buyer_signal": False,
        "payment_candidate": False,
        "provider_payment_candidate": False,
        "verified": False,
    }

    status = str((attempt or {}).get("status") or competitor.get("status") or "")
    result = (attempt or {}).get("result") or {}
    if status in {"attempt_completed", "research_incomplete", "fallback_strategy"} and (
        result.get("offer") or result.get("opportunity")
    ):
        score += 12
        flags["valid_strategy"] = True
        signals.append({"points": 12, "signal": "estrategia concreta registrada"})

    ext = result.get("external_evidence_urls") or []
    if isinstance(ext, list) and ext:
        score += 8
        signals.append({"points": 8, "signal": "evidencia externa de mercado/demanda"})

    packet = result.get("execution_packet") or {}
    packet_fields = sum(bool(packet.get(k)) for k in ("channel", "message", "deliverable"))
    if packet_fields >= 2:
        score += 5
        signals.append({"points": 5, "signal": "paquete de ejecución utilizable"})

    run_status = str((run or {}).get("status") or "")
    executor_valid = bool(run) and not run_status.startswith("invalid_")
    if executor_valid and ((run or {}).get("offer_url") or (run or {}).get("product_url")):
        score += 15
        flags["materialized"] = True
        signals.append({"points": 15, "signal": "oferta/producto materializado"})

    if executor_valid and (run or {}).get("offer_url"):
        score += 5
        signals.append({"points": 5, "signal": "landing/oferta pública"})

    quality = str((run or {}).get("quality_status") or "")
    if executor_valid and quality == "ready_to_sell":
        score += 15
        flags["ready"] = True
        signals.append({"points": 15, "signal": "quality gate listo para vender"})

    sendable = int((run or {}).get("outreach_sendable") or 0)
    if executor_valid and sendable > 0:
        score += 5
        signals.append({"points": 5, "signal": f"{sendable} prospectos enviables preparados"})

    own_sent = [x for x in sent if ref_of(x) == ref]
    if own_sent:
        pts = min(10, len(own_sent) * 2)
        score += pts
        flags["sent"] = True
        signals.append({"points": pts, "signal": f"{len(own_sent)} outreach realmente enviados"})

    own_responses = [x for x in responses if ref_of(x) == ref]
    positive = [
        x for x in own_responses
        if str(x.get("status") or x.get("type") or "").lower()
        in {"replied", "interested", "qualified", "negotiation", "payment_intent", "buyer_signal"}
    ]
    if positive:
        pts = 15 if any(str(x.get("status") or "").lower() in {"negotiation", "payment_intent"} for x in positive) else 10
        score += pts
        flags["buyer_signal"] = True
        signals.append({"points": pts, "signal": "respuesta/interés comercial real"})

    own_candidates = [x for x in candidates if ref_of(x) == ref]
    if own_candidates:
        flags["payment_candidate"] = True
        strongest = max(
            own_candidates,
            key=lambda x: 1 if str(x.get("status")) == "provider_confirmation_candidate" else 0,
        )
        if str(strongest.get("status")) == "provider_confirmation_candidate":
            score = max(score, 96)
            flags["provider_payment_candidate"] = True
            signals.append({"points": "floor=96", "signal": "confirmación candidata de proveedor de pago"})
        else:
            score = max(score, 92)
            signals.append({"points": "floor=92", "signal": "evidencia candidata de pago"})

    verified_entry = verified.get(ref)
    verified_events = int((verified_entry or {}).get("verified_events") or 0)
    verified_profit = float((verified_entry or {}).get("verified_net_profit_eur") or 0)
    if verified_events > 0:
        score = 100
        flags["verified"] = True
        signals.append({"points": "100", "signal": "cobro verificado: ranking oficial"})

    score = max(0, min(100, int(score)))
    return {
        "competitor_id": competitor.get("id"),
        "competitor_name": competitor.get("name"),
        "competitor_number": competitor.get("number"),
        "payment_reference": ref,
        "proximity_score": score,
        "stage": stage(score, flags),
        "verified_net_profit_eur": f"{verified_profit:.2f}",
        "verified_events": verified_events,
        "attempt_status": status,
        "executor_status": run_status or None,
        "offer_url": (run or {}).get("offer_url"),
        "outreach_sent": len(own_sent),
        "payment_candidates": len(own_candidates),
        "needs_account_review": flags["payment_candidate"] and not flags["verified"],
        "signals": signals,
    }


def build():
    state = load_json(COMPETITORS, {"competitors": []})
    competitors = state.get("competitors", [])
    attempts = latest_attempts()
    runs = {ref_of(x): x for x in load_json_dir(EXECUTOR / "runs") if ref_of(x)}
    sent = sent_rows()
    responses = response_rows()
    candidates = load_json_dir(EXECUTOR / "payment_candidates")
    verified = verified_map()

    entries = []
    for competitor in competitors:
        ref = str(competitor.get("payment_reference") or f"RANK-{competitor.get('name')}")
        entries.append(
            score_one(
                competitor,
                attempts.get(ref),
                runs.get(ref),
                sent,
                responses,
                candidates,
                verified,
            )
        )

    entries.sort(
        key=lambda x: (
            -int(x.get("proximity_score") or 0),
            -int(x.get("outreach_sent") or 0),
            int(x.get("competitor_number") or 0),
        )
    )
    for index, entry in enumerate(entries, start=1):
        entry["proximity_position"] = index

    return {
        "schema_version": "1.0",
        "generated_at": now_iso(),
        "name": "Money Proximity Score",
        "warning": "No es dinero ni una probabilidad estadística. Es un indicador de avance comercial basado solo en señales observables. El ranking oficial sigue gobernado por cobros verificados.",
        "scale": {
            "0-24": "idea / estrategia",
            "25-49": "oferta en construcción",
            "50-69": "lista para vender",
            "70-84": "contacto real con mercado",
            "85-91": "señal fuerte de comprador",
            "92-99": "evidencia de pago pendiente de revisión",
            "100": "cobro verificado",
        },
        "entries": entries,
    }


def main():
    result = build()
    OUTPUT.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if result["entries"]:
        top = result["entries"][0]
        print(f"Leader proximity: {top['competitor_name']} {top['proximity_score']}/100 · {top['stage']}")
    else:
        print("No competitors for proximity ranking")


if __name__ == "__main__":
    main()
