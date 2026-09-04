#!/usr/bin/env python3

import json

from iamo_runtime import choose_agent_for_round, persist_runtime


def main():
    runtime = persist_runtime()
    selected = choose_agent_for_round(runtime.get("agents", []))
    summary = {
        "agents": len(runtime.get("agents", [])),
        "cells": len(runtime.get("cells", [])),
        "opportunities": len(runtime.get("opportunities", [])),
        "selected_agent": (selected or {}).get("name"),
    }
    print(json.dumps(summary, ensure_ascii=False))


if __name__ == "__main__":
    main()
