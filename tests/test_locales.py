import gettext
import unittest

from network_puzzles import localedir


class TestGettext(unittest.TestCase):
    def test_fr_catalog_loads(self):
        try:
            t = gettext.translation(
                "networkpuzzles", localedir=localedir, languages=["fr"]
            )
        except FileNotFoundError:
            self.fail("FR .mo file not found; run `uv run scripts/compile-locales.py`")
        self.assertEqual(t.gettext("Ping Test"), "Test de ping")
