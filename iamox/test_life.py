from __future__ import annotations

import unittest

import life


class LifeTests(unittest.TestCase):
    def test_fibonacci_budget_grows(self):
        self.assertEqual([life.fibonacci(i) for i in range(8)], [1, 1, 2, 3, 5, 8, 13, 21])

    def test_near_duplicate_proposals_are_detected(self):
        first = "Probar una ruta local alternativa y reversible"
        second = "Elegir una ruta alternativa reversible para la seguridad"
        self.assertGreaterEqual(life.semantic_similarity(first, second), life.SIMILARITY_THRESHOLD)

    def test_every_agent_inherits_creator_and_safe_scope(self):
        agent = {"id": "iamo985"}
        state = life.ensure_life(agent, "2026-09-04T14:00:00Z")
        self.assertEqual(state["creator"]["github"], "amoedo7")
        self.assertEqual(state["lineage"]["prototype"], "IAMO1 v0.3.0")
        self.assertFalse(state["scope"]["self_propagation"])
        self.assertEqual(state["genome_version"], life.GENOME_VERSION)

    def test_repetition_escalates_and_progress_resets(self):
        agent = {"id": "iamo1"}
        at = "2026-09-04T14:00:00Z"
        focus = "Probar una ruta local alternativa y reversible"
        life.observe(agent, focus, at, progress_marker="task-1|research|review|0|0|")
        for _ in range(3):
            life.observe(agent, focus, at, progress_marker="task-1|research|review|0|0|")
        self.assertGreaterEqual(agent["life"]["stagnation"], 3)
        self.assertEqual(agent["life"]["directive"], "request_peer_counterexample")
        self.assertGreater(agent["life"]["fibonacci_budget"], 1)

        life.observe(agent, focus, at, progress_marker="task-1|offer|open|1|0|")
        self.assertEqual(agent["life"]["stagnation"], 0)
        self.assertEqual(agent["life"]["directive"], "continue_with_evidence")

    def test_population_heartbeat_assigns_seed_action(self):
        agents = [{"id": "iamo1", "task_id": "task-1"}, {"id": "iamo2", "task_id": None}]
        queue = [{
            "id": "task-1",
            "title": "Paid code review package",
            "gate": "research",
            "status": "review",
            "evidence": [],
            "artifacts": [],
        }]
        summary = life.heartbeat_population(agents, queue, "2026-09-04T14:00:00Z")
        self.assertEqual(summary["living_agents"], 2)
        self.assertEqual(agents[0]["life"]["next_action"], "seek_external_evidence")
        self.assertEqual(agents[1]["life"]["next_action"], "observe_and_learn")


if __name__ == "__main__":
    unittest.main()
