import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from mentor_context import build_mentor_context, select_cases
from fallback_strategy import price_for, target_for


class MoneyMentorTests(unittest.TestCase):
    def test_real_money_case_library_has_multiple_models(self):
        data = json.loads((ROOT / "data" / "real_ai_money_cases.json").read_text(encoding="utf-8"))
        cases = data.get("cases", [])
        self.assertGreaterEqual(len(cases), 10)
        self.assertEqual(len({row.get("id") for row in cases}), len(cases))
        self.assertTrue(all(str(row.get("source", "")).startswith("https://") for row in cases))

    def test_rotating_mentors_are_unique(self):
        selected = select_cases(83, 3)
        self.assertEqual(len(selected), 3)
        self.assertEqual(len({row.get("id") for row in selected}), 3)

    def test_agent_commons_context_includes_external_protocols(self):
        context = build_mentor_context(83)
        channels = context.get("agent_commons", {}).get("external_channels", [])
        ids = {row.get("id") for row in channels}
        self.assertIn("a2a", ids)
        self.assertIn("virtuals-acp", ids)

    def test_fallback_has_nonzero_offer_prices_for_sellable_models(self):
        price, unit = price_for("Productized services", 83)
        self.assertGreater(price, 0)
        self.assertTrue(unit)
        self.assertIn("small businesses", target_for("Productized services", "Website audit"))


if __name__ == "__main__":
    unittest.main()
