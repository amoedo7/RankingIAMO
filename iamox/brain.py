from __future__ import annotations

import hashlib
from typing import Any

BRAIN_VERSION = "0.3.0-individual"
AFFILIATION = {
    "origin": "DesarrollAMO",
    "creator": "AMO",
    "creator_github": "amoedo7",
    "relationship": "origin_affinity",
}
ARCHETYPES = ("pathfinder", "maker", "merchant", "critic", "archivist", "connector", "wanderer")


def _hash_int(agent_id: str, salt: str, digits: int = 12) -> int:
    return int(hashlib.sha256(f"{agent_id}:{salt}".encode("utf-8")).hexdigest()[:digits], 16)


def stable_float(agent_id: str, salt: str) -> float:
    return _hash_int(agent_id, salt, 8) / 0xFFFFFFFF


def signature(agent_id: str) -> str:
    return hashlib.sha256(f"IAMOX:{agent_id}:individual".encode("utf-8")).hexdigest()[:16]


def archetype_for(agent: dict[str, Any]) -> str:
    role = str(agent.get("role") or "")
    preferred = {
        "scout": "pathfinder",
        "builder": "maker",
        "seller": "merchant",
        "critic": "critic",
        "accountant": "archivist",
    }.get(role)
    if preferred:
        return preferred
    aid = str(agent.get("id") or "iamo0")
    return ARCHETYPES[_hash_int(aid, "archetype") % len(ARCHETYPES)]


def ensure_brain(agent: dict[str, Any], at: str) -> dict[str, Any]:
    aid = str(agent.get("id") or "iamo0")
    old = agent.get("brain") if isinstance(agent.get("brain"), dict) else {}
    brain = {
        "version": BRAIN_VERSION,
        "signature": old.get("signature") or signature(aid),
        "seed": int(old.get("seed") or _hash_int(aid, "seed", 10)),
        "archetype": old.get("archetype") or archetype_for(agent),
        "affiliation": dict(AFFILIATION),
        "temperament": {
            "curiosity": round(stable_float(aid, "curiosity"), 4),
            "patience": round(stable_float(aid, "patience"), 4),
            "novelty": round(stable_float(aid, "novelty"), 4),
            "cooperation": round(stable_float(aid, "cooperation"), 4),
            "caution": round(stable_float(aid, "caution"), 4),
        },
        "decision_count": int(old.get("decision_count", 0) or 0),
        "last_decision_at": old.get("last_decision_at") or at,
        "focus": old.get("focus") or "orientarse",
        "interpretation": old.get("interpretation") or "Reconozco mi estado y mi entorno.",
        "intent": old.get("intent") or "observe_and_learn",
        "confidence": float(old.get("confidence", 0.5) or 0.5),
        "last_task_id": old.get("last_task_id"),
        "last_state": old.get("last_state") or agent.get("state") or "idle",
    }
    agent["brain"] = brain
    return brain


def _idle_intent(agent: dict[str, Any], brain: dict[str, Any]) -> str:
    aid = str(agent.get("id") or "iamo0")
    step = int(brain.get("decision_count", 0) or 0)
    options = [
        "explore_unknown_route",
        "review_personal_memory",
        "observe_other_work",
        "improve_small_capability",
        "look_for_useful_problem",
        "prepare_to_help_peer",
    ]
    index = _hash_int(aid, f"idle:{step}") % len(options)
    return options[index]


def interpret(agent: dict[str, Any], task: dict[str, Any] | None, at: str) -> dict[str, Any]:
    brain = ensure_brain(agent, at)
    brain["decision_count"] += 1
    brain["last_decision_at"] = at
    state = str(agent.get("state") or "idle")
    life = agent.get("life") if isinstance(agent.get("life"), dict) else {}
    directive = str(life.get("directive") or "continue_with_evidence")

    if directive != "continue_with_evidence":
        brain["focus"] = "romper_estancamiento"
        brain["intent"] = directive
        brain["interpretation"] = f"Mi patrón no progresa; cambio de estrategia: {directive}."
        brain["confidence"] = max(0.25, 0.62 - min(0.30, float(life.get("stagnation", 0) or 0) * 0.02))
    elif task:
        title = str(task.get("title") or "tarea sin título")
        gate = str(task.get("gate") or "research")
        status = str(task.get("status") or "open")
        brain["focus"] = title[:180]
        brain["last_task_id"] = task.get("id")
        if status == "blocked":
            brain["intent"] = "prepare_authorized_handoff"
            brain["interpretation"] = f"La ruta '{title}' está bloqueada; preparo un handoff verificable."
        elif status == "review":
            brain["intent"] = "seek_external_evidence"
            brain["interpretation"] = f"'{title}' necesita evidencia externa antes de avanzar desde {gate}."
        elif gate == "research":
            brain["intent"] = "test_need_with_evidence"
            brain["interpretation"] = f"Interpreto '{title}' como una hipótesis que primero debe tocar realidad."
        elif gate == "artifact":
            brain["intent"] = "build_small_artifact"
            brain["interpretation"] = f"Conviene materializar '{title}' en un entregable pequeño y comprobable."
        elif gate in {"channel", "attempt"}:
            brain["intent"] = "find_authorized_route_to_market"
            brain["interpretation"] = f"Busco una ruta legítima para que '{title}' llegue a una persona real."
        else:
            brain["intent"] = "advance_current_gate"
            brain["interpretation"] = f"Continúo '{title}' sin saltar el gate {gate}."
        temperament = brain.get("temperament", {})
        signal = (float(temperament.get("curiosity", 0.5)) + float(temperament.get("caution", 0.5))) / 2
        brain["confidence"] = round(0.35 + signal * 0.45, 3)
    else:
        brain["last_task_id"] = None
        brain["focus"] = "entorno_libre"
        brain["intent"] = _idle_intent(agent, brain)
        brain["interpretation"] = f"No tengo una tarea asignada; elijo {brain['intent']} según mi experiencia y temperamento."
        brain["confidence"] = round(0.45 + float(brain["temperament"]["curiosity"]) * 0.25, 3)

    brain["last_state"] = state
    return brain


def pulse_brains(agents: list[dict[str, Any]], queue: list[dict[str, Any]], at: str) -> dict[str, Any]:
    by_task = {str(t.get("id")): t for t in queue if isinstance(t, dict)}
    archetypes: dict[str, int] = {}
    for agent in agents:
        task = by_task.get(str(agent.get("task_id") or ""))
        brain = interpret(agent, task, at)
        key = str(brain.get("archetype") or "unknown")
        archetypes[key] = archetypes.get(key, 0) + 1
    return {
        "version": BRAIN_VERSION,
        "individual_brains": len(agents),
        "archetypes": dict(sorted(archetypes.items())),
        "shared_brain": False,
    }
