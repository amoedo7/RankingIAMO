import unittest

from scripts import update_readme


class UpdateReadmeRenderingTests(unittest.TestCase):
    def test_render_has_no_trailing_whitespace(self):
        rendered = update_readme.render()
        offenders = [line for line in rendered.splitlines() if line != line.rstrip()]
        self.assertEqual(offenders, [])

    def test_public_links_keep_explicit_line_breaks_without_spaces(self):
        rendered = update_readme.render()
        self.assertIn(f"**[🏆 Abrir RankingIAMO en vivo →]({update_readme.ARENA_URL})**<br>", rendered)
        self.assertIn(f"**[👁️ Abrir ObserverIAMO →]({update_readme.OBSERVER_URL})**<br>", rendered)


if __name__ == "__main__":
    unittest.main()
