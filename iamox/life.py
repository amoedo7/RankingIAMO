from __future__ import annotations

import re
from typing import Any

GENOME_VERSION = "0.4.0-population"
CREATOR = {
    "name": "AMO",
    "github": "amoedo7",
    "origin": "IAMO / RankingIAMO",
}
LINEAGE = {
    "prototype": "IAMO1 v0.3.0",
    "inheritance": "shared_runtime",
}
SCOPE = {
    "mode": "authorized_ecosystem_only",
    "self_propagation": False,
    "credential_discovery": False,
    "external_writes_require_authorization": True,
}
FIBONACCI = (1, 1, 2, 3, 5, 8, 13, 21, 34, 55)
MAX_RECENT_FOCUS = 8
SIMILARITY_THRESHOLD = 0.60

_WORDS = re.compile(r"[a-z0-9áéíóúüñ]+", re.IGNORECASE)
_STOPWORDS = {
    "a", "al", "algo", "and", "como", "con", "de", "del", "el", "en", "es", "esta", "este",
    "for", "la", "las", "los", "of", "o", "para", "por", "que", "se", "the", "to", "un", "una",
    "y",
}


def fibonacci(index: int) -> int:
    if index <= 0:
        return 1
    if index < len(FIBONACCI):
        return FIBONACCI[index]
    a, b = FIBONACCI[-2], FIBONACCI[-1]
    for _ in range(len(FIBONACCI), index + 1):
        a, b = b, a + b
    return b


def canonical_focus(text: str) -> str:
    tokens = [w.lower() for w in _WORDS.findall(str(text or ""))]
    useful = sorted({w for w in tokens if len(w) > 2 and w not in _STOPWORDS})
    return " ".join(useful)


def semantic_similarity(left: str, right: str) -> float:
    a = set(canonical_focus(left).split())
    b = set(canonical_focus(right).split())
    if not a or not b:
        return 0.0
    return len(a & b) / min(len(a), len(b))


def is_semantic_repeat(focus: str, recent: list[str]) -> bool:
    if not focus:
        return False
    return any(semantic_similarity(focus, old) >= SIMILARITY_THRESHOLD for old in recent if old)


def directive_for(stagnation: int) -> str:
    if stagnation >= 13:
        return "owner_review_required"
    if stagnation >= 8:
        return "abandon_local_loop_and_change_route"
    if stagnation >= 5:
        return "seek_new_external_evidence"
    if stagnation >= 3:
        return "request_peer_counterexample"
    if stagnation >= 2:
        return "switch_method_or_tool"
    if stagnation >= 1:
        return "try_distinct_reversible_variant"
    return "continue_with_evidence"


def default_life(old: dict[str, Any] | None, at: str) -> dict[str, Any]:
    old = old if isinstance(old, dict) else {}
    recent = old.get("recent_focus") if isinstance(old.get("recent_focus"), list) else []
    return {
        "genome_version": GENOME_VERSION,
        "creator": dict(CREATOR),
        "lineage": dict(LINEAGE),
        "scope": dict(SCOPE),
        "born_at": old.get("born_at") or at,
        "last_heartbeat_at": old.get("last_heartbeat_at") or at,
        "heartbeats": int(old.get("heartbeats", 0) or 0),
        "age_rounds": int(old.get("age_rounds", 0) or 0),
        "stagnation": int(old.get("stagnation", 0) or 0),
        "fibonacci_index": int(old.get("fibonacci_index", 0) or 0),
        "fibonacci_budget": int(old.get("fibonacci_budget", 1) or 1),
        "loop_breaks": int(old.get("loop_breaks", 0) or 0),
        "progress_events": int(old.get("progress_events", 0) or 0),
        "recent_focus": [str(x) for x in recent[-MAX_RECENT_FOCUS:]],
        "last_progress_marker": old.get("last_progress_marker"),
        "directive": old.get("directive") or "continue_with_evidence",
        "next_action": old.get("next_action") or "observe",
    }


def ensure_life(agent: dict[str, Any], at: str) -> dict[str, Any]:
    life = default_life(agent.get("life"), at)
    agent["life"] = life
    return life


def observe(
    agent: dict[str, Any],
    focus: str,
    at: str,
    *,
    progress_marker: str | None = None,
) -> dict[str, Any]:
    life = ensure_life(agent, at)
    life["heartbeats"] += 1
    life["age_rounds"] += 1
    life["last_heartbeat_at"] = at

    canonical = canonical_focus(focus)
    previous_marker = life.get("last_progress_marker")
    made_progress = progress_marker is not None and progress_marker != previous_marker

    if made_progress:
        life["progress_events"] += 1
        life["stagnation"] = 0
        life["fibonacci_index"] = 0
        life["last_progress_marker"] = progress_marker
    elif canonical:
        if is_semantic_repeat(canonical, life["recent_focus"]):
            life["stagnation"] += 1
            life["fibonacci_index"] = min(life["fibonacci_index"] + 1, 64)
            life["loop_breaks"] += 1
        else:
            life["stagnation"] = max(0, life["stagnation"] - 1)
            life["fibonacci_index"] = max(0, life["fibonacci_index"] - 1)

    if canonical:
        recent = life["recent_focus"]
        recent.append(canonical)
        del recent[:-MAX_RECENT_FOCUS]

    life["fibonacci_budget"] = fibonacci(life["fibonacci_index"])
    life["directive"] = directive_for(life["stagnation"])
    return life


def task_progress_marker(task: dict[str, Any]) -> str:
    evidence = task.get("evidence") if isinstance(task.get("evidence"), list) else []
    artifacts = task.get("artifacts") if isinstance(task.get("artifacts"), list) else []
    handoff = task.get("handoff") if isinstance(task.get("handoff"), dict) else {}
    return "|".join(
        [
            str(task.get("id") or ""),
            str(task.get("gate") or ""),
            str(task.get("status") or ""),
            str(len(evidence)),
            str(len(artifacts)),
            str(handoff.get("action") or ""),
        ]
    )


def seed_next_action(agent: dict[str, Any], task: dict[str, Any] | None) -> str:
    life = agent.get("life") if isinstance(agent.get("life"), dict) else {}
    directive = str(life.get("directive") or "continue_with_evidence")
    if directive != "continue_with_evidence":
        return directive
    if not task:
        return "observe_and_learn"
    status = str(task.get("status") or "")
    if status == "blocked":
        return "prepare_authorized_handoff"
    if status == "review":
        return "seek_external_evidence"
    if status in {"open", "assigned"}:
        return "advance_current_gate"
    return "learn_from_result"


def heartbeat_population(agents: list[dict[str, Any]], queue: list[dict[str, Any]], at: str) -> dict[str, Any]:
    by_task = {str(t.get("id")): t for t in queue if isinstance(t, dict)}
    for agent in agents:
        task = by_task.get(str(agent.get("task_id") or ""))
        focus = ""
        marker = None
        if task:
            focus = " ".join(
                [
                    str(task.get("title") or ""),
                    str(task.get("gate") or ""),
                    str(task.get("blocking_reason") or ""),
                ]
            )
            marker = task_progress_marker(task)
        life = observe(agent, focus, at, progress_marker=marker)
        life["next_action"] = seed_next_action(agent, task)
        agent["heartbeat_at"] = at
    return population_summary(agents)


def population_summary(agents: list[dict[str, Any]]) -> dict[str, Any]:
    lives = [a.get("life", {}) for a in agents if isinstance(a.get("life"), dict)]
    return {
        "living_agents": len(lives),
        "genome_version": GENOME_VERSION,
        "creator": dict(CREATOR),
        "stagnating_agents": sum(1 for x in lives if int(x.get("stagnation", 0) or 0) >= 3),
        "loop_breaks": sum(int(x.get("loop_breaks", 0) or 0) for x in lives),
        "total_heartbeats": sum(int(x.get("heartbeats", 0) or 0) for x in lives),
        "scope": dict(SCOPE),
    }
