from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import identity

ROOT = Path(__file__).resolve().parents[1]
COMPETITORS = ROOT / "data" / "competitors.json"


def now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def load_registry() -> tuple[dict[str, Any], list[dict[str, Any]]]:
    raw = json.loads(COMPETITORS.read_text(encoding="utf-8"))
    if isinstance(raw, dict):
        rows = raw.get("competitors")
        if not isinstance(rows, list):
            raise SystemExit("data/competitors.json has no competitors list")
        return raw, rows
    if isinstance(raw, list):
        return {"schema_version": "1.0", "competitors": raw}, raw
    raise SystemExit("Unsupported competitors registry format")


def next_number(rows: list[dict[str, Any]]) -> int:
    numbers = []
    for row in rows:
        try:
            numbers.append(int(row.get("number") or row.get("competitor_number") or 0))
        except (TypeError, ValueError):
            pass
    return max(numbers or [0]) + 1


def birth(
    number: int,
    born_at: str,
    *,
    parent: dict[str, Any] | None = None,
    birthplace: str = identity.DEFAULT_BIRTHPLACE,
) -> dict[str, Any]:
    name = f"IAMO{number}"
    parent_identity = parent.get("identity", {}) if isinstance(parent, dict) else {}
    parent_uid = parent_identity.get("birth_uid") or None
    parent_generation = int(parent_identity.get("generation", 0) or 0)
    generation = parent_generation + 1 if parent_uid else (0 if number == 1 else 1)
    uid = identity.birth_uid(name, born_at, birthplace, parent_uid)
    return {
        "id": f"iamo{number}",
        "name": name,
        "number": number,
        "payment_reference": f"RANK-IAMO{number}",
        "born_at": born_at,
        "birth_uid": uid,
        "birthplace": birthplace,
        "parent_birth_uid": parent_uid,
        "lineage_generation": generation,
        "status": "born",
        "verified_net_profit_eur": "0.00",
        "runtime_generation": "0.5.0-stem",
        "origin": "DesarrollAMO",
        "creator": "AMO",
    }


def spawn(
    count: int = 1,
    *,
    parent: dict[str, Any] | None = None,
    birthplace: str = identity.DEFAULT_BIRTHPLACE,
) -> list[dict[str, Any]]:
    if count < 1 or count > 10:
        raise SystemExit("count must be between 1 and 10")
    registry, rows = load_registry()
    created: list[dict[str, Any]] = []
    number = next_number(rows)
    for offset in range(count):
        item = birth(number + offset, now(), parent=parent, birthplace=birthplace)
        rows.append(item)
        created.append(item)
    registry["competitors"] = rows
    registry["updated_at"] = now()
    COMPETITORS.write_text(json.dumps(registry, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return created


def main() -> None:
    parser = argparse.ArgumentParser(description="Create IAMOX identities with immutable birth lineage.")
    parser.add_argument("--count", type=int, default=1)
    parser.add_argument("--birthplace", default=identity.DEFAULT_BIRTHPLACE)
    args = parser.parse_args()
    created = spawn(args.count, birthplace=args.birthplace)
    print(json.dumps({"created": created}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
