import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import iamo_runtime as runtime


class IAMORuntimeTests(unittest.TestCase):
    def base_agent(self, **overrides):
        agent = {
            "id": "iamo9",
            "name": "IAMO9",
            "number": 9,
            "payment_reference": "RANK-IAMO9",
            "lifecycle": {"status": "attempt_completed"},
            "state": {
                "stage": "LISTO PARA VENDER",
                "proximity_score": 65,
                "attempt_status": "attempt_completed",
                "executor_status": None,
                "quality_status": None,
                "has_strategy": True,
            },
            "commercial": {
                "materialized": False,
                "ready_to_sell": False,
                "outreach_sendable": 0,
                "outreach_sent": 0,
                "buyer_signals": 0,
                "offer_url": "",
                "product_url": "",
            },
            "evidence": {
                "external_evidence_count": 1,
                "payment_candidates": 0,
                "verified_events": 0,
                "verified_net_profit_eur": "0.00",
                "money_claim_locked": True,
            },
            "memory": {
                "target_customer": "Local clinic",
                "offer": "Website fix sprint",
                "opportunity": "Slow conversion site",
            },
            "skills": ["web_audit"],
            "tasks": [],
            "cell": None,
            "collaboration": {"suggestions": [], "improvement_proposal": ""},
            "attempt": {},
            "run": {},
        }
        for key, value in overrides.items():
            agent[key] = value
        return agent

    def test_infer_skills_from_attempt_and_product_files(self):
        agent = {
            "attempt": {
                "result": {
                    "opportunity": "Shopify catalog feed errors and conversion loss",
                    "offer": "Automated feed cleanup and webhook relay",
                }
            },
            "run": {"product_files": ["catalog_feed_audit.py", "docs/setup.md"]},
        }
        skills = runtime.infer_skills(agent)
        self.assertIn("ecommerce_ops", skills)
        self.assertIn("automation", skills)

    def test_build_tasks_requests_executor_handoff(self):
        agent = self.base_agent()
        tasks = runtime.build_tasks(agent)
        kinds = [task["kind"] for task in tasks]
        self.assertIn("executor_handoff", kinds)

    def test_build_tasks_blocks_on_payment_review(self):
        agent = self.base_agent(
            evidence={
                "external_evidence_count": 1,
                "payment_candidates": 1,
                "verified_events": 0,
                "verified_net_profit_eur": "0.00",
                "money_claim_locked": True,
            }
        )
        tasks = runtime.build_tasks(agent)
        review = next(task for task in tasks if task["kind"] == "payment_review")
        self.assertEqual(review["status"], "needs_human")

    def test_choose_agent_for_round_prefers_ready_high_priority(self):
        low = self.base_agent(name="IAMO10", number=10)
        low["tasks"] = [{"kind": "iteration", "priority": 10, "status": "ready"}]
        high = self.base_agent(name="IAMO11", number=11)
        high["tasks"] = [{"kind": "payment_review", "priority": 110, "status": "needs_human"}]
        chosen = runtime.choose_agent_for_round([low, high])
        self.assertEqual(chosen["name"], "IAMO10")

    def test_assign_cells_chunks_members_in_groups_of_eight(self):
        agents = []
        for i in range(1, 10):
            agent = self.base_agent(name=f"IAMO{i}", number=i)
            agent["skills"] = ["web_audit"]
            agents.append(agent)
        cells = runtime.assign_cells(agents)
        ids = {agent["cell"]["id"] for agent in agents}
        self.assertIn("web_audit-cell-1", ids)
        self.assertIn("web_audit-cell-2", ids)
        self.assertEqual(len(cells), 2)


if __name__ == "__main__":
    unittest.main()
