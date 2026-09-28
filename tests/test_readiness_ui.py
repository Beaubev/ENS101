import pathlib
import re
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]


def read(relative_path):
    return (ROOT / relative_path).read_text(encoding="utf-8")


class ReadinessUiTests(unittest.TestCase):
    def setUp(self):
        self.html = read("static/index.html")
        self.js = read("static/app.js")
        self.content = self.html + self.js

    def test_live_source_controls_are_absent(self):
        forbidden = [
            "Check live",
            "Checking Ensign Connect (PeopleGrove)",
            "/api/ensign-connect/lookup",
            "/api/career-explorer/lookup",
            "/api/career-explorer/session",
            "/api/ensign-connect/session",
            "launch-login",
            "refresh_pathwayu",
            "Authenticate Career Explorer",
            "Authenticate Ensign Connect",
            "btn-check-connect-live",
            "prep-career-auth-btn",
            "prep-connect-auth-btn",
        ]
        for value in forbidden:
            with self.subTest(value=value):
                self.assertNotIn(value, self.content)

    def test_single_student_readiness_action(self):
        self.assertIn("/api/student-readiness/lookup", self.js)
        self.assertEqual(self.js.count("/api/student-readiness/lookup"), 1)
        self.assertIn("Check Student Readiness", self.html)
        self.assertIn("Checking previously retrieved readiness data…", self.js)

    def test_freshness_states_are_rendered(self):
        for copy in (
            "Last updated",
            "Student Readiness data is older than 36 hours.",
            "Showing the last successful import from",
            "Student Readiness is temporarily unavailable",
            "No retrieved Student Readiness record",
            "unsupported data version",
        ):
            with self.subTest(copy=copy):
                self.assertIn(copy, self.js)

    def test_manual_pdf_fallback_is_labeled_and_separate(self):
        self.assertIn("Manual fallback: use a student-provided Career Explorer PDF", self.html)
        upload = re.search(r"async function handlePdfUpload\(file\) \{.*?\n\}", self.js, re.S)
        self.assertIsNotNone(upload)
        self.assertNotIn("student-readiness", upload.group(0))
        self.assertNotIn("readiness-freshness", upload.group(0))

    def test_personality_scores_are_shown_out_of_five(self):
        self.assertIn("personality_scores", self.js)
        self.assertIn("/ 5", self.js)

    def test_download_never_requests_an_unscoped_report(self):
        self.assertNotIn("url = '/api/career-explorer/download-report';", self.js)
        self.assertNotIn("/api/career-explorer/download-report?email=", self.js)


if __name__ == "__main__":
    unittest.main()
