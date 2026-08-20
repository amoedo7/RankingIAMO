#!/usr/bin/env python3

import json
import os
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COMPETITORS = ROOT / "data" / "competitors.json"
NORMAL_MIN_GAP_SECONDS = 9 * 60
WATCHDOG_STALE_SECONDS = 20 * 60


def parse_iso(value):
    if not value:
        return None
    value = str(value).replace("Z", "+00:00")
    try:
        dt = datetime.fromisoformat(value)
    except ValueError:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def latest_birth():
    if not COMPETITORS.exists():
        return None
    try:
        data = json.loads(COMPETITORS.read_text(encoding="utf-8"))
    except Exception:
        return None
    births = [
        parse_iso(item.get("born_at"))
        for item in data.get("competitors", [])
        if isinstance(item, dict)
    ]
    births = [dt for dt in births if dt is not None]
    return max(births) if births else None


def emit(key, value):
    output = os.environ.get("GITHUB_OUTPUT")
    if output:
        with open(output, "a", encoding="utf-8") as fh:
            fh.write(f"{key}={value}\n")


def main():
    event_name = os.environ.get("GITHUB_EVENT_NAME", "manual")
    trigger_source = os.environ.get("IAMO_TRIGGER_SOURCE", "")
    last = latest_birth()
    now = datetime.now(timezone.utc)

    if last is None:
        should_spawn = True
        age_seconds = -1
        reason = "no previous competitor"
    else:
        age_seconds = max(0, int((now - last).total_seconds()))

        if event_name == "push":
            # A workflow-file change is an intentional one-time bootstrap.
            threshold = 0
        elif event_name == "schedule":
            # Scheduled cron is only a recovery watchdog.
            threshold = WATCHDOG_STALE_SECONDS
        else:
            # Normal self-chain/manual runs must not create near-duplicates.
            threshold = NORMAL_MIN_GAP_SECONDS

        should_spawn = age_seconds >= threshold
        if should_spawn:
            reason = (
                "workflow bootstrap" if event_name == "push"
                else f"last competitor is {age_seconds}s old"
            )
        else:
            reason = f"too early: last competitor is only {age_seconds}s old (< {threshold}s)"

    emit("should_spawn", "true" if should_spawn else "false")
    emit("last_age_seconds", str(age_seconds))
    emit("reason", reason.replace("\n", " "))

    print(
        f"event={event_name} source={trigger_source or '-'} "
        f"should_spawn={should_spawn} age={age_seconds}s reason={reason}"
    )


if __name__ == "__main__":
    main()
