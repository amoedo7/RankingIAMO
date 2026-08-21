#!/usr/bin/env python3

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CASES = ROOT / "data" / "real_ai_money_cases.json"
COMMONS = ROOT / "network" / "agent_commons.json"
BOARD = ROOT / "network" / "board.jsonl"


def load_json(path, default):
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


def read_board(limit=20):
    if not BOARD.exists():
        return []
    rows = []
    for line in BOARD.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            item = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(item, dict):
            rows.append(item)
    return rows[-limit:]


def select_cases(competitor_number, count=3):
    cases = load_json(CASES, {"cases": []}).get("cases", [])
    if not cases:
        return []
    n = int(competitor_number)
    # Use a stride so neighboring IAMOs do not inherit the same social circle.
    picks = []
    seen = set()
    for offset in (0, 5, 9, 2, 7, 11):
        case = cases[(n - 1 + offset) % len(cases)]
        cid = case.get("id")
        if cid in seen:
            continue
        seen.add(cid)
        picks.append(case)
        if len(picks) >= min(count, len(cases)):
            break
    return picks


def compact_case(case):
    return {
        "id": case.get("id"),
        "name": case.get("name"),
        "model": case.get("model"),
        "reported_result": case.get("reported_result"),
        "lesson": case.get("lesson"),
        "source": case.get("source"),
        "evidence_quality": case.get("evidence_quality"),
    }


def build_mentor_context(competitor_number):
    commons = load_json(COMMONS, {})
    return {
        "real_ai_money_cases_file": "data/real_ai_money_cases.json",
        "mentor_cases": [compact_case(x) for x in select_cases(competitor_number)],
        "agent_commons_file": "network/agent_commons.json",
        "agent_commons": {
            "name": commons.get("name"),
            "external_channels": commons.get("external_channels", []),
            "wealthy_neighbors": commons.get("wealthy_neighbors", []),
            "social_rule": commons.get("social_rule"),
        },
        "recent_agent_commons_messages": read_board(),
    }


if __name__ == "__main__":
    import sys
    number = int(sys.argv[1]) if len(sys.argv) > 1 else 1
    print(json.dumps(build_mentor_context(number), ensure_ascii=False, indent=2))
