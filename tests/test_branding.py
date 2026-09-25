from html.parser import HTMLParser
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
APP_NAME = "ENS 101 Mentor Desk"
APP_VERSION = "v1.0"
APP_TITLE = f"{APP_NAME} {APP_VERSION} — Ensign College Career Services"


class PageTextParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.title_parts = []
        self.text_parts = []
        self._in_title = False

    def handle_starttag(self, tag, attrs):
        if tag == "title":
            self._in_title = True

    def handle_endtag(self, tag):
        if tag == "title":
            self._in_title = False

    def handle_data(self, data):
        text = data.strip()
        if not text:
            return
        self.text_parts.append(text)
        if self._in_title:
            self.title_parts.append(text)

    @property
    def title(self):
        return " ".join(self.title_parts)

    @property
    def text(self):
        return " ".join(self.text_parts)


def parse_page(relative_path):
    parser = PageTextParser()
    parser.feed((ROOT / relative_path).read_text(encoding="utf-8"))
    return parser


class BrandingTests(unittest.TestCase):
    def test_main_page_displays_versioned_app_name(self):
        page = parse_page("static/index.html")

        self.assertEqual(APP_TITLE, page.title)
        self.assertIn(APP_NAME, page.text)
        self.assertIn(APP_VERSION, page.text)


if __name__ == "__main__":
    unittest.main()
