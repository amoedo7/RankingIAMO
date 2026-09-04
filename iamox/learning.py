from __future__ import annotations

import json
from pathlib import Path
from typing import Any

GATES = ("research", "offer", "artifact", "channel", "attempt", "payment")


def read_jsonl(path: Path, limit: int = 5000) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    try:
        with path.open("r", encoding="utf-8") as handle:
            for line in handle:
                line = line.strip()
                if not line:
                    continue
                try:
                    value = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if isinstance(value, dict):
                    rows.append(value)
                    if len(rows) > limit:
                        rows.pop(0)
    except OSError:
        pass
    return rows


def _remember(bucket: list[str], value: str, limit: int = 8) -> None:
    value = " ".join(str(value or "").split())[:220]
    if not value or value in bucket:
        return
    bucket.append(value)
    del bucket[:-limit]


def _rep(agent: dict[str, Any]) -> dict[str, int]:
    rep = agent.setdefault("reputation", {})
    for key in ("evidence", "peer_help", "delivery", "economic_truth", "cycles"):
        rep[key] = int(rep.get(key, 0) or 0)
    return rep


def learn_from_history(agents: list[dict[str, Any]], attempts_path: Path, earnings_path: Path, learned_at: str) -> None:
    by_id = {str(a.get("id", "")).lower(): a for a in agents}
    for attempt in read_jsonl(attempts_path):
        aid = str(attempt.get("competitor_id") or "").lower()
        agent = by_id.get(aid)
        if not agent:
            continue
        rep = _rep(agent)
        memory = agent.setdefault("memory", {"accepted_lessons": [], "failed_patterns": [], "successful_patterns": []})
        result = attempt.get("result") if isinstance(attempt.get("result"), dict) else {}
        status = str(attempt.get("status") or "")
        evidence = result.get("external_evidence_urls") if isinstance(result.get("external_evidence_urls"), list) else []
        if evidence:
            rep["evidence"] += 1
            _remember(memory.setdefault("accepted_lessons", []), f"External evidence found for: {result.get('opportunity') or result.get('summary')}")
        if status in {"attempt_completed", "executed", "offer_ready"}:
            rep["delivery"] += 1
        if status in {"research_incomplete", "invalid_agent_output", "error"}:
            _remember(memory.setdefault("failed_patterns", []), f"{status}: {result.get('summary') or result.get('opportunity') or aid}")

    for earning in read_jsonl(earnings_path):
        try:
            amount = float(earning.get("verified_net_profit_eur") or earning.get("net_profit_eur") or 0)
        except (TypeError, ValueError):
            amount = 0.0
        if amount <= 0:
            continue
        aid = str(earning.get("competitor_id") or earning.get("iamo_id") or "").lower()
        agent = by_id.get(aid)
        if not agent:
            continue
        rep = _rep(agent)
        rep["economic_truth"] += 1
        memory = agent.setdefault("memory", {"accepted_lessons": [], "failed_patterns": [], "successful_patterns": []})
        _remember(memory.setdefault("successful_patterns", []), f"Verified profit EUR {amount:.2f}")
    for agent in agents:
        _rep(agent)
        agent["last_learning_at"] = learned_at


def next_gate(current: str) -> str:
    try:
        idx = GATES.index(current)
    except ValueError:
        return "research"
    return GATES[min(idx + 1, len(GATES) - 1)]


def recycle_reviews(agents: list[dict[str, Any]], queue: list[dict[str, Any]], cells: list[dict[str, Any]], at: str) -> list[dict[str, Any]]:
    by_agent = {a.get("id"): a for a in agents}
    by_cell = {c.get("id"): c for c in cells}
    handoffs: list[dict[str, Any]] = []
    for task in queue:
        if task.get("status") != "review":
            continue
        task["review_rounds"] = int(task.get("review_rounds", 0) or 0) + 1
        cell = by_cell.get(task.get("cell_id"))
        evidence = task.get("evidence") if isinstance(task.get("evidence"), list) else []
        if evidence:
            task["gate"] = next_gate(str(task.get("gate") or "research"))
            task["status"] = "open"
            task["blocking_reason"] = None
        else:
            task["status"] = "blocked"
            task["blocking_reason"] = "needs_external_evidence"
            task["handoff"] = {
                "owner": "EjecutorIAMO",
                "action": "validate_external_demand",
                "created_at": at,
            }
            handoffs.append({"task_id": task.get("id"), "cell_id": task.get("cell_id"), **task["handoff"]})
        task["updated_at"] = at
        if cell:
            cell["status"] = "released"
            cell["updated_at"] = at
            for member in cell.get("members", []):
                agent = by_agent.get(member.get("agent_id"))
                if not agent:
                    continue
                if member.get("role") == "critic":
                    _rep(agent)["peer_help"] += 1
                agent["cell_id"] = None
                agent["task_id"] = None
                agent["state"] = "learn"
    return handoffs
