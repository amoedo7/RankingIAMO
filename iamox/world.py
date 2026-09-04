from __future__ import annotations

import hashlib
import json
import math
import os
from pathlib import Path
from typing import Any

WORLD_VERSION = "0.2.0"
WORLD_WIDTH = 2048
WORLD_HEIGHT = 1280
MARGIN = 70

ZONES = {
    "origin": {"name": "Portal de Origen", "x": 1010, "y": 620, "radius": 150},
    "forest": {"name": "Bosque de Exploración", "x": 430, "y": 330, "radius": 250},
    "market": {"name": "Mercado de Oportunidades", "x": 1600, "y": 360, "radius": 225},
    "workshop": {"name": "Taller de Construcción", "x": 1430, "y": 890, "radius": 230},
    "archive": {"name": "Archivo de Memoria", "x": 610, "y": 930, "radius": 230},
    "observatory": {"name": "Observatorio", "x": 1770, "y": 1010, "radius": 170},
    "harbor": {"name": "Puerto de Handoffs", "x": 300, "y": 1110, "radius": 150},
    "plaza": {"name": "Plaza DesarrollAMO", "x": 1030, "y": 930, "radius": 180},
}


def _hash_int(agent_id: str, salt: str, digits: int = 12) -> int:
    return int(hashlib.sha256(f"{agent_id}:{salt}".encode("utf-8")).hexdigest()[:digits], 16)


def _unit(agent_id: str, salt: str) -> float:
    return _hash_int(agent_id, salt, 8) / 0xFFFFFFFF


def _clamp(v: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, v))


def identity_key(agent: dict[str, Any]) -> str:
    identity = agent.get("identity") if isinstance(agent.get("identity"), dict) else {}
    return str(identity.get("birth_uid") or agent.get("id") or "iamo0")


def preferred_zone(agent: dict[str, Any], task: dict[str, Any] | None = None) -> str:
    brain = agent.get("brain") if isinstance(agent.get("brain"), dict) else {}
    intent = str(brain.get("intent") or "")
    state = str(agent.get("state") or "idle")
    role = str(agent.get("role") or "")
    if state in {"handoff", "blocked"} or "handoff" in intent:
        return "harbor"
    if "evidence" in intent or "observe" in intent or role == "critic":
        return "observatory" if role == "critic" else "forest"
    if "artifact" in intent or "build" in intent or role == "builder":
        return "workshop"
    if "market" in intent or role == "seller":
        return "market"
    if "memory" in intent or role == "accountant":
        return "archive"
    if "help_peer" in intent or state in {"cell", "peer_review"}:
        return "plaza"
    if role == "scout":
        return "forest"
    if task:
        return "plaza"
    return "origin"


def spawn(agent_id: str, zone_key: str) -> tuple[float, float]:
    zone = ZONES.get(zone_key, ZONES["origin"])
    angle = _unit(agent_id, "spawn-angle") * math.tau
    radius = 28 + _unit(agent_id, "spawn-radius") * (float(zone["radius"]) * 0.78)
    x = float(zone["x"]) + math.cos(angle) * radius
    y = float(zone["y"]) + math.sin(angle) * radius
    return round(_clamp(x, MARGIN, WORLD_WIDTH - MARGIN), 2), round(_clamp(y, MARGIN, WORLD_HEIGHT - MARGIN), 2)


def ensure_world(agent: dict[str, Any], at: str) -> dict[str, Any]:
    aid = identity_key(agent)
    old = agent.get("world") if isinstance(agent.get("world"), dict) else {}
    zone = str(old.get("zone") or preferred_zone(agent))
    if zone not in ZONES:
        zone = "origin"
    sx, sy = spawn(aid, zone)
    state = {
        "version": WORLD_VERSION,
        "zone": zone,
        "x": float(old.get("x", sx) or sx),
        "y": float(old.get("y", sy) or sy),
        "heading": float(old.get("heading", _unit(aid, "heading") * math.tau) or 0.0),
        "steps": int(old.get("steps", 0) or 0),
        "last_moved_at": old.get("last_moved_at") or at,
        "spawn_x": float(old.get("spawn_x", sx) or sx),
        "spawn_y": float(old.get("spawn_y", sy) or sy),
    }
    agent["world"] = state
    return state


def move_agent(agent: dict[str, Any], task: dict[str, Any] | None, at: str) -> dict[str, Any]:
    aid = identity_key(agent)
    world = ensure_world(agent, at)
    zone_key = preferred_zone(agent, task)
    zone = ZONES[zone_key]
    step_no = int(world.get("steps", 0) or 0) + 1
    brain = agent.get("brain") if isinstance(agent.get("brain"), dict) else {}
    temperament = brain.get("temperament") if isinstance(brain.get("temperament"), dict) else {}
    curiosity = float(temperament.get("curiosity", 0.5) or 0.5)
    patience = float(temperament.get("patience", 0.5) or 0.5)

    angle_noise = (_unit(aid, f"move-angle:{step_no}") - 0.5) * 1.5
    target_angle = math.atan2(float(zone["y"]) - world["y"], float(zone["x"]) - world["x"])
    if world.get("zone") == zone_key:
        target_angle = world["heading"] + angle_noise
    else:
        target_angle += angle_noise * 0.25

    base_step = 16 + curiosity * 26 + (1.0 - patience) * 11
    if str(agent.get("state") or "") in {"cell", "peer_review"}:
        base_step *= 1.15
    if str(agent.get("state") or "") in {"idle", "learn"}:
        base_step *= 0.68

    nx = world["x"] + math.cos(target_angle) * base_step
    ny = world["y"] + math.sin(target_angle) * base_step
    if world.get("zone") == zone_key:
        dx = nx - float(zone["x"])
        dy = ny - float(zone["y"])
        dist = math.hypot(dx, dy)
        limit = float(zone["radius"]) * 0.92
        if dist > limit:
            nx = float(zone["x"]) + dx / dist * limit
            ny = float(zone["y"]) + dy / dist * limit

    world["zone"] = zone_key
    world["x"] = round(_clamp(nx, MARGIN, WORLD_WIDTH - MARGIN), 2)
    world["y"] = round(_clamp(ny, MARGIN, WORLD_HEIGHT - MARGIN), 2)
    world["heading"] = round(target_angle, 5)
    world["steps"] = step_no
    world["last_moved_at"] = at
    return world


def _compact_task(task: dict[str, Any] | None) -> dict[str, Any] | None:
    if not task:
        return None
    return {
        "id": task.get("id"),
        "title": task.get("title"),
        "gate": task.get("gate"),
        "status": task.get("status"),
        "blocking_reason": task.get("blocking_reason"),
    }


def _public_identity(agent: dict[str, Any]) -> dict[str, Any]:
    identity = agent.get("identity") if isinstance(agent.get("identity"), dict) else {}
    display = str(identity.get("display_name") or agent.get("name") or agent.get("id") or "IAMO")
    alias = str(identity.get("encounter_alias") or display)
    return {
        "birth_uid": identity.get("birth_uid"),
        "display_name": display,
        "encounter_alias": alias,
        "birthplace": identity.get("birthplace"),
        "generation": identity.get("generation"),
        "parent_birth_uid": identity.get("parent_birth_uid"),
        "lineage_root": identity.get("lineage_root"),
    }


def public_agent(agent: dict[str, Any], task: dict[str, Any] | None) -> dict[str, Any]:
    brain = agent.get("brain") if isinstance(agent.get("brain"), dict) else {}
    world = agent.get("world") if isinstance(agent.get("world"), dict) else {}
    life = agent.get("life") if isinstance(agent.get("life"), dict) else {}
    identity = _public_identity(agent)
    return {
        "id": agent.get("id"),
        "name": agent.get("name"),
        "encounter_name": identity["encounter_alias"],
        "number": agent.get("number"),
        "identity": identity,
        "role": agent.get("role"),
        "state": agent.get("state"),
        "cell_id": agent.get("cell_id"),
        "task_id": agent.get("task_id"),
        "heartbeat_at": agent.get("heartbeat_at"),
        "brain": {
            "version": brain.get("version"),
            "signature": brain.get("signature"),
            "archetype": brain.get("archetype"),
            "intent": brain.get("intent"),
            "interpretation": brain.get("interpretation"),
            "confidence": brain.get("confidence"),
            "affiliation": brain.get("affiliation"),
        },
        "life": {
            "heartbeats": life.get("heartbeats", 0),
            "progress_events": life.get("progress_events", 0),
            "stagnation": life.get("stagnation", 0),
            "directive": life.get("directive"),
            "reproduction": life.get("reproduction", {}),
        },
        "world": {
            "version": world.get("version"),
            "zone": world.get("zone"),
            "zone_name": ZONES.get(str(world.get("zone")), {}).get("name"),
            "x": world.get("x"),
            "y": world.get("y"),
            "heading": world.get("heading"),
            "steps": world.get("steps", 0),
        },
        "task": _compact_task(task),
        "reputation": agent.get("reputation", {}),
        "memory": agent.get("memory", {}),
    }


def report_filename(agent: dict[str, Any]) -> str:
    identity = _public_identity(agent)
    display = identity["display_name"]
    alias = identity["encounter_alias"]
    uid = str(identity.get("birth_uid") or "")
    if alias != display and uid:
        return f"{display}-{uid.split(':')[-1][:8]}.json"
    number = agent.get("number")
    if number is not None:
        return f"IAMO{int(number)}.json"
    return f"{str(agent.get('id') or 'iamo').upper()}.json"


def report_path(report_dir: Path, agent: dict[str, Any]) -> Path:
    return report_dir / "agents" / report_filename(agent)


def _stable_report_payload(public: dict[str, Any]) -> dict[str, Any]:
    copy = json.loads(json.dumps(public, ensure_ascii=False))
    world = copy.get("world") if isinstance(copy.get("world"), dict) else {}
    if "x" in world and world.get("x") is not None:
        world["x"] = round(float(world["x"]) / 48) * 48
    if "y" in world and world.get("y") is not None:
        world["y"] = round(float(world["y"]) / 48) * 48
    copy["heartbeat_at"] = None
    return copy


def write_reports(agents: list[dict[str, Any]], queue: list[dict[str, Any]], at: str, report_dir: Path) -> int:
    by_task = {str(t.get("id")): t for t in queue if isinstance(t, dict)}
    changed = 0
    report_dir.mkdir(parents=True, exist_ok=True)
    (report_dir / "agents").mkdir(parents=True, exist_ok=True)
    for agent in agents:
        task = by_task.get(str(agent.get("task_id") or ""))
        public = public_agent(agent, task)
        path = report_path(report_dir, agent)
        previous = None
        try:
            previous = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            pass
        previous_public = previous.get("agent") if isinstance(previous, dict) else None
        if previous_public is not None and _stable_report_payload(previous_public) == _stable_report_payload(public):
            continue
        payload = {
            "schema": "iamox.report.v1",
            "reported_at": at,
            "agent": public,
        }
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
        changed += 1
    return changed


def pulse_world(
    agents: list[dict[str, Any]],
    queue: list[dict[str, Any]],
    at: str,
    *,
    snapshot_path: Path,
    report_dir: Path,
) -> dict[str, Any]:
    by_task = {str(t.get("id")): t for t in queue if isinstance(t, dict)}
    zones: dict[str, int] = {}
    snapshot_agents: list[dict[str, Any]] = []
    for agent in agents:
        task = by_task.get(str(agent.get("task_id") or ""))
        world = move_agent(agent, task, at)
        zone_key = str(world.get("zone") or "origin")
        zones[zone_key] = zones.get(zone_key, 0) + 1
        snapshot_agents.append(public_agent(agent, task))

    snapshot = {
        "schema": "iamox.world.snapshot.v2",
        "world_version": WORLD_VERSION,
        "generated_at": at,
        "bounds": {"width": WORLD_WIDTH, "height": WORLD_HEIGHT},
        "zones": ZONES,
        "agent_count": len(snapshot_agents),
        "agents": snapshot_agents,
        "note": "Public observation snapshot: movement is reported by IAMOX runtime; birth_uid preserves identity and encounter aliases disambiguate independent same-name births.",
    }
    snapshot_path.parent.mkdir(parents=True, exist_ok=True)
    tmp = snapshot_path.with_suffix(snapshot_path.suffix + ".tmp")
    tmp.write_text(json.dumps(snapshot, ensure_ascii=False, separators=(",", ":"), sort_keys=True), encoding="utf-8")
    os.replace(tmp, snapshot_path)
    changed_reports = write_reports(agents, queue, at, report_dir)
    return {
        "version": WORLD_VERSION,
        "agents_on_map": len(snapshot_agents),
        "zones": dict(sorted(zones.items())),
        "reports_changed": changed_reports,
        "snapshot": str(snapshot_path),
    }
