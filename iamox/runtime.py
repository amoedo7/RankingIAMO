from __future__ import annotations

import hashlib
import json
import math
import os
import random
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import life

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
IAMOX = ROOT / "iamox"
STATE = IAMOX / "state"
TASKS = IAMOX / "tasks"
CELLS = IAMOX / "cells"

COMPETITORS = DATA / "competitors.json"
LATEST = DATA / "latest.json"
EARNINGS = DATA / "earnings.jsonl"
PLAYBOOK = DATA / "monetization_playbook.json"
AGENTS = STATE / "agents.json"
QUEUE = TASKS / "queue.json"
CELLS_FILE = CELLS / "cells.json"
SUMMARY = STATE / "summary.json"

ROLES = ("scout", "builder", "seller", "critic", "accountant")
ACTIVE_STATES = {"idle", "observe", "propose", "peer_review", "cell", "execution_ready", "handoff", "measure", "learn", "blocked"}


def now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def read_json(path: Path, default: Any) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return default


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    os.replace(tmp, path)


def competitor_rows() -> list[dict[str, Any]]:
    raw = read_json(COMPETITORS, [])
    if isinstance(raw, dict):
        for key in ("competitors", "items", "entries"):
            if isinstance(raw.get(key), list):
                return raw[key]
        return []
    return raw if isinstance(raw, list) else []


def stable_role(agent_id: str) -> str:
    value = int(hashlib.sha256(agent_id.encode()).hexdigest()[:8], 16)
    return ROLES[value % len(ROLES)]


def stable_float(agent_id: str, salt: str) -> float:
    h = hashlib.sha256(f"{agent_id}:{salt}".encode()).hexdigest()
    return int(h[:8], 16) / 0xFFFFFFFF


def normalize_agent(row: dict[str, Any], old: dict[str, Any] | None = None) -> dict[str, Any]:
    old = old or {}
    number = row.get("competitor_number") or row.get("number")
    agent_id = str(row.get("competitor_id") or row.get("id") or (f"iamo{number}" if number else "")).lower()
    if not agent_id.startswith("iamo"):
        return {}
    role = old.get("role") or stable_role(agent_id)
    at = now()
    agent = {
        "id": agent_id,
        "name": row.get("competitor_name") or row.get("name") or agent_id.upper(),
        "number": number,
        "payment_reference": row.get("payment_reference") or (f"RANK-IAMO{number}" if number else ""),
        "role": role,
        "state": old.get("state", "idle") if old.get("state") in ACTIVE_STATES else "idle",
        "cell_id": old.get("cell_id"),
        "task_id": old.get("task_id"),
        "heartbeat_at": at,
        "reputation": old.get("reputation", {"evidence": 0, "peer_help": 0, "delivery": 0, "economic_truth": 0}),
        "memory": old.get("memory", {"accepted_lessons": [], "failed_patterns": [], "successful_patterns": []}),
        "traits": {
            "exploration": round(stable_float(agent_id, "exploration"), 4),
            "execution": round(stable_float(agent_id, "execution"), 4),
            "skepticism": round(stable_float(agent_id, "skepticism"), 4),
            "commercial": round(stable_float(agent_id, "commercial"), 4),
            "coordination": round(stable_float(agent_id, "coordination"), 4),
        },
    }
    life.ensure_life(agent, at)
    return agent


def bootstrap_agents() -> list[dict[str, Any]]:
    current = read_json(AGENTS, [])
    by_id = {x.get("id"): x for x in current if isinstance(x, dict)}
    agents = []
    for row in competitor_rows():
        item = normalize_agent(row, by_id.get(str(row.get("competitor_id") or row.get("id") or "").lower()))
        if item:
            agents.append(item)
    agents.sort(key=lambda x: (x.get("number") is None, x.get("number") or 10**9))
    write_json(AGENTS, agents)
    return agents


def evidence_score(agent: dict[str, Any]) -> float:
    rep = agent.get("reputation", {})
    traits = agent.get("traits", {})
    return (
        rep.get("evidence", 0) * 3
        + rep.get("peer_help", 0) * 2
        + rep.get("delivery", 0) * 3
        + rep.get("economic_truth", 0) * 5
        + traits.get("execution", 0)
        + traits.get("coordination", 0)
    )


def route_catalog() -> list[dict[str, Any]]:
    raw = read_json(PLAYBOOK, {})
    if isinstance(raw, list):
        return raw
    if isinstance(raw, dict):
        for key in ("routes", "items", "playbook"):
            if isinstance(raw.get(key), list):
                return raw[key]
    return []


def ensure_queue(agents: list[dict[str, Any]]) -> list[dict[str, Any]]:
    queue = read_json(QUEUE, [])
    open_tasks = [x for x in queue if x.get("status") in {"open", "assigned", "review"}]
    if open_tasks:
        return queue
    routes = route_catalog()
    latest = read_json(LATEST, {})
    seeds: list[dict[str, Any]] = []
    if latest:
        seeds.append({
            "title": latest.get("result", {}).get("opportunity") or "Revalidar última oportunidad",
            "source": "data/latest.json",
            "gate": "research",
        })
    for i, route in enumerate(routes[:8]):
        title = route.get("name") or route.get("title") or route.get("route") or f"Playbook route {i+1}"
        seeds.append({"title": str(title), "source": "data/monetization_playbook.json", "gate": "research"})
    if not seeds:
        seeds = [{"title": "Encontrar una necesidad verificable para un producto AMO existente", "source": "bootstrap", "gate": "research"}]
    queue = []
    for idx, seed in enumerate(seeds, 1):
        queue.append({
            "id": f"task-{idx:03d}",
            "title": seed["title"],
            "source": seed["source"],
            "gate": seed["gate"],
            "status": "open",
            "cell_id": None,
            "created_at": now(),
            "updated_at": now(),
            "evidence": [],
            "artifacts": [],
            "peer_reviews": [],
            "handoff": None,
            "verified_net_profit_eur": "0.00",
        })
    write_json(QUEUE, queue)
    return queue


def choose_member(pool: list[dict[str, Any]], role: str, used: set[str]) -> dict[str, Any] | None:
    candidates = [a for a in pool if a["id"] not in used and not a.get("cell_id")]
    if not candidates:
        return None
    key_map = {"scout": "exploration", "builder": "execution", "seller": "commercial", "critic": "skepticism", "accountant": "coordination"}
    trait = key_map[role]
    candidates.sort(key=lambda a: (a.get("role") == role, a.get("traits", {}).get(trait, 0), evidence_score(a)), reverse=True)
    return candidates[0]


def form_cells(agents: list[dict[str, Any]], queue: list[dict[str, Any]], max_cells: int = 21) -> list[dict[str, Any]]:
    cells = []
    used: set[str] = set()
    open_tasks = [t for t in queue if t.get("status") == "open"][:max_cells]
    for task in open_tasks:
        members = []
        for role in ROLES:
            member = choose_member(agents, role, used)
            if member:
                members.append({"agent_id": member["id"], "role": role})
                used.add(member["id"])
        if len(members) < 3:
            continue
        cell_id = f"cell-{task['id'].split('-')[-1]}"
        for m in members:
            agent = next(a for a in agents if a["id"] == m["agent_id"])
            agent["cell_id"] = cell_id
            agent["task_id"] = task["id"]
            agent["state"] = "cell"
        task["cell_id"] = cell_id
        task["status"] = "assigned"
        task["updated_at"] = now()
        cells.append({
            "id": cell_id,
            "task_id": task["id"],
            "status": "active",
            "members": members,
            "gate": task.get("gate", "research"),
            "created_at": now(),
            "updated_at": now(),
        })
    write_json(AGENTS, agents)
    write_json(QUEUE, queue)
    write_json(CELLS_FILE, cells)
    return cells


def advance_simulation(agents: list[dict[str, Any]], queue: list[dict[str, Any]], cells: list[dict[str, Any]]) -> None:
    by_agent = {a["id"]: a for a in agents}
    by_task = {t["id"]: t for t in queue}
    for cell in cells:
        task = by_task[cell["task_id"]]
        members = [by_agent[m["agent_id"]] for m in cell["members"]]
        scout = next((a for a, m in zip(members, cell["members"]) if m["role"] == "scout"), None)
        critic = next((a for a, m in zip(members, cell["members"]) if m["role"] == "critic"), None)
        research_strength = sum(a["traits"]["exploration"] for a in members) / len(members)
        review_strength = critic["traits"]["skepticism"] if critic else 0.5
        if task["gate"] == "research":
            task["status"] = "review"
            task["peer_reviews"].append({
                "at": now(),
                "reviewer": critic["id"] if critic else members[-1]["id"],
                "verdict": "needs_external_evidence",
                "note": "La célula debe aportar evidencia externa verificable antes de escalar.",
            })
            for a in members:
                a["state"] = "peer_review"
            if scout:
                scout["reputation"]["evidence"] += 0
        task["updated_at"] = now()
        cell["updated_at"] = now()
    write_json(AGENTS, agents)
    write_json(QUEUE, queue)
    write_json(CELLS_FILE, cells)


def summary(agents: list[dict[str, Any]], queue: list[dict[str, Any]], cells: list[dict[str, Any]]) -> dict[str, Any]:
    states = defaultdict(int)
    roles = defaultdict(int)
    for a in agents:
        states[a.get("state", "unknown")] += 1
        roles[a.get("role", "unknown")] += 1
    result = {
        "schema_version": "1.0",
        "generated_at": now(),
        "agent_count": len(agents),
        "cell_count": len(cells),
        "task_count": len(queue),
        "agent_states": dict(sorted(states.items())),
        "agent_roles": dict(sorted(roles.items())),
        "open_tasks": sum(1 for t in queue if t.get("status") == "open"),
        "assigned_tasks": sum(1 for t in queue if t.get("status") in {"assigned", "review"}),
        "verified_profit_source": "data/earnings.jsonl only",
        "verified_profit_rule": "Only externally verifiable received money changes the economic ranking.",
        "next_action": "Cells in peer_review must add external evidence before execution handoff.",
    }
    write_json(SUMMARY, result)
    return result


def run(max_cells: int = 21) -> dict[str, Any]:
    agents = bootstrap_agents()
    queue = ensure_queue(agents)
    cells = form_cells(agents, queue, max_cells=max_cells)
    advance_simulation(agents, queue, cells)
    return summary(agents, queue, cells)


if __name__ == "__main__":
    print(json.dumps(run(int(os.environ.get("IAMOX_MAX_CELLS", "21"))), ensure_ascii=False, indent=2))
