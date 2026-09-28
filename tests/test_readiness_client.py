import copy
import io
import json
import os
import socket
import tempfile
import unittest
from unittest.mock import patch
from urllib.error import HTTPError, URLError

from readiness_client import (
    ReadinessConfigError,
    ReadinessContractError,
    ReadinessError,
    ReadinessRequestError,
    ReadinessUnavailable,
    lookup_ens101_projection,
    read_consumer_token,
)


SYNTHETIC_EMAIL = "synthetic.student@ensign.edu"
SYNTHETIC_TOKEN = "synthetic-token"
BASE_URL = "http://127.0.0.1:5055"


def valid_projection(**overrides):
    payload = {
        "projection": "ens101.v1",
        "projection_version": "1",
        "record_status": "complete",
        "freshness": "fresh",
        "last_successful_import_at": "2026-09-24T09:45:00+00:00",
        "sources": {
            "peoplegrove": {"status": "fresh", "imported_at": "2026-09-24T10:00:00+00:00"},
            "career_explorer": {"status": "fresh", "imported_at": "2026-09-24T09:45:00+00:00"},
        },
        "data": {
            "ensign_connect": {"account_ready": True},
            "career_explorer": {
                "status": "complete",
                "completed_count": 4,
                "total": 4,
                "missing": [],
                "holland_code": "SEC",
                "interests": ["Social", "Enterprising", "Conventional"],
                "values": ["Service"],
                "personality": {"Conscientiousness": 4.2},
                "workplace_preferences": ["Team-oriented"],
            },
        },
        "warnings": [],
    }
    payload.update(overrides)
    return payload


class FakeResponse:
    def __init__(self, raw, status=200):
        self.raw = raw
        self.status = status

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def read(self):
        return self.raw


def encode(payload):
    return json.dumps(payload).encode("utf-8")


def fake_ok(payload, captured=None):
    raw = payload if isinstance(payload, bytes) else encode(payload)

    def fake_open(request, timeout):
        if captured is not None:
            captured["request"] = request
            captured["timeout"] = timeout
        return FakeResponse(raw)

    return fake_open


def fake_http_error(code, payload):
    raw = payload if isinstance(payload, bytes) else encode(payload)

    def fake_open(request, timeout):
        raise HTTPError(request.full_url, code, "synthetic", {}, io.BytesIO(raw))

    return fake_open


def fake_raises(error):
    def fake_open(request, timeout):
        raise error

    return fake_open


def lookup(fake_open, **kwargs):
    kwargs.setdefault("token", SYNTHETIC_TOKEN)
    kwargs.setdefault("base_url", BASE_URL)
    return lookup_ens101_projection(SYNTHETIC_EMAIL, urlopen_fn=fake_open, **kwargs)


class RequestShapeTests(unittest.TestCase):
    def test_requests_exact_projection_with_email_only(self):
        captured = {}
        lookup_ens101_projection(
            "  Synthetic.Student@Ensign.edu ",
            urlopen_fn=fake_ok(valid_projection(), captured),
            token=SYNTHETIC_TOKEN,
            base_url=BASE_URL + "/",
        )
        request = captured["request"]
        self.assertEqual(
            request.full_url, BASE_URL + "/api/v1/projections/ens101.v1/lookup"
        )
        self.assertEqual(request.get_method(), "POST")
        self.assertEqual(json.loads(request.data), {"email": SYNTHETIC_EMAIL})
        self.assertEqual(request.get_header("X-readiness-token"), SYNTHETIC_TOKEN)
        self.assertEqual(captured["timeout"], 4.0)


class AcceptedResponseTests(unittest.TestCase):
    def test_complete_fresh_record_is_returned(self):
        payload = lookup(fake_ok(valid_projection()))
        self.assertEqual(payload["record_status"], "complete")

    def test_stale_record_with_null_fields_is_usable(self):
        body = valid_projection(
            record_status="incomplete",
            freshness="stale",
            last_successful_import_at=None,
            sources={
                "peoplegrove": {"status": "missing", "imported_at": None},
                "career_explorer": {"status": "stale", "imported_at": "2026-09-20T09:45:00+00:00"},
            },
            data={"ensign_connect": {"account_ready": None}, "career_explorer": None},
            warnings=["peoplegrove_source_missing", "career_explorer_source_stale"],
        )
        payload = lookup(fake_ok(body))
        self.assertEqual(payload["freshness"], "stale")
        self.assertIsNone(payload["last_successful_import_at"])

    def test_not_found_404_is_an_answer_not_an_outage(self):
        body = valid_projection(
            record_status="not_found",
            data={"ensign_connect": {"account_ready": False}, "career_explorer": None},
        )
        payload = lookup(fake_http_error(404, body))
        self.assertEqual(payload["record_status"], "not_found")


class ContractViolationTests(unittest.TestCase):
    def assert_rejected(self, body, code=200):
        opener = fake_ok(body) if code == 200 else fake_http_error(code, body)
        with self.assertRaises(ReadinessContractError):
            lookup(opener)

    def test_numeric_projection_version_is_rejected(self):
        self.assert_rejected(valid_projection(projection_version=1))

    def test_wrong_projection_is_rejected(self):
        self.assert_rejected(valid_projection(projection="resume.v1"))

    def test_unknown_record_status_is_rejected(self):
        self.assert_rejected(valid_projection(record_status="partial"))

    def test_unknown_freshness_is_rejected(self):
        self.assert_rejected(valid_projection(freshness="old"))

    def test_missing_top_level_keys_are_rejected(self):
        for key in ("sources", "data", "warnings", "last_successful_import_at"):
            with self.subTest(key=key):
                body = valid_projection()
                del body[key]
                self.assert_rejected(body)

    def test_unknown_source_status_is_rejected(self):
        body = valid_projection()
        body["sources"]["peoplegrove"]["status"] = "current"
        self.assert_rejected(body)

    def test_non_boolean_account_ready_is_rejected(self):
        body = valid_projection()
        body["data"]["ensign_connect"]["account_ready"] = "yes"
        self.assert_rejected(body)

    def test_non_object_career_explorer_is_rejected(self):
        body = valid_projection()
        body["data"]["career_explorer"] = ["complete"]
        self.assert_rejected(body)

    def test_non_list_warnings_are_rejected(self):
        self.assert_rejected(valid_projection(warnings="stale"))

    def test_status_code_and_record_status_must_agree(self):
        self.assert_rejected(valid_projection(record_status="not_found"), code=200)
        self.assert_rejected(valid_projection(record_status="complete"), code=404)

    def test_unsupported_projection_409_is_a_contract_error(self):
        self.assert_rejected({"status": "unsupported_projection"}, code=409)


class FailureMappingTests(unittest.TestCase):
    def test_setup_failures_are_config_errors(self):
        for code, status in ((401, "unauthorized"), (403, "forbidden_projection")):
            with self.subTest(code=code):
                with self.assertRaises(ReadinessConfigError):
                    lookup(fake_http_error(code, {"status": status}))

    def test_missing_token_is_a_config_error(self):
        with self.assertRaises(ReadinessConfigError):
            lookup(fake_ok(valid_projection()), token="", token_reader=lambda: None)

    def test_token_path_can_be_overridden(self):
        with tempfile.TemporaryDirectory() as directory:
            token_file = os.path.join(directory, "consumer-token")
            with open(token_file, "w", encoding="utf-8") as handle:
                handle.write(SYNTHETIC_TOKEN + "\n")
            with patch.dict(os.environ, {"READINESS_CONSUMER_TOKEN_PATH": token_file}):
                self.assertEqual(read_consumer_token(), SYNTHETIC_TOKEN)
            with patch.dict(os.environ, {"READINESS_CONSUMER_TOKEN_PATH": token_file + ".missing"}):
                self.assertIsNone(read_consumer_token())

    def test_error_hierarchy(self):
        self.assertTrue(issubclass(ReadinessConfigError, ReadinessUnavailable))
        for error in (ReadinessUnavailable, ReadinessContractError, ReadinessRequestError):
            self.assertTrue(issubclass(error, ReadinessError))

    def test_rejected_email_is_a_request_error(self):
        with self.assertRaises(ReadinessRequestError):
            lookup(fake_http_error(400, {"status": "invalid_request"}))

    def test_outages_are_unavailable(self):
        cases = {
            "503": fake_http_error(503, {"status": "temporarily_unavailable"}),
            "500 non-json": fake_http_error(500, b"<html>error</html>"),
            "refused": fake_raises(URLError(ConnectionRefusedError())),
            "oserror": fake_raises(OSError("connection refused")),
            "timeout": fake_raises(socket.timeout("timed out")),
            "non-json 200": fake_ok(b"not json"),
        }
        for name, opener in cases.items():
            with self.subTest(case=name):
                with self.assertRaises(ReadinessUnavailable) as caught:
                    lookup(opener)
                self.assertNotIsInstance(caught.exception, ReadinessConfigError)


class PrivacyTests(unittest.TestCase):
    def test_error_messages_never_leak_email_token_or_body(self):
        leaky_body = valid_projection(projection="resume.v1", note=SYNTHETIC_EMAIL)
        openers = [
            fake_ok(leaky_body),
            fake_http_error(400, {"status": "invalid_request", "email": SYNTHETIC_EMAIL}),
            fake_http_error(401, {"status": "unauthorized"}),
            fake_raises(OSError(f"failed for {SYNTHETIC_EMAIL}")),
        ]
        for opener in openers:
            with self.assertRaises(ReadinessError) as caught:
                lookup(opener)
            message = str(caught.exception)
            self.assertNotIn(SYNTHETIC_EMAIL, message)
            self.assertNotIn(SYNTHETIC_TOKEN, message)
            self.assertNotIn("resume.v1", message)

    def test_valid_payload_is_not_mutated(self):
        body = valid_projection()
        original = copy.deepcopy(body)
        self.assertEqual(lookup(fake_ok(body)), original)


if __name__ == "__main__":
    unittest.main()
