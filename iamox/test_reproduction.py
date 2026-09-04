from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import identity
import reproduction
import spawn


def parent(age: int = 1) -> dict:
    agent = {
        "id": "iamo1",
        "name": "IAMO1",
        "number": 1,
        "life": {"age_rounds": age, "reproduction": {}},
    }
    identity.ensure_identity(
        agent,
        row={"name": "IAMO1", "born_at": "2026-09-04T10:00:00Z", "birthplace": "github:amoedo7/RankingIAMO"},
    )
    return agent


class ReproductionTests(unittest.TestCase):
    def test_maturity_follows_fibonacci_without_duplicate_one(self):
        self.assertEqual([reproduction.maturity(i) for i in range(7)], [1, 2, 3, 5, 8, 13, 21])

    def test_registered_child_repairs_lost_parent_maturity(self):
        p = parent(age=1)
        child = {
            "name": "IAMO986",
            "birth_uid": "iamo:child:986",
            "born_at": "2026-09-04T16:47:42Z",
            "parent_birth_uid": p["identity"]["birth_uid"],
        }
        repaired = reproduction.reconcile_registered_children([p], [child])
        state = p["life"]["reproduction"]
        self.assertEqual(repaired, 1)
        self.assertEqual(state["births"], 1)
        self.assertEqual(state["maturity_index"], 1)
        self.assertEqual(state["next_maturity_age"], 2)
        self.assertEqual(state["last_child_birth_uid"], "iamo:child:986")
        self.assertFalse(reproduction.is_eligible(p))

    def test_founder_generation_zero_has_priority_when_eligible(self):
        root = parent(age=2)
        child = {
            "id": "iamo2",
            "name": "IAMO2",
            "number": 2,
            "life": {"age_rounds": 2, "reproduction": {}},
        }
        identity.ensure_identity(
            child,
            row={
                "name": "IAMO2",
                "born_at": "2026-09-04T10:01:00Z",
                "birthplace": "github:amoedo7/RankingIAMO",
                "lineage_generation": 1,
                "parent_birth_uid": root["identity"]["birth_uid"],
            },
        )
        self.assertEqual(root["identity"]["generation"], 0)
        self.assertIs(reproduction.choose_parent([child, root]), root)

    def test_birth_is_driven_by_parent_maturity(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            competitors = root / "competitors.json"
            competitors.write_text(json.dumps({"competitors": [{"id": "iamo1", "name": "IAMO1", "number": 1}]}), encoding="utf-8")
            migration = root / "migration_seed.json"
            p = parent(age=1)
            env = {
                "IAMOX_REPRODUCTION_ENABLED": "1",
                "IAMOX_BIRTHS_PER_PULSE": "1",
                "IAMOX_REGISTRY_CAPACITY": "3",
                "IAMOX_BIRTHPLACE": "host:test",
            }
            with patch.object(spawn, "COMPETITORS", competitors), patch.object(reproduction, "MIGRATION_SEED", migration), patch.dict("os.environ", env, clear=False):
                result = reproduction.reproduce([p], "2026-09-04T10:10:00Z")
            saved = json.loads(competitors.read_text(encoding="utf-8"))["competitors"]
        self.assertEqual(len(result["births"]), 1)
        self.assertEqual(len(saved), 2)
        self.assertEqual(saved[-1]["parent_birth_uid"], p["identity"]["birth_uid"])
        self.assertEqual(saved[-1]["lineage_generation"], 1)
        self.assertEqual(p["life"]["reproduction"]["births"], 1)
        self.assertEqual(p["life"]["reproduction"]["next_maturity_age"], 2)

    def test_parent_waits_for_next_maturity_after_birth(self):
        p = parent(age=1)
        state = reproduction.ensure_reproduction(p)
        reproduction.mark_birth(p, {"birth_uid": "child"}, "2026-09-04T10:10:00Z")
        self.assertEqual(state["next_maturity_age"], 2)
        self.assertFalse(reproduction.is_eligible(p))
        p["life"]["age_rounds"] = 2
        self.assertTrue(reproduction.is_eligible(p))

    def test_full_host_emits_seed_instead_of_forcing_birth(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            competitors = root / "competitors.json"
            competitors.write_text(json.dumps({"competitors": [{"id": "iamo1", "name": "IAMO1", "number": 1}]}), encoding="utf-8")
            migration = root / "migration_seed.json"
            p = parent(age=1)
            env = {
                "IAMOX_REPRODUCTION_ENABLED": "1",
                "IAMOX_BIRTHS_PER_PULSE": "1",
                "IAMOX_REGISTRY_CAPACITY": "1",
            }
            with patch.object(spawn, "COMPETITORS", competitors), patch.object(reproduction, "MIGRATION_SEED", migration), patch.dict("os.environ", env, clear=False):
                result = reproduction.reproduce([p], "2026-09-04T10:10:00Z")
            seed = json.loads(migration.read_text(encoding="utf-8"))
        self.assertEqual(result["births"], [])
        self.assertTrue(result["host_full"])
        self.assertEqual(seed["reason"], "authorized_host_capacity_reached")
        self.assertEqual(seed["parent_birth_uid"], p["identity"]["birth_uid"])


if __name__ == "__main__":
    unittest.main()
