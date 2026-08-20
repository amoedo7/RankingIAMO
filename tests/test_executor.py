import importlib.util
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts" / "executor_finalize.py"
spec = importlib.util.spec_from_file_location("executor_finalize", MODULE_PATH)
executor = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = executor
spec.loader.exec_module(executor)


class ExecutorPolicyTests(unittest.TestCase):
    def test_product_paths_cannot_escape_workspace(self):
        self.assertIsNone(executor.safe_product_path("../../secret.txt"))
        self.assertIsNone(executor.safe_product_path("/etc/passwd.txt"))
        self.assertIsNone(executor.safe_product_path("payload.exe"))
        self.assertEqual(str(executor.safe_product_path("docs/guide.md")), "docs/guide.md")

    def test_amo_urls_are_not_external_evidence(self):
        self.assertFalse(executor.external_url("https://cobramo.netlify.app/"))
        self.assertFalse(executor.external_url("https://github.com/amoedo7/RankingIAMO"))
        self.assertTrue(executor.external_url("https://example.com/contact"))

    def test_outreach_requires_external_evidence_and_valid_contact(self):
        prospects = [
            {
                "company": "Sin evidencia",
                "contact_email": "sales@example.com",
                "evidence_url": "https://cobramo.netlify.app/",
                "message": "Oferta",
            },
            {
                "company": "Empresa Real",
                "website": "https://example.com/",
                "contact_email": "sales@example.com",
                "contact_url": "https://example.com/contact",
                "evidence_url": "https://example.com/contact",
                "why_fit": "Tiene una necesidad relevante.",
                "subject": "Propuesta concreta",
                "message": "Podemos resolver este problema.",
            },
        ]
        rows = executor.normalize_prospects(
            prospects,
            "https://raw.githack.com/amoedo7/RankingIAMO/main/offers/RANK-IAMO99/index.html",
            "RANK-IAMO99",
            3,
        )
        self.assertEqual(len(rows), 1)
        row = rows[0]
        self.assertEqual(row["contact_email"], "sales@example.com")
        self.assertEqual(row["status"], "pending")
        self.assertIn("DesarrollAMO", row["message"])
        self.assertIn("RANK-IAMO99", row["message"])
        self.assertIn("no te escribamos de nuevo", row["message"])

    def test_outreach_is_capped(self):
        prospects = []
        for i in range(10):
            prospects.append({
                "company": f"Empresa {i}",
                "contact_email": f"sales{i}@example.com",
                "evidence_url": f"https://example.com/contact/{i}",
                "message": f"Oferta {i}",
            })
        rows = executor.normalize_prospects(
            prospects,
            "https://example.com/offer",
            "RANK-IAMO1",
            3,
        )
        self.assertEqual(len(rows), 3)


if __name__ == "__main__":
    unittest.main()
