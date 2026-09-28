import unittest
from http import HTTPStatus
from unittest.mock import patch

from tests.app_harness import LocalServer, app
from tests.test_readiness_client import SYNTHETIC_EMAIL, valid_projection
from readiness_client import (
    ReadinessConfigError,
    ReadinessContractError,
    ReadinessRequestError,
    ReadinessUnavailable,
)

ROUTE = "/api/student-readiness/lookup"


def returns(payload):
    return lambda email: payload


def raises(error):
    def lookup(email):
        raise error
    return lookup


class BuildResponseTests(unittest.TestCase):
    def test_answers_map_to_http_status(self):
        cases = {
            "complete fresh": (valid_projection(), HTTPStatus.OK),
            "complete stale": (valid_projection(freshness="stale"), HTTPStatus.OK),
            "incomplete": (valid_projection(record_status="incomplete"), HTTPStatus.OK),
            "not found": (valid_projection(record_status="not_found"), HTTPStatus.NOT_FOUND),
        }
        for name, (payload, expected) in cases.items():
            with self.subTest(case=name):
                status, body = app.build_student_readiness_response(
                    SYNTHETIC_EMAIL, lookup_fn=returns(payload)
                )
                self.assertEqual(status, expected)
                self.assertEqual(body, payload)

    def test_failures_map_to_http_status(self):
        cases = {
            "unavailable": (ReadinessUnavailable("x"), HTTPStatus.SERVICE_UNAVAILABLE, "temporarily_unavailable"),
            "config": (ReadinessConfigError("x"), HTTPStatus.SERVICE_UNAVAILABLE, "temporarily_unavailable"),
            "contract": (ReadinessContractError("x"), HTTPStatus.BAD_GATEWAY, "incompatible_schema"),
            "request": (ReadinessRequestError("x"), HTTPStatus.BAD_REQUEST, "invalid_request"),
        }
        for name, (error, expected_status, expected_body_status) in cases.items():
            with self.subTest(case=name):
                status, body = app.build_student_readiness_response(
                    SYNTHETIC_EMAIL, lookup_fn=raises(error)
                )
                self.assertEqual(status, expected_status)
                self.assertEqual(body["status"], expected_body_status)
                self.assertNotIn(SYNTHETIC_EMAIL, str(body))

    def test_default_lookup_is_the_strict_projection_client(self):
        with patch.object(app, "lookup_ens101_projection", return_value=valid_projection()) as lookup:
            status, _ = app.build_student_readiness_response(SYNTHETIC_EMAIL)
        self.assertEqual(status, HTTPStatus.OK)
        lookup.assert_called_once_with(SYNTHETIC_EMAIL)


class RouteTests(unittest.TestCase):
    def setUp(self):
        allow = patch.object(app.RATE_LIMITER, "is_allowed", return_value=True)
        allow.start()
        self.addCleanup(allow.stop)

    def test_route_returns_projection(self):
        with patch.object(app, "lookup_ens101_projection", return_value=valid_projection()) as lookup, \
             LocalServer() as server:
            status, body, _ = server.request("POST", ROUTE, {"email": " Synthetic.Student@Ensign.edu "})
        self.assertEqual(status, 200)
        self.assertEqual(body["record_status"], "complete")
        lookup.assert_called_once_with(SYNTHETIC_EMAIL)

    def test_route_returns_404_for_not_found(self):
        payload = valid_projection(record_status="not_found")
        with patch.object(app, "lookup_ens101_projection", return_value=payload), \
             LocalServer() as server:
            status, body, _ = server.request("POST", ROUTE, {"email": SYNTHETIC_EMAIL})
        self.assertEqual(status, 404)
        self.assertEqual(body["record_status"], "not_found")

    def test_route_reports_outage_without_fallback(self):
        with patch.object(app, "lookup_ens101_projection", side_effect=ReadinessUnavailable("x")) as lookup, \
             LocalServer() as server:
            status, body, _ = server.request("POST", ROUTE, {"email": SYNTHETIC_EMAIL})
        self.assertEqual(status, 503)
        self.assertEqual(body["status"], "temporarily_unavailable")
        self.assertEqual(lookup.call_count, 1)

    def test_invalid_email_is_rejected_before_lookup(self):
        bodies = [
            {"email": "someone@gmail.com"},
            {"email": ""},
            {},
        ]
        with patch.object(app, "lookup_ens101_projection") as lookup, LocalServer() as server:
            for body in bodies:
                with self.subTest(body=body):
                    status, payload, raw = server.request("POST", ROUTE, body)
                    self.assertEqual(status, 400)
                    self.assertEqual(payload["status"], "invalid_email")
                    self.assertNotIn(b"gmail", raw)
            status, payload, _ = server.request("POST", ROUTE, raw_body=b"not json")
            self.assertEqual(status, 400)
        lookup.assert_not_called()

    def test_rate_limit_applies_before_lookup(self):
        with patch.object(app.RATE_LIMITER, "is_allowed", return_value=False), \
             patch.object(app, "lookup_ens101_projection") as lookup, \
             LocalServer() as server:
            status, body, _ = server.request("POST", ROUTE, {"email": SYNTHETIC_EMAIL})
        self.assertEqual(status, 429)
        self.assertEqual(body["status"], "rate_limited")
        lookup.assert_not_called()

    def test_route_is_limited_to_the_mentor_workstation(self):
        with patch.object(app.CoachHandler, "_career_lookup_is_local", return_value=False), \
             patch.object(app, "lookup_ens101_projection") as lookup, \
             LocalServer() as server:
            status, body, _ = server.request("POST", ROUTE, {"email": SYNTHETIC_EMAIL})
        self.assertEqual(status, 403)
        self.assertEqual(body["status"], "local_only")
        lookup.assert_not_called()


if __name__ == "__main__":
    unittest.main()
