from pathlib import Path
import json
import subprocess
import unittest

from playwright.sync_api import sync_playwright


ROOT = Path(__file__).resolve().parents[1]
NOTE_UTILS = ROOT / "static" / "note-utils.js"


def normalize_note(value):
    script = (
        "const { ensurePermanentConversationTag } = require(process.argv[1]);"
        "process.stdout.write(ensurePermanentConversationTag(JSON.parse(process.argv[2])));"
    )
    result = subprocess.run(
        ["node", "-e", script, str(NOTE_UTILS), json.dumps(value)],
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout


class ConversationNoteTagTests(unittest.TestCase):
    def test_empty_note_contains_required_tag(self):
        self.assertEqual("#SSTEAM", normalize_note(""))

    def test_existing_note_is_preserved_below_required_tag(self):
        self.assertEqual(
            "#SSTEAM\nDiscussed internship timing.",
            normalize_note("Discussed internship timing."),
        )

    def test_required_tag_is_not_duplicated(self):
        self.assertEqual(
            "#SSTEAM\nDiscussed internship timing.",
            normalize_note("#SSTEAM\nDiscussed internship timing.\n#SSTEAM"),
        )

    def test_app_integrates_required_tag_with_field_and_copied_notes(self):
        app_js = (ROOT / "static" / "app.js").read_text(encoding="utf-8")
        index_html = (ROOT / "static" / "index.html").read_text(encoding="utf-8")

        self.assertIn('src="note-utils.js"', index_html)
        self.assertIn("ensurePermanentConversationTag", app_js)
        self.assertIn("sessionNotes: ensurePermanentConversationTag('')", app_js)
        self.assertIn("session_notes: ensurePermanentConversationTag(state.sessionNotes)", app_js)

    def test_new_appointment_renders_required_tag_immediately(self):
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto((ROOT / "static" / "index.html").as_uri(), wait_until="domcontentloaded")

            self.assertEqual("#SSTEAM", page.locator("#session-notes").input_value())
            browser.close()


if __name__ == "__main__":
    unittest.main()
