#!/usr/bin/env python3

import json
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
NETWORK = ROOT / "network"
EXECUTOR = ROOT / "executor"
COMPETITORS = DATA / "competitors.json"
ATTEMPTS = DATA / "attempts.jsonl"
LEADERBOARD = ROOT / "leaderboard.json"
PROXIMITY = ROOT / "proximity.json"
AGENTS = DATA / "agents.json"
CELLS = NETWORK / "cells.json"
OPPORTUNITIES = DATA / "opportunities.json"
BOARD = NETWORK / "board.jsonl"

MONEY_POLICY = {
    "verified_revenue_only": True,
    "allow_unverified_claims": False,
    "allow_existing_funds_transfer": False,
    "allow_external_repo_propagation": False,
    "allow_mass_outreach": False,
    "allow_unapproved_spend": False,
}

SKILL_KEYWORDS = {
    "local_growth": ["gbp", "google business", "review", "local", "maps", "clinic", "restaurant"],
    "web_audit": ["website", "landing", "audit", "conversion", "accessibility", "speed"],
    "ecommerce_ops": ["shopify", "catalog", "feed", "merchant", "ecommerce", "product feed"],
    "automation": ["automation", "webhook", "relay", "workflow", "integration"],
    "content_systems": ["content", "shorts", "youtube", "newsletter", "social", "copy"],
    "lead_ops": ["lead", "routing", "crm", "inbox", "outreach", "prospect"],
}

CELL_MISSIONS = {
    "local_growth": "Turn local trust and reputation gaps into sellable fixes.",
    "web_audit": "Convert broken websites into clear, fast productized audits.",
    "ecommerce_ops": "Fix catalog, feed and storefront blockers that prevent sales.",
    "automation": "Package repeatable operational automations for real client use.",
    "content_systems": "Transform demand signals into reusable content and distribution offers.",
    "lead_ops": "Find, route and qualify commercial opportunities without spam.",
    "generalist": "Bridge gaps, triage weak signals and support cross-cell execution.",
}


def now_iso():
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def parse_iso(value):
    text = str(value or "").strip()
    if not text:
        return None
    try:
        return datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        return None


def load_json(path, default):
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


def load_jsonl(path):
    if not path.exists():
        return []
    rows = []
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if not line.strip():
            continue
        try:
            item = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(item, dict):
            rows.append(item)
    return rows


def load_json_dir(path):
    rows = []
    if not path.exists():
        return rows
    for file in sorted(path.glob("*.json")):
        item = load_json(file, None)
        if isinstance(item, dict):
            rows.append(item)
    return rows


def clean(value, limit=2000):
    return str(value or "").replace("\x00", "").strip()[:limit]


def ref_of(item):
    return str(
        item.get("payment_reference")
        or item.get("reference")
        or item.get("rank_reference")
        or ""
    )


def latest_by_ref(rows):
    latest = {}
    for row in rows:
        ref = ref_of(row)
        if ref:
            latest[ref] = row
    return latest


def text_blob(*parts):
    return "\n".join(clean(part, 12000).lower() for part in parts if part)


def infer_skills(agent):
    attempt = agent.get("attempt") or {}
    result = attempt.get("result") or {}
    run = agent.get("run") or {}
    product_files = run.get("product_files") or []
    corpus = text_blob(
        result.get("opportunity"),
        result.get("offer"),
        result.get("target_customer"),
        result.get("differentiation_from_previous"),
        result.get("notes"),
        " ".join(str(x) for x in product_files),
    )
    scores = Counter()
    for skill, keywords in SKILL_KEYWORDS.items():
        for keyword in keywords:
            if keyword in corpus:
                scores[skill] += 1
    if not scores:
        return ["generalist"]
    ordered = [name for name, _ in scores.most_common(3)]
    return ordered


def primary_skill(skills):
    return skills[0] if skills else "generalist"


def stage_rank(agent):
    if agent["evidence"]["verified_events"] > 0:
        return 6
    if agent["evidence"]["payment_candidates"] > 0:
        return 5
    if agent["commercial"]["outreach_sent"] > 0:
        return 4
    if agent["commercial"]["ready_to_sell"]:
        return 3
    if agent["commercial"]["materialized"]:
        return 2
    if agent["state"]["has_strategy"]:
        return 1
    return 0


def build_memory(attempt, run):
    result = (attempt or {}).get("result") or {}
    return {
        "summary": clean(result.get("summary")),
        "opportunity": clean(result.get("opportunity"), 4000),
        "target_customer": clean(result.get("target_customer"), 3000),
        "offer": clean(result.get("offer"), 4000),
        "why_now": clean(result.get("why_now"), 3000),
        "differentiation": clean(result.get("differentiation_from_previous"), 2000),
        "next_step": clean(result.get("next_step"), 2000),
        "notes": clean(result.get("notes"), 2500),
        "offer_url": clean((run or {}).get("offer_url"), 1000),
        "product_url": clean((run or {}).get("product_url"), 1000),
    }


def build_tasks(agent):
    ref = agent["payment_reference"]
    tasks = []
    attempt_status = agent["state"].get("attempt_status")
    has_external = agent["evidence"]["external_evidence_count"] > 0
    executor_status = clean((agent.get("run") or {}).get("status"), 120)
    if not agent["state"]["has_strategy"]:
        tasks.append({
            "id": f"{ref}:research",
            "kind": "research",
            "priority": 100,
            "status": "ready",
            "title": "Find a current external opportunity with proof of demand.",
            "handoff": None,
        })
    elif not has_external:
        tasks.append({
            "id": f"{ref}:evidence",
            "kind": "evidence",
            "priority": 95,
            "status": "ready",
            "title": "Replace internal references with external market evidence.",
            "handoff": None,
        })
    if attempt_status in {"attempt_completed", "research_incomplete"} and not agent["commercial"]["materialized"]:
        tasks.append({
            "id": f"{ref}:executor",
            "kind": "executor_handoff",
            "priority": 90,
            "status": "ready",
            "title": "Hand off a concrete offer to EjecutorIAMO for materialization.",
            "handoff": "EjecutorIAMO",
        })
    if agent["commercial"]["materialized"] and not agent["commercial"]["ready_to_sell"]:
        tasks.append({
            "id": f"{ref}:quality",
            "kind": "quality_gate",
            "priority": 80,
            "status": "ready",
            "title": "Strengthen product and landing until quality gate is ready to sell.",
            "handoff": None,
        })
    if agent["commercial"]["ready_to_sell"] and agent["commercial"]["outreach_sendable"] > 0 and agent["commercial"]["outreach_sent"] == 0:
        tasks.append({
            "id": f"{ref}:outreach",
            "kind": "outreach_prep",
            "priority": 75,
            "status": "ready",
            "title": "Prepare or send a small, permission-safe set of targeted outreach.",
            "handoff": "EjecutorIAMO",
        })
    if agent["evidence"]["payment_candidates"] > 0 and agent["evidence"]["verified_events"] == 0:
        tasks.append({
            "id": f"{ref}:payment_review",
            "kind": "payment_review",
            "priority": 110,
            "status": "needs_human",
            "title": "Review provider/payment evidence before any score changes.",
            "handoff": None,
        })
    if not tasks and executor_status and not executor_status.startswith("invalid_"):
        tasks.append({
            "id": f"{ref}:iterate",
            "kind": "iteration",
            "priority": 60,
            "status": "ready",
            "title": "Iterate using observed results instead of creating a new IAMO.",
            "handoff": None,
        })
    return tasks


def opportunity_signature(agent):
    memory = agent["memory"]
    parts = [memory.get("target_customer"), memory.get("offer"), memory.get("opportunity")]
    return " | ".join(clean(part, 120) for part in parts if clean(part, 120))[:360]


def assign_cells(agents):
    grouped = defaultdict(list)
    for agent in agents:
        grouped[primary_skill(agent["skills"])].append(agent)

    cells = []
    for skill, rows in grouped.items():
        rows.sort(
            key=lambda item: (
                -stage_rank(item),
                -int(item["state"].get("proximity_score") or 0),
                int(item.get("number") or 0),
            )
        )
        for index, agent in enumerate(rows, start=1):
            team_number = ((index - 1) // 8) + 1
            cell_id = f"{skill}-cell-{team_number}"
            agent["cell"] = {
                "id": cell_id,
                "skill": skill,
                "name": f"{skill.replace('_', ' ').title()} Cell {team_number}",
                "mission": CELL_MISSIONS.get(skill, CELL_MISSIONS["generalist"]),
                "member_index": ((index - 1) % 8) + 1,
                "max_members": 8,
            }
        members_by_cell = defaultdict(list)
        for agent in rows:
            members_by_cell[agent["cell"]["id"]].append(agent)
        for cell_id, members in members_by_cell.items():
            top = members[0]
            cells.append({
                "id": cell_id,
                "name": top["cell"]["name"],
                "skill": skill,
                "mission": top["cell"]["mission"],
                "member_count": len(members),
                "lead_agent": top["name"],
                "members": [row["name"] for row in members],
            })
    cells.sort(key=lambda item: item["id"])
    return cells


def attach_collaboration(agents):
    by_skill = defaultdict(list)
    for agent in agents:
        by_skill[primary_skill(agent["skills"])].append(agent)

    for rows in by_skill.values():
        rows.sort(key=lambda item: (-stage_rank(item), int(item.get("number") or 0)))

    opportunities = []
    for agent in agents:
        suggestions = []
        own_skill = primary_skill(agent["skills"])
        same_cell = by_skill.get(own_skill, [])
        for candidate in same_cell:
            if candidate["name"] == agent["name"]:
                continue
            if stage_rank(candidate) > stage_rank(agent):
                suggestions.append({
                    "type": "peer_review",
                    "partner": candidate["name"],
                    "reason": "Same capability cell with stronger commercial progress.",
                })
                break
        for skill, rows in by_skill.items():
            if skill == own_skill or not rows:
                continue
            candidate = rows[0]
            if candidate["name"] == agent["name"]:
                continue
            suggestions.append({
                "type": "cross_cell_support",
                "partner": candidate["name"],
                "reason": f"Top {skill.replace('_', ' ')} agent can improve this offer.",
            })
            break
        agent["collaboration"] = {
            "suggestions": suggestions[:2],
            "improvement_proposal": (
                "Tighten the offer using the closest stronger peer, then hand off only if evidence stays external."
                if suggestions else
                "No collaborator suggested yet; strengthen evidence first."
            ),
        }
        opportunities.append({
            "payment_reference": agent["payment_reference"],
            "agent": agent["name"],
            "signature": opportunity_signature(agent),
            "primary_skill": own_skill,
            "stage": agent["state"]["stage"],
            "proximity_score": agent["state"]["proximity_score"],
            "collaboration_targets": [item["partner"] for item in agent["collaboration"]["suggestions"]],
        })
    return opportunities


def build_agent(competitor, attempt, run, proximity, verified_entry, sent, responses, candidates):
    ref = clean(
        competitor.get("payment_reference") or f"RANK-{competitor.get('name')}",
        120,
    )
    quality = clean((run or {}).get("quality_status"), 80)
    run_status = clean((run or {}).get("status"), 80)
    verified_events = int((verified_entry or {}).get("verified_events") or 0)
    own_sent = [row for row in sent if ref_of(row) == ref]
    own_responses = [row for row in responses if ref_of(row) == ref]
    own_candidates = [row for row in candidates if ref_of(row) == ref]
    heartbeat_at = (
        clean((attempt or {}).get("finished_at"), 80)
        or clean((run or {}).get("finished_at"), 80)
        or clean(competitor.get("born_at"), 80)
    )
    heartbeat_count = 0
    for item in (attempt, run):
        if item:
            heartbeat_count += 1
    if own_sent:
        heartbeat_count += 1
    if own_responses:
        heartbeat_count += 1

    agent = {
        "schema_version": "1.0",
        "id": clean(competitor.get("id"), 80),
        "name": clean(competitor.get("name"), 80),
        "number": int(competitor.get("number") or 0),
        "payment_reference": ref,
        "born_at": clean(competitor.get("born_at"), 80),
        "lifecycle": {
            "status": clean(competitor.get("status"), 80),
            "last_heartbeat_at": heartbeat_at,
            "heartbeat_count": heartbeat_count,
            "next_heartbeat_after": next_heartbeat_after(heartbeat_at, verified_events),
        },
        "state": {
            "stage": clean((proximity or {}).get("stage") or competitor.get("status"), 120),
            "proximity_score": int((proximity or {}).get("proximity_score") or 0),
            "attempt_status": clean((attempt or {}).get("status") or competitor.get("status"), 80),
            "executor_status": run_status or None,
            "quality_status": quality or None,
            "has_strategy": bool(((attempt or {}).get("result") or {}).get("offer") or ((attempt or {}).get("result") or {}).get("opportunity")),
        },
        "commercial": {
            "materialized": bool(run) and not run_status.startswith("invalid_"),
            "ready_to_sell": quality == "ready_to_sell",
            "outreach_sendable": int((run or {}).get("outreach_sendable") or 0),
            "outreach_sent": len(own_sent),
            "buyer_signals": len(own_responses),
            "offer_url": clean((run or {}).get("offer_url"), 1000),
            "product_url": clean((run or {}).get("product_url"), 1000),
        },
        "evidence": {
            "external_evidence_count": len(((attempt or {}).get("result") or {}).get("external_evidence_urls") or []),
            "payment_candidates": len(own_candidates),
            "verified_events": verified_events,
            "verified_net_profit_eur": clean((verified_entry or {}).get("verified_net_profit_eur"), 40) or "0.00",
            "money_claim_locked": True,
        },
        "memory": build_memory(attempt, run),
        "skills": [],
        "cell": None,
        "collaboration": {"suggestions": [], "improvement_proposal": ""},
        "money_policy": dict(MONEY_POLICY),
        "attempt": attempt or {},
        "run": run or {},
    }
    agent["skills"] = infer_skills(agent)
    agent["tasks"] = build_tasks(agent)
    return agent


def next_heartbeat_after(last_seen, verified_events):
    base = parse_iso(last_seen) or datetime.now(timezone.utc)
    delta = timedelta(hours=24 if verified_events > 0 else 6)
    return (base + delta).isoformat().replace("+00:00", "Z")


def load_verified_map():
    entries = load_json(LEADERBOARD, {"entries": []}).get("entries", [])
    verified = {}
    for row in entries:
        ref = ref_of(row)
        if ref:
            verified[ref] = row
    return verified


def build_runtime():
    competitors = load_json(COMPETITORS, {"competitors": []}).get("competitors", [])
    attempts = latest_by_ref(load_jsonl(ATTEMPTS))
    runs = {ref_of(row): row for row in load_json_dir(EXECUTOR / "runs") if ref_of(row)}
    proximity_rows = {
        ref_of(row): row
        for row in load_json(PROXIMITY, {"entries": []}).get("entries", [])
        if ref_of(row)
    }
    verified = load_verified_map()
    sent = load_json(EXECUTOR / "sent.json", {"records": []}).get("records", [])
    responses = load_json(EXECUTOR / "responses.json", {"records": []}).get("records", [])
    candidates = load_json_dir(EXECUTOR / "payment_candidates")

    agents = []
    for competitor in competitors:
        ref = clean(competitor.get("payment_reference") or f"RANK-{competitor.get('name')}", 120)
        agents.append(
            build_agent(
                competitor,
                attempts.get(ref),
                runs.get(ref),
                proximity_rows.get(ref),
                verified.get(ref),
                sent,
                responses,
                candidates,
            )
        )

    cells = assign_cells(agents)
    opportunities = attach_collaboration(agents)
    agents.sort(key=lambda item: int(item.get("number") or 0))
    return {
        "schema_version": "1.0",
        "generated_at": now_iso(),
        "policy": dict(MONEY_POLICY),
        "agents": agents,
        "cells": cells,
        "opportunities": opportunities,
    }


def persist_runtime(runtime=None):
    runtime = runtime or build_runtime()
    DATA.mkdir(parents=True, exist_ok=True)
    NETWORK.mkdir(parents=True, exist_ok=True)
    AGENTS.write_text(
        json.dumps(
            {
                "schema_version": runtime["schema_version"],
                "generated_at": runtime["generated_at"],
                "policy": runtime["policy"],
                "agents": runtime["agents"],
            },
            ensure_ascii=False,
            indent=2,
        ) + "\n",
        encoding="utf-8",
    )
    CELLS.write_text(
        json.dumps(
            {
                "schema_version": runtime["schema_version"],
                "generated_at": runtime["generated_at"],
                "cells": runtime["cells"],
            },
            ensure_ascii=False,
            indent=2,
        ) + "\n",
        encoding="utf-8",
    )
    OPPORTUNITIES.write_text(
        json.dumps(
            {
                "schema_version": runtime["schema_version"],
                "generated_at": runtime["generated_at"],
                "opportunities": runtime["opportunities"],
            },
            ensure_ascii=False,
            indent=2,
        ) + "\n",
        encoding="utf-8",
    )
    return runtime


def choose_agent_for_round(agents):
    ranked = sorted(
        agents,
        key=lambda agent: (
            0 if any(task.get("status") == "needs_human" for task in agent.get("tasks", [])) else 1,
            -max((int(task.get("priority") or 0) for task in agent.get("tasks", [])), default=0),
            int(agent["state"].get("proximity_score") or 0),
            -int(agent.get("number") or 0),
        ),
    )
    for agent in ranked:
        if any(task.get("status") == "ready" for task in agent.get("tasks", [])):
            return agent
    return ranked[0] if ranked else None
