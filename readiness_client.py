"""Strict client for the Student Readiness Hub `ens101.v1` projection.

ENS 101 reads student readiness only through this module. It calls a single
cache-only Hub endpoint and never contacts PeopleGrove or Career Explorer.
Every response is validated against the published contract before it reaches
the rest of the app, and every failure becomes a named exception so callers
cannot silently fall back to another source.

Contract: Student Readiness Hub README, "ENS101 projection API (`ens101.v1`)".
"""

import json
import os
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

PROJECTION = "ens101.v1"
PROJECTION_VERSION = "1"
DEFAULT_HUB_URL = "http://127.0.0.1:5055"
TOKEN_PATH = (
    Path.home()
    / "Library"
    / "Application Support"
    / "Ensign Student Readiness Hub"
    / "consumer-token"
)
TIMEOUT_SECONDS = 4.0

RECORD_STATUSES = {"complete", "incomplete", "not_found"}
FRESHNESS_VALUES = {"fresh", "stale"}
SOURCE_NAMES = ("peoplegrove", "career_explorer")
SOURCE_STATUSES = {"fresh", "stale", "missing"}


class ReadinessError(Exception):
    """Base class for every Student Readiness lookup failure."""


class ReadinessUnavailable(ReadinessError):
    """The Hub could not be reached or could not answer right now."""


class ReadinessConfigError(ReadinessUnavailable):
    """ENS is not set up to use the Hub (missing, wrong, or unallowlisted token)."""


class ReadinessContractError(ReadinessError):
    """The Hub answered with a projection ENS does not understand."""


class ReadinessRequestError(ReadinessError):
    """The Hub rejected the lookup request (for example, an invalid email)."""


def read_consumer_token():
    try:
        token = TOKEN_PATH.read_text(encoding="utf-8").strip()
    except OSError:
        return None
    return token or None


def lookup_ens101_projection(
    email,
    *,
    urlopen_fn=urlopen,
    token=None,
    base_url=None,
    token_reader=read_consumer_token,
):
    token = token or token_reader()
    if not token:
        raise ReadinessConfigError("Student Readiness consumer token is not configured")
    base_url = base_url or os.environ.get("READINESS_HUB_URL", DEFAULT_HUB_URL)

    request = Request(
        f"{base_url.rstrip('/')}/api/v1/projections/{PROJECTION}/lookup",
        data=json.dumps({"email": email.strip().lower()}).encode("utf-8"),
        headers={"Content-Type": "application/json", "X-Readiness-Token": token},
        method="POST",
    )
    try:
        with urlopen_fn(request, timeout=TIMEOUT_SECONDS) as response:
            status, raw = response.status, response.read()
    except HTTPError as error:
        # HTTPError is also a URLError/OSError, so it must be handled first:
        # a 404 is a valid "not found" answer, not an outage.
        try:
            status = error.code
            raise_for_status(status)
            raw = error.read()
        finally:
            error.close()
    except (URLError, OSError) as error:
        raise ReadinessUnavailable("Student Readiness is temporarily unavailable") from error

    payload = parse_json(raw)
    validate_projection(payload, http_status=status)
    return payload


def raise_for_status(status):
    """Raise the named exception for any status other than 200 or 404."""
    if status in (200, 404):
        return
    if status in (401, 403):
        raise ReadinessConfigError(f"Student Readiness rejected ENS credentials ({status})")
    if status == 400:
        raise ReadinessRequestError("Student Readiness rejected the lookup request")
    if status == 409:
        raise ReadinessContractError("Student Readiness does not support ens101.v1")
    if status >= 500:
        raise ReadinessUnavailable("Student Readiness is temporarily unavailable")
    raise ReadinessContractError(f"Student Readiness returned unexpected status {status}")


def parse_json(raw):
    try:
        return json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, ValueError):
        raise ReadinessUnavailable("Student Readiness returned an unreadable response") from None


def validate_projection(payload, *, http_status):
    """Reject anything that does not match the ens101.v1 contract exactly."""
    if not isinstance(payload, dict):
        _reject("response")
    if payload.get("projection") != PROJECTION:
        _reject("projection")
    # `"1" == 1` is False in Python, so a numeric version is rejected on purpose.
    if payload.get("projection_version") != PROJECTION_VERSION:
        _reject("projection_version")

    record_status = payload.get("record_status")
    if record_status not in RECORD_STATUSES:
        _reject("record_status")
    if (http_status == 404) != (record_status == "not_found"):
        _reject("record_status")
    if payload.get("freshness") not in FRESHNESS_VALUES:
        _reject("freshness")
    if "last_successful_import_at" not in payload or not _is_optional_str(
        payload["last_successful_import_at"]
    ):
        _reject("last_successful_import_at")

    sources = payload.get("sources")
    if not isinstance(sources, dict):
        _reject("sources")
    for name in SOURCE_NAMES:
        source = sources.get(name)
        if not isinstance(source, dict) or source.get("status") not in SOURCE_STATUSES:
            _reject(f"sources.{name}")
        if "imported_at" not in source or not _is_optional_str(source["imported_at"]):
            _reject(f"sources.{name}.imported_at")

    data = payload.get("data")
    if not isinstance(data, dict):
        _reject("data")
    ensign_connect = data.get("ensign_connect")
    if not isinstance(ensign_connect, dict) or "account_ready" not in ensign_connect:
        _reject("data.ensign_connect")
    # bool is checked explicitly: isinstance(1, bool) is False, but 1 == True.
    account_ready = ensign_connect["account_ready"]
    if account_ready is not None and not isinstance(account_ready, bool):
        _reject("data.ensign_connect.account_ready")
    if "career_explorer" not in data or not (
        data["career_explorer"] is None or isinstance(data["career_explorer"], dict)
    ):
        _reject("data.career_explorer")

    warnings = payload.get("warnings")
    if not isinstance(warnings, list) or not all(isinstance(w, str) for w in warnings):
        _reject("warnings")


def _is_optional_str(value):
    return value is None or isinstance(value, str)


def _reject(field):
    raise ReadinessContractError(f"Student Readiness response has an invalid {field}")
