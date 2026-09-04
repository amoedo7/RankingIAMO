from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

import brain
import world


class BrainWorldTests(unittest.TestCase):
    def agent(self, n: int, role: str = "scout"):
        return {
            "id": f"iamo{n}", "name": f"IAMO{n}", "number": n, "role": role,
            "state": "idle", "life": {"directive": "continue_with_evidence"},
            "reputation": {}, "memory": {}, "heartbeat_at": "2026-09-04T00:00:00Z",
        }

    def test_each_iamo_has_distinct_individual_brain(self):
        a = self.agent(7)
        b = self.agent(318)
        brain.ensure_brain(a, "2026-09-04T00:00:00Z")
        brain.ensure_brain(b, "2026-09-04T00:00:00Z")
        self.assertNotEqual(a["brain"]["signature"], b["brain"]["signature"])
        self.assertNotEqual(a["brain"]["seed"], b["brain"]["seed"])
        self.assertFalse(brain.pulse_brains([a, b], [], "2026-09-04T00:01:00Z")["shared_brain"])
        self.assertEqual(a["brain"]["affiliation"]["origin"], "DesarrollAMO")

    def test_spawn_is_stable_and_agents_are_distinct(self):
        a1 = world.spawn("iamo7", "forest")
        a2 = world.spawn("iamo7", "forest")
        b = world.spawn("iamo318", "forest")
        self.assertEqual(a1, a2)
        self.assertNotEqual(a1, b)

    def test_world_pulse_generates_snapshot_and_individual_reports(self):
        agents = [self.agent(7, "builder"), self.agent(318, "seller")]
        at = "2026-09-04T00:00:00Z"
        brain.pulse_brains(agents, [], at)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            result = world.pulse_world(
                agents, [], at,
                snapshot_path=root / "world" / "snapshot.json",
                report_dir=root / "reports",
            )
            self.assertEqual(result["agents_on_map"], 2)
            snapshot = json.loads((root / "world" / "snapshot.json").read_text(encoding="utf-8"))
            self.assertEqual(snapshot["agent_count"], 2)
            self.assertTrue((root / "reports" / "agents" / "IAMO7.json").exists())
            self.assertTrue((root / "reports" / "agents" / "IAMO318.json").exists())
            self.assertNotEqual(snapshot["agents"][0]["brain"]["signature"], snapshot["agents"][1]["brain"]["signature"])


if __name__ == "__main__":
    unittest.main()
