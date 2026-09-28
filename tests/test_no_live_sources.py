import base64
import pathlib
import sys
import unittest
from unittest.mock import patch

from tests.app_harness import LocalServer, app

ROOT = pathlib.Path(__file__).resolve().parents[1]

SOURCE_MODULES = (
    "pathwayu_admin_client",
    "ensign_connect_client",
    "login_pathwayu_admin",
    "login_ensign_connect",
)
RETIRED_FILES = SOURCE_MODULES + ("pathwayu_admin_client.py.local-replaced-by-shared",)
RETIRED_GET = (
    "/api/career-explorer/session",
    "/api/career-explorer/admin-status",
    "/api/ensign-connect/session",
    "/api/ensign-connect/admin-status",
)
RETIRED_POST = (
    "/api/career-explorer/launch-login",
    "/api/career-explorer/lookup",
    "/api/ensign-connect/launch-login",
    "/api/ensign-connect/lookup",
    "/api/ensign-connect/lookup-live",
)


class NoSourceCodeTests(unittest.TestCase):
    def test_app_does_not_load_source_clients(self):
        for module in SOURCE_MODULES:
            with self.subTest(module=module):
                self.assertNotIn(module, sys.modules)

    def test_source_client_files_are_deleted(self):
        for name in RETIRED_FILES:
            filename = name if name.endswith("-shared") else f"{name}.py"
            with self.subTest(file=filename):
                self.assertFalse((ROOT / filename).exists())

    def test_live_lookup_helpers_are_gone(self):
        for name in (
            "lookup_student_connect",
            "lookup_student_completion",
            "lookup_student_report",
            "lookup_readiness_hub",
            "publish_pathwayu_result_to_hub",
            "check_admin_session",
            "check_connect_session",
        ):
            with self.subTest(name=name):
                self.assertFalse(hasattr(app, name))


class RetiredEndpointTests(unittest.TestCase):
    def test_retired_endpoints_return_410_without_lookups(self):
        with patch.object(app, "lookup_ens101_projection", side_effect=AssertionError("lookup called")), \
             LocalServer() as server:
            for path in RETIRED_GET:
                with self.subTest(method="GET", path=path):
                    status, body, _ = server.request("GET", path)
                    self.assertEqual(status, 410)
                    self.assertEqual(body["status"], "retired")
            for path in RETIRED_POST:
                with self.subTest(method="POST", path=path):
                    status, body, _ = server.request(
                        "POST", path, {"email": "synthetic.student@ensign.edu"}
                    )
                    self.assertEqual(status, 410)
                    self.assertEqual(body["status"], "retired")

    def test_retired_endpoints_ignore_query_strings(self):
        with LocalServer() as server:
            status, body, _ = server.request("POST", "/api/ensign-connect/lookup-live?x=1", {})
        self.assertEqual(status, 410)
        self.assertEqual(body["status"], "retired")


class ManualPdfTests(unittest.TestCase):
    def test_manual_pdf_parse_stays_local(self):
        synthetic_text = "Synthetic Career Explorer report text"
        pdf_base64 = base64.b64encode(b"%PDF-1.4 synthetic").decode("ascii")
        with patch.object(app, "extract_text_from_pdf", return_value=synthetic_text) as extract, \
             patch.object(app, "parse_pathwayu_text", return_value={"completed_count": 4}) as parse, \
             patch.object(app, "lookup_ens101_projection", side_effect=AssertionError("readiness called")), \
             patch.object(app, "urlopen", side_effect=AssertionError("network called")), \
             LocalServer() as server:
            status, body, _ = server.request(
                "POST", "/api/career-explorer/parse-pdf", {"pdf_base64": pdf_base64}
            )
        self.assertEqual(status, 200)
        self.assertEqual(body["data"], {"completed_count": 4})
        extract.assert_called_once()
        parse.assert_called_once_with(synthetic_text)


if __name__ == "__main__":
    unittest.main()
