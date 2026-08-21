import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("rebuild_proximity", ROOT / "scripts" / "rebuild_proximity.py")
MOD = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MOD)


class ProximityScoreTests(unittest.TestCase):
    def competitor(self):
        return {"id": "iamo9", "name": "IAMO9", "number": 9, "payment_reference": "RANK-IAMO9", "status": "attempt_completed"}

    def valid_attempt(self):
        return {
            "payment_reference": "RANK-IAMO9",
            "status": "attempt_completed",
            "result": {
                "opportunity": "real problem",
                "offer": "fixed service",
                "external_evidence_urls": ["https://example.com/demand"],
                "execution_packet": {"channel": "email", "message": "hello", "deliverable": "audit"},
            },
        }

    def score(self, attempt=None, run=None, sent=None, responses=None, candidates=None, verified=None):
        return MOD.score_one(
            self.competitor(),
            attempt,
            run,
            sent or [],
            responses or [],
            candidates or [],
            verified or {},
        )

    def test_invalid_empty_competitor_stays_zero(self):
        row = self.score({"status": "invalid_agent_output", "result": {}})
        self.assertEqual(row["proximity_score"], 0)

    def test_valid_researched_strategy_gets_only_early_funnel_points(self):
        row = self.score(self.valid_attempt())
        self.assertEqual(row["proximity_score"], 25)
        self.assertFalse(row["needs_account_review"])

    def test_ready_product_and_sendable_prospects_raise_score_without_awarding_money(self):
        run = {
            "status": "materialized",
            "offer_url": "https://example.com/offer",
            "product_url": "https://example.com/product.zip",
            "quality_status": "ready_to_sell",
            "outreach_sendable": 3,
        }
        row = self.score(self.valid_attempt(), run=run)
        self.assertEqual(row["proximity_score"], 65)
        self.assertEqual(row["verified_events"], 0)

    def test_payment_proof_never_auto_verifies(self):
        candidate = {"payment_reference": "RANK-IAMO9", "status": "proof_received_unverified"}
        row = self.score(self.valid_attempt(), candidates=[candidate])
        self.assertEqual(row["proximity_score"], 92)
        self.assertTrue(row["needs_account_review"])
        self.assertEqual(row["verified_events"], 0)

    def test_provider_candidate_stops_below_100(self):
        candidate = {"payment_reference": "RANK-IAMO9", "status": "provider_confirmation_candidate"}
        row = self.score(self.valid_attempt(), candidates=[candidate])
        self.assertEqual(row["proximity_score"], 96)
        self.assertTrue(row["needs_account_review"])

    def test_only_verified_event_reaches_100(self):
        verified = {"RANK-IAMO9": {"payment_reference": "RANK-IAMO9", "verified_events": 1, "verified_net_profit_eur": "12.50"}}
        row = self.score(self.valid_attempt(), verified=verified)
        self.assertEqual(row["proximity_score"], 100)
        self.assertEqual(row["verified_net_profit_eur"], "12.50")
        self.assertFalse(row["needs_account_review"])


if __name__ == "__main__":
    unittest.main()
