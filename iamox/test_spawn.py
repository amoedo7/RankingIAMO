from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import spawn


class SpawnTests(unittest.TestCase):
    def test_next_number_uses_highest_identity(self):
        rows = [{"number": 7}, {"number": 985}, {"competitor_number": 12}]
        self.assertEqual(spawn.next_number(rows), 986)

    def test_birth_contains_individual_runtime_marker(self):
        row = spawn.birth(986, "2026-09-04T15:00:00Z")
        self.assertEqual(row["id"], "iamo986")
        self.assertEqual(row["payment_reference"], "RANK-IAMO986")
        self.assertEqual(row["runtime_generation"], "0.3.0-individual")
        self.assertEqual(row["creator"], "AMO")

    def test_spawn_appends_without_rewriting_existing_identities(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "competitors.json"
            original = {"schema_version": "1.0", "competitors": [{"id": "iamo1", "name": "IAMO1", "number": 1}]}
            path.write_text(json.dumps(original), encoding="utf-8")
            with patch.object(spawn, "COMPETITORS", path):
                made = spawn.spawn(2)
            saved = json.loads(path.read_text(encoding="utf-8"))["competitors"]
        self.assertEqual([x["name"] for x in made], ["IAMO2", "IAMO3"])
        self.assertEqual(saved[0]["id"], "iamo1")
        self.assertEqual(len({x["id"] for x in saved}), 3)


if __name__ == "__main__":
    unittest.main()
