from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import runtime


class RuntimeTests(unittest.TestCase):
    def test_stable_role_is_deterministic(self):
        self.assertEqual(runtime.stable_role("iamo1"), runtime.stable_role("iamo1"))
        self.assertIn(runtime.stable_role("iamo1"), runtime.ROLES)

    def test_agent_normalization_preserves_identity(self):
        row = {"competitor_id": "iamo7", "competitor_name": "IAMO7", "competitor_number": 7}
        agent = runtime.normalize_agent(row)
        self.assertEqual(agent["id"], "iamo7")
        self.assertEqual(agent["payment_reference"], "RANK-IAMO7")
        self.assertEqual(agent["state"], "idle")
        self.assertIn(agent["role"], runtime.ROLES)

    def test_money_is_not_invented_by_runtime(self):
        row = {"competitor_id": "iamo8", "competitor_name": "IAMO8", "competitor_number": 8}
        agent = runtime.normalize_agent(row)
        self.assertNotIn("verified_net_profit_eur", agent)

    def test_form_cells_uses_unique_agents(self):
        agents = [runtime.normalize_agent({"competitor_id": f"iamo{i}", "competitor_name": f"IAMO{i}", "competitor_number": i}) for i in range(1, 16)]
        queue = [{"id": "task-001", "title": "x", "gate": "research", "status": "open", "updated_at": runtime.now(), "peer_reviews": []}, {"id": "task-002", "title": "y", "gate": "research", "status": "open", "updated_at": runtime.now(), "peer_reviews": []}]
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            with patch.object(runtime, "AGENTS", root / "agents.json"), patch.object(runtime, "QUEUE", root / "queue.json"), patch.object(runtime, "CELLS_FILE", root / "cells.json"):
                cells = runtime.form_cells(agents, queue, max_cells=2)
        ids = [m["agent_id"] for c in cells for m in c["members"]]
        self.assertEqual(len(ids), len(set(ids)))

    def test_peer_review_gate_does_not_fake_evidence(self):
        agents = [runtime.normalize_agent({"competitor_id": f"iamo{i}", "competitor_name": f"IAMO{i}", "competitor_number": i}) for i in range(1, 8)]
        queue = [{"id": "task-001", "title": "x", "gate": "research", "status": "open", "updated_at": runtime.now(), "peer_reviews": [], "evidence": [], "artifacts": [], "verified_net_profit_eur": "0.00"}]
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            with patch.object(runtime, "AGENTS", root / "agents.json"), patch.object(runtime, "QUEUE", root / "queue.json"), patch.object(runtime, "CELLS_FILE", root / "cells.json"):
                cells = runtime.form_cells(agents, queue, max_cells=1)
                runtime.advance_simulation(agents, queue, cells)
        self.assertEqual(queue[0]["evidence"], [])
        self.assertEqual(queue[0]["verified_net_profit_eur"], "0.00")
        self.assertEqual(queue[0]["status"], "review")


if __name__ == "__main__":
    unittest.main()
