from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import runner
import runtime


class RunnerTests(unittest.TestCase):
    def test_rotating_choice_prefers_less_used_agent(self):
        a = runtime.normalize_agent({"id": "iamo1", "name": "IAMO1", "number": 1})
        b = runtime.normalize_agent({"id": "iamo2", "name": "IAMO2", "number": 2})
        a["role"] = b["role"] = "scout"
        a["traits"]["exploration"] = 1.0
        b["traits"]["exploration"] = 0.2
        a["reputation"]["cycles"] = 5
        b["reputation"]["cycles"] = 0
        chosen = runner.rotating_choice([a, b], "scout", set())
        self.assertEqual(chosen["id"], "iamo2")

    def test_append_unseen_tasks_does_not_duplicate_titles(self):
        queue = [{"id": "x", "title": "Known", "status": "blocked"}]
        with patch.object(runtime, "route_catalog", return_value=[{"name": "Known"}, {"name": "Fresh"}]), patch.object(runtime, "read_json", return_value={}):
            added = runner.append_unseen_tasks(queue, "2026-09-04T00:00:00Z", limit=9)
        self.assertEqual(added, 1)
        self.assertEqual(queue[-1]["title"], "Fresh")
        self.assertEqual(queue[-1]["verified_net_profit_eur"], "0.00")

    def test_task_id_is_stable_for_new_title(self):
        a = runner.task_id("Example", [])
        b = runner.task_id("Example", [])
        self.assertEqual(a, b)
        self.assertTrue(a.startswith("task-"))


if __name__ == "__main__":
    unittest.main()
