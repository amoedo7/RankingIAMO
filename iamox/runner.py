from __future__ import annotations

import hashlib
import json
import os
from typing import Any

import brain
import learning
import life
import reproduction
import runtime
import world

HANDOFFS = runtime.IAMOX / "handoffs" / "pending.json"
REPORTS = runtime.IAMOX / "reports"
WORLD_SNAPSHOT = runtime.IAMOX / "world" / "snapshot.json"
MAX_NEW_TASKS = int(os.environ.get("IAMOX_NEW_TASKS_PER_ROUND", "9"))
MAX_CELLS = int(os.environ.get("IAMOX_MAX_CELLS", "21"))


def rotating_choice(pool: list[dict[str, Any]], role: str, used: set[str]) -> dict[str, Any] | None:
    candidates = [a for a in pool if a["id"] not in used and not a.get("cell_id")]
    if not candidates:
        return None
    trait_for = {"scout": "exploration", "builder": "execution", "seller": "commercial", "critic": "skepticism", "accountant": "coordination"}
    trait = trait_for[role]
    candidates.sort(
        key=lambda a: (
            int(a.get("reputation", {}).get("cycles", 0) or 0),
            int(a.get("life", {}).get("stagnation", 0) or 0),
            -(1 if a.get("role") == role else 0),
            -float(a.get("traits", {}).get(trait, 0) or 0),
            -float(runtime.evidence_score(a)),
            a["id"],
        )
    )
    return candidates[0]


def task_id(title: str, queue: list[dict[str, Any]]) -> str:
    digest = hashlib.sha256(title.encode("utf-8")).hexdigest()[:10]
    existing = {str(x.get("id")) for x in queue}
    candidate = f"task-{digest}"
    if candidate not in existing:
        return candidate
    return f"task-{digest}-{len(queue)+1}"


def append_unseen_tasks(queue: list[dict[str, Any]], at: str, limit: int = MAX_NEW_TASKS) -> int:
    if any(t.get("status") == "open" for t in queue):
        return 0
    seen = {str(t.get("title") or "").strip().lower() for t in queue}
    seeds: list[tuple[str, str]] = []
    latest = runtime.read_json(runtime.LATEST, {})
    latest_title = str(latest.get("result", {}).get("opportunity") or "").strip()
    if latest_title:
        seeds.append((latest_title, "data/latest.json"))
    for route in runtime.route_catalog():
        title = str(route.get("name") or route.get("title") or route.get("route") or "").strip()
        if title:
            seeds.append((title, "data/monetization_playbook.json"))
    added = 0
    for title, source in seeds:
        if title.lower() in seen:
            continue
        queue.append({
            "id": task_id(title, queue),
            "title": title,
            "source": source,
            "gate": "research",
            "status": "open",
            "cell_id": None,
            "created_at": at,
            "updated_at": at,
            "evidence": [],
            "artifacts": [],
            "peer_reviews": [],
            "handoff": None,
            "verified_net_profit_eur": "0.00",
        })
        seen.add(title.lower())
        added += 1
        if added >= limit:
            break
    return added


def recycle_orphans(agents: list[dict[str, Any]], cells: list[dict[str, Any]]) -> int:
    active_cells = {str(c.get("id")) for c in cells if c.get("status") == "active"}
    repaired = 0
    for agent in agents:
        cell_id = agent.get("cell_id")
        if cell_id and str(cell_id) not in active_cells:
            agent["cell_id"] = None
            agent["task_id"] = None
            agent["state"] = "learn"
            repaired += 1
        elif not cell_id and agent.get("state") == "learn":
            agent["state"] = "idle"
    return repaired


def run() -> dict[str, Any]:
    at = runtime.now()
    agents = runtime.bootstrap_agents()
    learning.learn_from_history(agents, runtime.DATA / "attempts.jsonl", runtime.EARNINGS, at)

    queue = runtime.read_json(runtime.QUEUE, [])
    if not queue:
        queue = runtime.ensure_queue(agents)
    previous_cells = runtime.read_json(runtime.CELLS_FILE, [])
    repaired_orphans = recycle_orphans(agents, previous_cells)
    handoffs = learning.recycle_reviews(agents, queue, previous_cells, at)
    append_unseen_tasks(queue, at)

    runtime.choose_member = rotating_choice
    cells = runtime.form_cells(agents, queue, max_cells=MAX_CELLS)
    by_agent = {a["id"]: a for a in agents}
    for cell in cells:
        for member in cell.get("members", []):
            agent = by_agent.get(member.get("agent_id"))
            if agent:
                rep = agent.setdefault("reputation", {})
                rep["cycles"] = int(rep.get("cycles", 0) or 0) + 1

    runtime.advance_simulation(agents, queue, cells)
    life.heartbeat_population(agents, queue, at)

    reproduction_summary = reproduction.reproduce(agents, at)
    runtime.write_json(runtime.AGENTS, agents)
    if reproduction_summary.get("births"):
        agents = runtime.bootstrap_agents()

    life_summary = life.population_summary(agents)
    brain_summary = brain.pulse_brains(agents, queue, at)
    world_summary = world.pulse_world(
        agents,
        queue,
        at,
        snapshot_path=WORLD_SNAPSHOT,
        report_dir=REPORTS,
    )

    runtime.write_json(runtime.AGENTS, agents)
    runtime.write_json(HANDOFFS, handoffs[:21])
    result = runtime.summary(agents, queue, cells)
    result["pending_handoffs"] = len(handoffs)
    result["learning_enabled"] = True
    result["repaired_orphans"] = repaired_orphans
    result["life"] = life_summary
    result["reproduction"] = reproduction_summary
    result["brain"] = brain_summary
    result["world"] = world_summary
    runtime.write_json(runtime.SUMMARY, result)
    return result


if __name__ == "__main__":
    print(json.dumps(run(), ensure_ascii=False, indent=2))
