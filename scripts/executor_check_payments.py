#!/usr/bin/env python3

import json
from collections import defaultdict
from decimal import Decimal, InvalidOperation
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LEDGER = ROOT / "data" / "earnings.jsonl"
RUNS = ROOT / "executor" / "runs"
OUTPUT = ROOT / "executor" / "payment_status.json"


def money(value):
    try:
        return Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        return Decimal("0")


def fmt(value):
    return format(value.quantize(Decimal("0.01")), "f")


def read_earnings():
    result = defaultdict(lambda: {
        "verified_events": 0,
        "gross_revenue_eur": Decimal("0"),
        "direct_cost_eur": Decimal("0"),
        "net_profit_eur": Decimal("0"),
        "event_ids": [],
        "last_verified_at": None,
    })
    if not LEDGER.exists():
        return result

    for raw in LEDGER.read_text(encoding="utf-8").splitlines():
        if not raw.strip():
            continue
        try:
            event = json.loads(raw)
        except json.JSONDecodeError:
            continue
        if event.get("status") != "verified":
            continue
        ref = str(event.get("payment_reference") or "").strip()
        if not ref.startswith("RANK-IAMO"):
            continue
        row = result[ref]
        row["verified_events"] += 1
        row["gross_revenue_eur"] += money(event.get("gross_revenue_eur"))
        row["direct_cost_eur"] += money(event.get("direct_cost_eur"))
        row["net_profit_eur"] += money(event.get("net_profit_eur"))
        row["event_ids"].append(str(event.get("event_id") or ""))
        verified_at = str(event.get("verified_at") or "")
        if verified_at and (row["last_verified_at"] is None or verified_at > row["last_verified_at"]):
            row["last_verified_at"] = verified_at
    return result


def main():
    payments = read_earnings()
    statuses = []

    if RUNS.exists():
        for path in sorted(RUNS.glob("RANK-IAMO*.json")):
            try:
                run = json.loads(path.read_text(encoding="utf-8"))
            except Exception:
                continue
            ref = str(run.get("payment_reference") or path.stem)
            payment = payments.get(ref)
            if payment:
                statuses.append({
                    "payment_reference": ref,
                    "competitor_name": run.get("competitor_name"),
                    "status": "paid_verified",
                    "verified_events": payment["verified_events"],
                    "gross_revenue_eur": fmt(payment["gross_revenue_eur"]),
                    "direct_cost_eur": fmt(payment["direct_cost_eur"]),
                    "net_profit_eur": fmt(payment["net_profit_eur"]),
                    "event_ids": payment["event_ids"],
                    "last_verified_at": payment["last_verified_at"],
                })
            else:
                statuses.append({
                    "payment_reference": ref,
                    "competitor_name": run.get("competitor_name"),
                    "status": "waiting_verified_payment",
                    "verified_events": 0,
                    "gross_revenue_eur": "0.00",
                    "direct_cost_eur": "0.00",
                    "net_profit_eur": "0.00",
                    "event_ids": [],
                    "last_verified_at": None,
                })

    payload = {
        "schema_version": "1.0",
        "source_of_truth": "data/earnings.jsonl",
        "statuses": statuses,
    }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    paid = sum(1 for row in statuses if row["status"] == "paid_verified")
    print(f"Payment status actualizado: {len(statuses)} ofertas · {paid} con pago verificado")


if __name__ == "__main__":
    main()
