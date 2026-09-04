#!/usr/bin/env bash
set -euo pipefail

python - <<'PY'
import json
from pathlib import Path

contract = json.loads(Path('.amo').read_text(encoding='utf-8'))
assert contract.get('schema') == 'desarrollamo.amo.v1'
assert contract.get('id') == 'rankingiamo'
checks = contract.get('health', {}).get('checks', [])
assert checks, 'RankingIAMO contract must declare at least one health check'
assert checks[0].get('command') == 'bash scripts/autocheck.sh'
assert contract.get('policy', {}).get('self_declared_pass_allowed') is False
print('RANKINGIAMO_CONTRACT_OK')
PY

python -m unittest discover -s tests -v
python scripts/rebuild_runtime.py
python scripts/rebuild_proximity.py
python scripts/rebuild_ranking.py --check
