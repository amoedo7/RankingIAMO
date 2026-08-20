#!/usr/bin/env python3

import argparse
import json
import sys
from collections import defaultdict
from decimal import Decimal, InvalidOperation
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LEDGER = ROOT / "data" / "earnings.jsonl"
OUTPUT = ROOT / "leaderboard.json"

REQUIRED = {
    "event_id",
    "competitor_id",
    "competitor_name",
    "competitor_type",
    "status",
    "currency",
    "amount_original",
    "gross_revenue_eur",
    "direct_cost_eur",
    "net_profit_eur",
    "verified_at",
    "evidence_ref",
}


def money(value, field, line_number):
    try:
        return Decimal(str(value))
    except InvalidOperation:
        raise ValueError(
            f"Linea {line_number}: {field} no contiene una cantidad valida"
        )


def canonical_decimal(value):
    value = value.quantize(Decimal("0.01"))
    return format(value, "f")


def build():
    stats = defaultdict(
        lambda: {
            "name": "",
            "type": "",
            "profit": Decimal("0"),
            "gross": Decimal("0"),
            "cost": Decimal("0"),
            "events": 0,
            "last_verified_at": None,
        }
    )

    seen = set()

    if not LEDGER.exists():
        raise ValueError(f"No existe {LEDGER}")

    for line_number, raw in enumerate(
        LEDGER.read_text(encoding="utf-8").splitlines(), start=1
    ):
        if not raw.strip():
            continue

        try:
            event = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise ValueError(
                f"Linea {line_number}: JSON invalido: {exc}"
            )

        missing = REQUIRED - set(event)
        if missing:
            raise ValueError(
                f"Linea {line_number}: faltan campos: {sorted(missing)}"
            )

        event_id = str(event["event_id"])

        if event_id in seen:
            raise ValueError(
                f"Linea {line_number}: event_id duplicado: {event_id}"
            )

        seen.add(event_id)

        if event["status"] != "verified":
            continue

        gross = money(event["gross_revenue_eur"], "gross_revenue_eur", line_number)
        cost = money(event["direct_cost_eur"], "direct_cost_eur", line_number)
        profit = money(event["net_profit_eur"], "net_profit_eur", line_number)

        if gross < 0 or cost < 0:
            raise ValueError(
                f"Linea {line_number}: ingresos y costes deben ser positivos"
            )

        if profit != gross - cost:
            raise ValueError(
                f"Linea {line_number}: net_profit_eur debe ser gross_revenue_eur - direct_cost_eur"
            )

        competitor_id = str(event["competitor_id"])
        row = stats[competitor_id]

        row["name"] = str(event["competitor_name"])
        row["type"] = str(event["competitor_type"])
        row["profit"] += profit
        row["gross"] += gross
        row["cost"] += cost
        row["events"] += 1

        verified_at = str(event["verified_at"])

        if row["last_verified_at"] is None or verified_at > row["last_verified_at"]:
            row["last_verified_at"] = verified_at

    ordered = sorted(
        stats.items(),
        key=lambda item: (
            -item[1]["profit"],
            -item[1]["events"],
            item[0],
        ),
    )

    entries = []

    for position, (competitor_id, row) in enumerate(ordered, start=1):
        entries.append(
            {
                "position": position,
                "competitor_id": competitor_id,
                "competitor_name": row["name"],
                "competitor_type": row["type"],
                "verified_net_profit_eur": canonical_decimal(row["profit"]),
                "verified_gross_revenue_eur": canonical_decimal(row["gross"]),
                "direct_cost_eur": canonical_decimal(row["cost"]),
                "verified_events": row["events"],
                "last_verified_at": row["last_verified_at"],
            }
        )

    return {
        "schema_version": "1.0",
        "ranking_metric": "verified_net_profit_eur",
        "rules": {
            "verified_payments_only": True,
            "pending_payments_score": "0.00",
            "leads_score": "0.00",
            "default_autonomous_budget_eur": "0.00",
        },
        "entries": entries,
    }


def render(data):
    return json.dumps(
        data,
        ensure_ascii=False,
        indent=2,
        sort_keys=False,
    ) + "\n"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    try:
        expected = render(build())
    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    if args.check:
        if not OUTPUT.exists():
            print("ERROR: leaderboard.json no existe", file=sys.stderr)
            return 1

        current = OUTPUT.read_text(encoding="utf-8")

        if current != expected:
            print(
                "ERROR: leaderboard.json no coincide con data/earnings.jsonl",
                file=sys.stderr,
            )
            print(
                "Ejecutar: python scripts/rebuild_ranking.py",
                file=sys.stderr,
            )
            return 1

        print("Ranking valido")
        return 0

    OUTPUT.write_text(expected, encoding="utf-8")
    print(f"Ranking reconstruido: {OUTPUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
