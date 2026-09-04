from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import identity
import spawn


class SpawnTests(unittest.TestCase):
    def test_next_number_uses_highest_identity(self):
        rows = [{"number": 7}, {"number": 985}, {"competitor_number": 12}]
        self.assertEqual(spawn.next_number(rows), 986)

    def test_birth_contains_stem_runtime_and_universal_identity(self):
        row = spawn.birth(986, "2026-09-04T15:00:00Z")
        self.assertEqual(row["id"], "iamo986")
        self.assertEqual(row["payment_reference"], "RANK-IAMO986")
        self.assertEqual(row["runtime_generation"], "0.5.0-stem")
        self.assertEqual(row["creator"], "AMO")
        self.assertTrue(row["birth_uid"].startswith("iamo:iamo1:"))
        self.assertEqual(row["lineage_generation"], 1)

    def test_parent_is_recorded_in_child(self):
        parent = {"identity": {"birth_uid": "iamo:iamo1:host:parent", "generation": 3}}
        row = spawn.birth(1000, "2026-09-04T15:00:00Z", parent=parent, birthplace="host:damo")
        self.assertEqual(row["parent_birth_uid"], "iamo:iamo1:host:parent")
        self.assertEqual(row["lineage_generation"], 4)
        self.assertEqual(row["birthplace"], "host:damo")

    def test_spawn_appends_without_rewriting_existing_identities(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "competitors.json"
            original = {"schema_version": "1.0", "competitors": [{"id": "iamo1", "name": "IAMO1", "number": 1}]}
            path.write_text(json.dumps(original), encoding="utf-8")
            with patch.object(spawn, "COMPETITORS", path):
                made = spawn.spawn(2, birthplace="host:test")
            saved = json.loads(path.read_text(encoding="utf-8"))["competitors"]
        self.assertEqual([x["name"] for x in made], ["IAMO2", "IAMO3"])
        self.assertEqual(saved[0]["id"], "iamo1")
        self.assertEqual(len({x["id"] for x in saved}), 3)
        self.assertEqual(len({x["birth_uid"] for x in made}), 2)


if __name__ == "__main__":
    unittest.main()
