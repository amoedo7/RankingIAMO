from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

import brain
import identity
import world


class BrainWorldTests(unittest.TestCase):
    def agent(self, n: int, role: str = "scout", *, agent_id: str | None = None, birthplace: str = "github:amoedo7/RankingIAMO"):
        agent = {
            "id": agent_id or f"iamo{n}", "name": f"IAMO{n}", "number": n, "role": role,
            "state": "idle", "life": {"directive": "continue_with_evidence"},
            "reputation": {}, "memory": {}, "heartbeat_at": "2026-09-04T00:00:00Z",
        }
        identity.ensure_identity(
            agent,
            row={"name": f"IAMO{n}", "born_at": "2026-09-04T00:00:00Z", "birthplace": birthplace},
        )
        return agent

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
            self.assertEqual(snapshot["schema"], "iamox.world.snapshot.v2")
            self.assertTrue((root / "reports" / "agents" / "IAMO7.json").exists())
            self.assertTrue((root / "reports" / "agents" / "IAMO318.json").exists())
            self.assertNotEqual(snapshot["agents"][0]["brain"]["signature"], snapshot["agents"][1]["brain"]["signature"])
            self.assertTrue(snapshot["agents"][0]["identity"]["birth_uid"])
            self.assertEqual(snapshot["agents"][0]["encounter_name"], "IAMO7")

    def test_same_display_name_uses_alias_and_distinct_report_files(self):
        a = self.agent(7, agent_id="iamo7", birthplace="github:amoedo7/RankingIAMO")
        b = self.agent(7, agent_id="iamo7-dk", birthplace="host:damo:denmark")
        identity.assign_encounter_aliases([a, b])
        self.assertNotEqual(a["identity"]["encounter_alias"], b["identity"]["encounter_alias"])
        self.assertNotEqual(world.report_filename(a), world.report_filename(b))
        self.assertTrue(world.report_filename(a).startswith("IAMO7-"))
        self.assertTrue(world.report_filename(b).startswith("IAMO7-"))
        self.assertNotEqual(world.identity_key(a), world.identity_key(b))
        public_a = world.public_agent(a, None)
        public_b = world.public_agent(b, None)
        self.assertEqual(public_a["identity"]["display_name"], "IAMO7")
        self.assertEqual(public_b["identity"]["display_name"], "IAMO7")
        self.assertNotEqual(public_a["encounter_name"], public_b["encounter_name"])


if __name__ == "__main__":
    unittest.main()
