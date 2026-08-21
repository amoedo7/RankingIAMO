import importlib.util
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PLAYBOOK = ROOT / "data" / "monetization_playbook.json"
PREPARE = ROOT / "scripts" / "prepare_iamo.py"

spec = importlib.util.spec_from_file_location("prepare_iamo", PREPARE)
prepare_iamo = importlib.util.module_from_spec(spec)
spec.loader.exec_module(prepare_iamo)


class MonetizationPlaybookTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = json.loads(PLAYBOOK.read_text(encoding="utf-8"))
        cls.routes = cls.data["routes"]

    def test_exactly_100_unique_routes(self):
        self.assertEqual(len(self.routes), 100)
        ids = [int(route["id"]) for route in self.routes]
        self.assertEqual(sorted(ids), list(range(1, 101)))
        self.assertEqual(len(set(ids)), 100)

    def test_every_route_is_actionable(self):
        for route in self.routes:
            self.assertTrue(str(route.get("category", "")).strip())
            self.assertTrue(str(route.get("title", "")).strip())
            self.assertTrue(str(route.get("first_test", "")).strip())
            self.assertIsInstance(route.get("channels"), list)

    def test_each_iamo_receives_five_distinct_seeds(self):
        for number in range(1, 21):
            seeds = prepare_iamo.select_playbook_seeds(self.routes, number)
            self.assertEqual(len(seeds), 5)
            self.assertEqual(len({int(seed["id"]) for seed in seeds}), 5)

    def test_twenty_consecutive_iamo_cover_all_100(self):
        seen = []
        for number in range(1, 21):
            seeds = prepare_iamo.select_playbook_seeds(self.routes, number)
            seen.extend(int(seed["id"]) for seed in seeds)
        self.assertEqual(sorted(seen), list(range(1, 101)))

    def test_seed_groups_are_cross_playbook_not_adjacent(self):
        seeds = prepare_iamo.select_playbook_seeds(self.routes, 1)
        self.assertEqual([int(seed["id"]) for seed in seeds], [1, 21, 41, 61, 81])
        seeds = prepare_iamo.select_playbook_seeds(self.routes, 20)
        self.assertEqual([int(seed["id"]) for seed in seeds], [20, 40, 60, 80, 100])


if __name__ == "__main__":
    unittest.main()
