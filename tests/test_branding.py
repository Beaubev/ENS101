from html.parser import HTMLParser
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
APP_NAME = "ENS 101 App - 1.0"


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

        self.assertEqual(APP_NAME, page.title)
        self.assertIn(APP_NAME, page.text)

    def test_admin_page_displays_versioned_app_name(self):
        page = parse_page("static/admin.html")

        self.assertIn(APP_NAME, page.title)
        self.assertIn(APP_NAME, page.text)

    def test_legacy_name_is_reserved_for_existing_data_directory(self):
        allowed = {
            (
                "app.py",
                'return Path.home() / "Library" / "Application Support" / "ENS 101 Mentor Desk"',
            )
        }
        occurrences = set()

        for path in ROOT.rglob("*"):
            if not path.is_file() or path.suffix not in {".py", ".html", ".js", ".css", ".md"}:
                continue
            if any(part in {".git", "venv", "tests", "__pycache__", ".playwright-cli"} for part in path.parts):
                continue
            relative_path = path.relative_to(ROOT).as_posix()
            for line in path.read_text(encoding="utf-8").splitlines():
                if "ENS 101 Mentor Desk" in line:
                    occurrences.add((relative_path, line.strip()))

        self.assertEqual(allowed, occurrences)


if __name__ == "__main__":
    unittest.main()
