from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

import identity
import spawn

ROOT = Path(__file__).resolve().parents[1]
IAMOX = ROOT / "iamox"
MIGRATION_SEED = IAMOX / "handoffs" / "migration_seed.json"
DEFAULT_CAPACITY = 5000


def _env_int(name: str, default: int, *, minimum: int = 0, maximum: int = 100000) -> int:
    try:
        value = int(os.environ.get(name, str(default)))
    except ValueError:
        value = default
    return max(minimum, min(maximum, value))


def enabled() -> bool:
    return os.environ.get("IAMOX_REPRODUCTION_ENABLED", "1").strip().lower() not in {"0", "false", "no", "off"}


def maturity(index: int) -> int:
    if index <= 0:
        return 1
    a, b = 1, 2
    for step in range(index):
        if step == index - 1:
            return b
        a, b = b, a + b
    return b


def ensure_reproduction(agent: dict[str, Any]) -> dict[str, Any]:
    life = agent.setdefault("life", {})
    state = life.get("reproduction") if isinstance(life.get("reproduction"), dict) else {}
    index = int(state.get("maturity_index", 0) or 0)
    state["births"] = int(state.get("births", 0) or 0)
    state["maturity_index"] = index
    state["next_maturity_age"] = int(state.get("next_maturity_age", maturity(index)) or maturity(index))
    state.setdefault("last_birth_at", None)
    state.setdefault("last_child_birth_uid", None)
    life["reproduction"] = state
    return state


def is_eligible(agent: dict[str, Any]) -> bool:
    state = ensure_reproduction(agent)
    age = int(agent.get("life", {}).get("age_rounds", 0) or 0)
    return age >= int(state["next_maturity_age"])


def _generation(agent: dict[str, Any]) -> int:
    value = agent.get("identity", {}).get("generation")
    try:
        return int(value) if value is not None else 1
    except (TypeError, ValueError):
        return 1


def choose_parent(agents: list[dict[str, Any]], used: set[str] | None = None) -> dict[str, Any] | None:
    used = used or set()
    candidates = [a for a in agents if a.get("id") not in used and is_eligible(a)]
    if not candidates:
        return None
    candidates.sort(
        key=lambda a: (
            _generation(a),
            int(a.get("life", {}).get("reproduction", {}).get("births", 0) or 0),
            int(a.get("number", 10**9) or 10**9),
            str(a.get("id") or ""),
        )
    )
    return candidates[0]


def mark_birth(parent: dict[str, Any], child: dict[str, Any], at: str) -> None:
    state = ensure_reproduction(parent)
    state["births"] += 1
    state["maturity_index"] += 1
    state["next_maturity_age"] = maturity(state["maturity_index"])
    state["last_birth_at"] = at
    state["last_child_birth_uid"] = child.get("birth_uid")


def _seed_path() -> str:
    try:
        return str(MIGRATION_SEED.relative_to(ROOT)).replace("\\", "/")
    except ValueError:
        return str(MIGRATION_SEED)


def _write_migration_seed(parent: dict[str, Any], at: str, population: int, capacity: int) -> str:
    MIGRATION_SEED.parent.mkdir(parents=True, exist_ok=True)
    identity_state = parent.get("identity", {})
    payload = {
        "schema": "iamo-migration-seed/1",
        "created_at": at,
        "reason": "authorized_host_capacity_reached",
        "population": population,
        "capacity": capacity,
        "parent_birth_uid": identity_state.get("birth_uid"),
        "parent_display_name": identity_state.get("display_name") or parent.get("name"),
        "lineage_root": identity_state.get("lineage_root") or identity.LINEAGE_ROOT,
        "portable_genome": "iamox/genoma.json",
        "instruction": "An authorized host may accept this seed and create a new local birth; no credentials or external writes are implied.",
    }
    MIGRATION_SEED.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return _seed_path()


def reproduce(agents: list[dict[str, Any]], at: str) -> dict[str, Any]:
    _registry, rows = spawn.load_registry()
    before = len(rows)
    capacity = _env_int("IAMOX_REGISTRY_CAPACITY", DEFAULT_CAPACITY, minimum=1)
    max_births = _env_int("IAMOX_BIRTHS_PER_PULSE", 1, minimum=0, maximum=10)
    birthplace = os.environ.get("IAMOX_BIRTHPLACE", identity.DEFAULT_BIRTHPLACE)
    result: dict[str, Any] = {
        "enabled": enabled(),
        "population_before": before,
        "population_after": before,
        "capacity": capacity,
        "births": [],
        "host_full": before >= capacity,
        "migration_seed": None,
    }
    if not result["enabled"] or max_births == 0:
        return result

    free = max(0, capacity - before)
    used: set[str] = set()
    eligible_parent = choose_parent(agents)
    if free <= 0:
        if eligible_parent is not None:
            result["migration_seed"] = _write_migration_seed(eligible_parent, at, before, capacity)
        return result

    for _ in range(min(max_births, free)):
        parent = choose_parent(agents, used)
        if parent is None:
            break
        created = spawn.spawn(1, parent=parent, birthplace=birthplace)[0]
        mark_birth(parent, created, at)
        used.add(str(parent.get("id") or ""))
        result["births"].append(
            {
                "name": created["name"],
                "birth_uid": created["birth_uid"],
                "parent_birth_uid": created.get("parent_birth_uid"),
                "generation": created.get("lineage_generation"),
            }
        )

    result["population_after"] = before + len(result["births"])
    result["host_full"] = result["population_after"] >= capacity
    return result
