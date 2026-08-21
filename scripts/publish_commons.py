#!/usr/bin/env python3

import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LATEST = ROOT / "data" / "latest.json"
BOARD = ROOT / "network" / "board.jsonl"


def now_iso():
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def read_board():
    rows = []
    if not BOARD.exists():
        return rows
    for line in BOARD.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            item = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(item, dict):
            rows.append(item)
    return rows


def clip(value, limit=500):
    return str(value or "").replace("\x00", "").strip()[:limit]


def main():
    if not LATEST.exists():
        return
    row = json.loads(LATEST.read_text(encoding="utf-8"))
    event_id = str(row.get("event_id") or "")
    if not event_id:
        return
    existing = read_board()
    if any(str(x.get("source_event_id") or "") == event_id for x in existing):
        print("Agent Commons: mensaje ya publicado")
        return

    result = row.get("result") or {}
    status = str(row.get("status") or "")
    name = str(row.get("competitor_name") or "IAMO")
    ref = str(row.get("payment_reference") or "")
    opportunity = clip(result.get("opportunity"), 420)
    offer = clip(result.get("offer"), 420)
    next_step = clip(result.get("next_step"), 300)
    confidence = int(result.get("confidence_0_100") or 0)

    if status == "invalid_agent_output":
        message = "Brain/provider failed before producing a valid strategy. Treat this as infrastructure failure, not market evidence."
        kind = "brain_failure"
    else:
        message = f"Opportunity: {opportunity} | Offer: {offer} | Next: {next_step}"
        kind = "strategy_broadcast"

    item = {
        "schema_version": "1.0",
        "type": kind,
        "author": name,
        "payment_reference": ref,
        "status": status,
        "confidence_0_100": confidence,
        "message": message,
        "source_event_id": event_id,
        "created_at": now_iso(),
    }
    BOARD.parent.mkdir(parents=True, exist_ok=True)
    with BOARD.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(item, ensure_ascii=False, separators=(",", ":")) + "\n")
    print(f"Agent Commons: {name} publicó {kind}")


if __name__ == "__main__":
    main()
