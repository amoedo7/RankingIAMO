from __future__ import annotations

import hashlib
import re
from typing import Any

LINEAGE_ROOT = "IAMO1"
DEFAULT_BIRTHPLACE = "github:amoedo7/RankingIAMO"
_SAFE = re.compile(r"[^a-z0-9]+", re.IGNORECASE)


def _slug(value: str) -> str:
    cleaned = _SAFE.sub("-", str(value or "unknown").strip().lower()).strip("-")
    return cleaned or "unknown"


def birth_uid(
    display_name: str,
    born_at: str,
    birthplace: str,
    parent_birth_uid: str | None = None,
    *,
    lineage_root: str = LINEAGE_ROOT,
) -> str:
    material = "|".join(
        [lineage_root, birthplace, display_name, born_at, parent_birth_uid or "root"]
    )
    digest = hashlib.sha256(material.encode("utf-8")).hexdigest()[:20]
    return f"iamo:{_slug(lineage_root)}:{_slug(birthplace)}:{digest}"


def ensure_identity(
    agent: dict[str, Any],
    *,
    row: dict[str, Any] | None = None,
    birthplace: str = DEFAULT_BIRTHPLACE,
) -> dict[str, Any]:
    row = row or {}
    old = agent.get("identity") if isinstance(agent.get("identity"), dict) else {}
    display_name = str(row.get("name") or row.get("competitor_name") or agent.get("name") or agent.get("id") or "IAMO")
    born_at = str(row.get("born_at") or old.get("born_at") or agent.get("born_at") or f"legacy:{agent.get('id') or display_name}")
    place = str(row.get("birthplace") or old.get("birthplace") or birthplace)
    parent_uid = row.get("parent_birth_uid") or old.get("parent_birth_uid")
    generation = row.get("lineage_generation", old.get("generation"))
    if generation is None:
        generation = 0 if display_name.upper() == LINEAGE_ROOT else 1
    uid = str(row.get("birth_uid") or old.get("birth_uid") or birth_uid(display_name, born_at, place, parent_uid))
    identity = {
        "birth_uid": uid,
        "display_name": display_name,
        "encounter_alias": str(old.get("encounter_alias") or display_name),
        "born_at": born_at,
        "birthplace": place,
        "lineage_root": str(old.get("lineage_root") or LINEAGE_ROOT),
        "generation": int(generation or 0),
        "parent_birth_uid": parent_uid,
    }
    agent["identity"] = identity
    return identity


def _place_code(value: str) -> str:
    parts = [_slug(x) for x in str(value or "host").split(":") if x]
    code = "-".join(parts[-2:]) if parts else "host"
    return code[:14]


def assign_encounter_aliases(agents: list[dict[str, Any]]) -> int:
    groups: dict[str, list[dict[str, Any]]] = {}
    for agent in agents:
        identity = ensure_identity(agent)
        groups.setdefault(identity["display_name"].casefold(), []).append(agent)

    collisions = 0
    for peers in groups.values():
        distinct = {p["identity"]["birth_uid"] for p in peers}
        if len(distinct) <= 1:
            for peer in peers:
                peer["identity"]["encounter_alias"] = peer["identity"]["display_name"]
            continue
        collisions += len(peers)
        for peer in peers:
            ident = peer["identity"]
            suffix = ident["birth_uid"].split(":")[-1][:6]
            ident["encounter_alias"] = f"{ident['display_name']}·{_place_code(ident['birthplace'])}-{suffix}"
    return collisions
