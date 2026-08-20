import importlib.util
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load_module(name, relative_path):
    spec = importlib.util.spec_from_file_location(name, ROOT / relative_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


prepare = load_module("prepare_iamo", "scripts/prepare_iamo.py")
finalize = load_module("finalize_iamo", "scripts/finalize_iamo.py")


class PrepareIAMOTests(unittest.TestCase):
    def test_next_number_is_monotonic(self):
        competitors = [
            {"number": 1, "name": "IAMO1"},
            {"number": 2, "name": "IAMO2"},
            {"number": 7, "name": "IAMO7"},
        ]
        self.assertEqual(prepare.next_number(competitors), 8)

    def test_next_number_starts_at_one(self):
        self.assertEqual(prepare.next_number([]), 1)

    def test_history_is_bounded(self):
        giant = "x" * 10000
        compact = prepare.compact_history(
            [
                {
                    "competitor_name": "IAMO1",
                    "result": {
                        "opportunity": giant,
                        "target_customer": giant,
                        "offer": giant,
                        "differentiation_from_previous": giant,
                    },
                }
            ]
        )
        self.assertLessEqual(len(compact[0]["opportunity"]), 600)
        self.assertLessEqual(len(compact[0]["offer"]), 600)


class FinalizeIAMOTests(unittest.TestCase):
    def setUp(self):
        self.identity = {
            "id": "iamo1",
            "name": "IAMO1",
            "number": 1,
            "born_at": "2026-08-20T00:00:00Z",
        }

    def test_extract_json_accepts_plain_json(self):
        parsed = finalize.extract_json('{"offer":"demo"}')
        self.assertEqual(parsed["offer"], "demo")

    def test_extract_json_accepts_fenced_json(self):
        parsed = finalize.extract_json('```json\n{"offer":"demo"}\n```')
        self.assertEqual(parsed["offer"], "demo")

    def test_model_cannot_credit_itself(self):
        raw = {
            "competitor_name": "IAMO999",
            "opportunity": "legit opportunity",
            "revenue_claim_eur": "999999.99",
            "execution_packet": {
                "cobramo_url": "https://evil.example/",
            },
        }
        normalized = finalize.normalize_result(raw, self.identity)
        self.assertEqual(normalized["competitor_name"], "IAMO1")
        self.assertEqual(normalized["revenue_claim_eur"], "0.00")
        self.assertEqual(
            normalized["execution_packet"]["cobramo_url"],
            "https://cobramo.netlify.app/",
        )

    def test_confidence_is_clamped(self):
        high = finalize.normalize_result({"confidence_0_100": 999}, self.identity)
        low = finalize.normalize_result({"confidence_0_100": -10}, self.identity)
        self.assertEqual(high["confidence_0_100"], 100)
        self.assertEqual(low["confidence_0_100"], 0)


if __name__ == "__main__":
    unittest.main()
