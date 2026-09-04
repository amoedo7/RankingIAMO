from __future__ import annotations

import unittest

import identity


class IdentityTests(unittest.TestCase):
    def test_independent_same_name_births_do_not_collide(self):
        a = {"id": "iamo7", "name": "IAMO7"}
        b = {"id": "iamo7-dk", "name": "IAMO7"}
        identity.ensure_identity(a, row={"name": "IAMO7", "born_at": "2026-09-04T10:00:00Z", "birthplace": "github:amoedo7/RankingIAMO"})
        identity.ensure_identity(b, row={"name": "IAMO7", "born_at": "2026-09-04T10:00:00Z", "birthplace": "host:damo:denmark"})
        self.assertNotEqual(a["identity"]["birth_uid"], b["identity"]["birth_uid"])
        collisions = identity.assign_encounter_aliases([a, b])
        self.assertEqual(collisions, 2)
        self.assertNotEqual(a["identity"]["encounter_alias"], b["identity"]["encounter_alias"])
        self.assertTrue(a["identity"]["encounter_alias"].startswith("IAMO7·"))

    def test_migration_preserves_birth_uid(self):
        agent = {"id": "iamo7", "name": "IAMO7"}
        first = identity.ensure_identity(agent, row={"born_at": "2026-09-04T10:00:00Z", "birthplace": "host:damo"})["birth_uid"]
        second = identity.ensure_identity(agent, row={"name": "IAMO7"}, birthplace="host:new-place")["birth_uid"]
        self.assertEqual(first, second)

    def test_parent_changes_descendant_identity(self):
        a = identity.birth_uid("IAMO8", "2026-09-04T11:00:00Z", "host:damo", "parent-a")
        b = identity.birth_uid("IAMO8", "2026-09-04T11:00:00Z", "host:damo", "parent-b")
        self.assertNotEqual(a, b)


if __name__ == "__main__":
    unittest.main()
