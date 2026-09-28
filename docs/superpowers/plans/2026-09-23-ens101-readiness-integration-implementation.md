# ENS 101 Student Readiness Integration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make ENS 101 read the `ens101.v1` Student Readiness projection exclusively, with visible freshness and no live PeopleGrove or PathwayU capability.

**Architecture:** A focused `readiness_client.py` owns the authenticated projection request and response validation. `app.py` exposes one ENS-facing lookup route and retains PDF upload as a separate manual workflow; the frontend removes all source login/session/live controls and renders Student Readiness freshness states.

**Tech Stack:** Python 3 stdlib HTTP server, `urllib`, existing HTML/CSS/JavaScript frontend, `unittest`.

**Spec:** `docs/superpowers/specs/2026-09-23-student-readiness-data-hub-design.md`

## Global Constraints

- Do not begin this plan until the Student Readiness plan handback proves the deployed `ens101.v1` projection is ready.
- ENS must never contact PeopleGrove or PathwayU, even on cache miss, stale data, timeout, malformed response, or Student Readiness outage.
- ENS requests only `POST /api/v1/projections/ens101.v1/lookup` with `{"email":"..."}` and `X-Readiness-Token`.
- Reject incompatible projection versions and incomplete response contracts visibly.
- Data older than 36 hours remains usable with a stale warning.
- Preserve manual PDF upload as an explicit workflow; it must not write to Student Readiness.
- Use the app name `ENS 101 Mentor Desk v1.0` consistently.
- Never add real student data to tests, logs, screenshots, commits, or handoff messages.

## Review Focus

- Student Readiness timeout, connection refusal, or non-JSON response must produce `temporarily_unavailable` without any source fallback; Task 1 tests this.
- A response claiming the wrong projection or version must be rejected before its data reaches guidance generation; Task 1 tests this.
- Stale data must remain usable while displaying both freshness and the last successful import timestamp; Task 3 tests this.
- Legacy live endpoints must be unavailable even when called directly outside the UI; Task 2 tests this.
- The manual PDF workflow must parse locally without publishing results or initiating network source access; Task 2 tests this.

---

### Task 1: Add and Test the Strict Student Readiness Client

> **Revised 2026-09-28** to match the deployed hub contract: hub `README.md`
> "ENS101 projection API" and `build_ens101_projection()` / the projection route
> in hub `app.py` at commit `3bb7339`. The original draft assumed a numeric
> version, top-level `peoplegrove`/`pathwayu` fields, and a `200` for
> `not_found`; none of those match the hub.

**Files:**
- Create: `readiness_client.py`
- Create: `tests/test_readiness_client.py`
- Modify: `.env.example`

**Interfaces:**
- Consumes: `READINESS_HUB_URL`, `~/Library/Application Support/Ensign Student Readiness Hub/consumer-token`, and Student Readiness `ens101.v1`.
- Produces: `lookup_ens101_projection(email, *, urlopen_fn=urlopen, token=None, base_url=READINESS_HUB_URL) -> dict` and the exceptions below.

**Contract the client enforces (from the hub):**

```json
{
  "projection": "ens101.v1",
  "projection_version": "1",
  "record_status": "complete | incomplete | not_found",
  "freshness": "fresh | stale",
  "last_successful_import_at": "ISO-8601 string or null",
  "sources": {
    "peoplegrove":     {"status": "fresh | stale | missing", "imported_at": "string or null"},
    "career_explorer": {"status": "fresh | stale | missing", "imported_at": "string or null"}
  },
  "data": {
    "ensign_connect": {"account_ready": "true | false | null"},
    "career_explorer": "object or null (individual detail fields may be null)"
  },
  "warnings": ["string", "..."]
}
```

- `projection_version` is the **string** `"1"`; the number `1` is rejected.
- `404` carries a full projection body with `record_status: "not_found"`. It is a valid answer, not an outage.
- The HTTP status and `record_status` must agree: `404` if and only if `not_found`.

**HTTP status → client outcome:**

| Hub response | Client outcome |
|---|---|
| `200` | Validated payload (`complete` or `incomplete`) |
| `404` | Validated payload (`not_found`) |
| `400 invalid_request` | `ReadinessRequestError` |
| `401 unauthorized`, `403 forbidden_projection`, missing token | `ReadinessConfigError` (subclass of `ReadinessUnavailable`) |
| `409 unsupported_projection` | `ReadinessContractError` |
| `5xx`, timeout, connection refused, non-JSON body | `ReadinessUnavailable` |
| `200`/`404` whose body fails validation | `ReadinessContractError` |

`urllib` raises `HTTPError` for every 4xx/5xx, so the client catches `HTTPError` **before** `URLError`/`OSError` and branches on `error.code`. No exception message may include the response body, the token, or the email.

- [ ] **Step 1: Write failing client tests**

Use a `fake_open` that returns a response object for `200` and raises `urllib.error.HTTPError(url, code, msg, hdrs, io.BytesIO(body))` for other statuses. Build payloads from one synthetic `valid_projection(**overrides)` helper so each test changes only the field under test. Cover at minimum:

- Requests exactly `POST {base}/api/v1/projections/ens101.v1/lookup` with body `{"email": ...}` only (no refresh fields) and the `X-Readiness-Token` header; email is trimmed and lowercased.
- Accepts a complete fresh `200`.
- Accepts a stale record with `last_successful_import_at: null`, a `missing` source, `account_ready: null`, and `data.career_explorer: null`.
- Returns (does not raise) a `404` `not_found` body.
- Rejects `projection_version` as the number `1`, and a wrong `projection` name.
- Rejects an unknown `record_status` or `freshness`, a missing `sources`/`data`/`warnings` key, and a non-boolean `account_ready`.
- Rejects a `200` claiming `not_found` and a `404` claiming `complete`.
- Maps `409` → `ReadinessContractError`; `401`/`403`/missing token → `ReadinessConfigError`; `400` → `ReadinessRequestError`; `503`, `OSError`, timeout, and non-JSON → `ReadinessUnavailable`.
- Asserts `isinstance(ReadinessConfigError(), ReadinessUnavailable)`.
- No raised message contains the synthetic email or token.

```python
def test_not_found_404_is_an_answer_not_an_outage(self):
    body = valid_projection(record_status="not_found")
    fake_open = fake_http_error(404, body)
    payload = lookup_ens101_projection("synthetic@ensign.edu", urlopen_fn=fake_open,
                                       token="synthetic-token")
    self.assertEqual(payload["record_status"], "not_found")

def test_numeric_projection_version_is_rejected(self):
    fake_open = fake_ok(valid_projection(projection_version=1))
    with self.assertRaises(ReadinessContractError):
        lookup_ens101_projection("synthetic@ensign.edu", urlopen_fn=fake_open,
                                 token="synthetic-token")
```

- [ ] **Step 2: Run the focused tests and confirm failure**

Run: `python3 -m unittest tests.test_readiness_client -v`

Expected: FAIL because `readiness_client.py` does not exist.

- [ ] **Step 3: Implement the strict client**

```python
PROJECTION = "ens101.v1"
PROJECTION_VERSION = "1"


def lookup_ens101_projection(email, *, urlopen_fn=urlopen, token=None,
                             base_url=READINESS_HUB_URL):
    token = token or read_consumer_token()  # raises ReadinessConfigError when absent
    request = Request(
        f"{base_url.rstrip('/')}/api/v1/projections/{PROJECTION}/lookup",
        data=json.dumps({"email": email.strip().lower()}).encode("utf-8"),
        headers={"Content-Type": "application/json", "X-Readiness-Token": token},
        method="POST",
    )
    try:
        with urlopen_fn(request, timeout=4.0) as response:
            status, raw = response.status, response.read()
    except HTTPError as error:          # must come before URLError/OSError
        status, raw = error.code, error.read()
        raise_for_status(status)        # 400/401/403/409/5xx -> named exceptions
    except (URLError, OSError, TimeoutError) as error:
        raise ReadinessUnavailable("Student Readiness is temporarily unavailable") from error
    payload = parse_json(raw)           # non-JSON -> ReadinessUnavailable
    validate_projection(payload, http_status=status)
    return payload
```

`validate_projection` enforces every rule in the contract above and raises `ReadinessContractError` with a message naming only the offending field.

- [ ] **Step 4: Document only non-secret configuration**

Add `READINESS_HUB_URL=http://127.0.0.1:5055` to `.env.example` with a comment giving the token path; never add token contents.

- [ ] **Step 5: Run focused and complete tests**

Run: `python3 -m unittest tests.test_readiness_client -v && python3 -m unittest discover -v`

Expected: all tests PASS.

- [ ] **Step 6: Commit the client**

```bash
git add readiness_client.py tests/test_readiness_client.py .env.example
git commit -m "feat: add strict Student Readiness projection client"
```

### Task 2: Replace Backend Live Lookups and Retire Source Routes

**Files:**
- Modify: `app.py`
- Create: `tests/test_readiness_routes.py`
- Create: `tests/test_no_live_sources.py`
- Delete after dependency scan: `ensign_connect_client.py`
- Delete after dependency scan: `login_ensign_connect.py`
- Delete after dependency scan: `login_pathwayu_admin.py`
- Delete after dependency scan: `pathwayu_admin_client.py.local-replaced-by-shared`

**Interfaces:**
- Consumes: `lookup_ens101_projection` from Task 1.
- Produces: `build_student_readiness_response(email, lookup_fn=lookup_ens101_projection) -> tuple[int, dict]`, `POST /api/student-readiness/lookup`, and HTTP 410 retired source endpoints.

- [ ] **Step 1: Write failing route tests with source clients poisoned**

Create a test handler using the repository's existing request test pattern. Patch `lookup_student_connect`, `lookup_student_completion`, and `lookup_student_report` to raise `AssertionError("live source called")`. Cover projection responses for complete, stale, incomplete, not found, unavailable, and contract error.

```python
def test_cache_miss_never_calls_live_sources(self):
    with patch.object(app, "lookup_student_connect", side_effect=AssertionError), \
         patch.object(app, "lookup_student_completion", side_effect=AssertionError), \
         patch.object(app, "lookup_student_report", side_effect=AssertionError), \
         patch.object(app, "lookup_ens101_projection", return_value={
             "projection": "ens101.v1", "projection_version": 1,
             "record_status": "not_found", "freshness": "fresh",
             "last_successful_import_at": "2026-09-23T09:00:00Z",
         }):
        status, body = app.build_student_readiness_response(
            "synthetic@ensign.edu", lookup_fn=app.lookup_ens101_projection
        )
    self.assertEqual(status, 404)
    self.assertEqual(body["record_status"], "not_found")
```

- [ ] **Step 2: Run route tests and confirm the current live behavior fails them**

Run: `python -m unittest tests.test_readiness_routes tests.test_no_live_sources -v`

Expected: FAIL because the unified route is absent and legacy live paths remain callable.

- [ ] **Step 3: Add the unified cache-only route**

In `app.py`, validate the email and rate limit exactly once, call `lookup_ens101_projection`, and translate contract states:

- `complete`, `fresh` -> HTTP 200
- `complete`, `stale` -> HTTP 200 with warning
- `incomplete` -> HTTP 200 with completeness warnings
- `not_found` -> HTTP 404
- `ReadinessUnavailable` -> HTTP 503
- `ReadinessContractError` -> HTTP 502 with `incompatible_schema`
- `ReadinessRequestError` -> HTTP 400 with `invalid_request` (the email is never echoed)
- `ReadinessConfigError` needs no branch: it subclasses `ReadinessUnavailable` and maps to 503; log its class name server-side so setup problems are distinguishable

Do not catch these conditions and call another lookup provider.

Keep the translation testable outside the HTTP server:

```python
def build_student_readiness_response(email, lookup_fn=lookup_ens101_projection):
    try:
        payload = lookup_fn(email)
    except ReadinessUnavailable:
        return HTTPStatus.SERVICE_UNAVAILABLE, {
            "status": "temporarily_unavailable",
            "message": "Student Readiness is temporarily unavailable.",
        }
    except ReadinessContractError:
        return HTTPStatus.BAD_GATEWAY, {
            "status": "incompatible_schema",
            "message": "Student Readiness returned an unsupported data version.",
        }
    status = payload["record_status"]
    return (HTTPStatus.NOT_FOUND if status == "not_found" else HTTPStatus.OK), payload
```

- [ ] **Step 4: Remove live source behavior**

Remove PathwayU/PeopleGrove client imports, login process globals, `publish_pathwayu_result_to_hub`, OneDrive snapshot fallback, and cached auto-PDF discovery from the normal lookup route. Return HTTP 410 `{"status":"retired"}` for one release from:

- `/api/career-explorer/launch-login`
- `/api/career-explorer/session`
- `/api/ensign-connect/launch-login`
- `/api/ensign-connect/session`
- `/api/ensign-connect/lookup-live`
- `/api/career-explorer/lookup`
- `/api/ensign-connect/lookup`

The manual PDF upload/parse/download endpoints remain available and must not call or publish to Student Readiness.

- [ ] **Step 5: Prove the manual PDF path stays independent**

Add a synthetic PDF/text fixture test that patches all network clients to raise, invokes only the manual upload parser, and asserts parsed data is returned without calling `lookup_ens101_projection` or any source client.

- [ ] **Step 6: Delete retired source files only after a clean dependency scan**

Run:

```bash
git grep -nE 'ensign_connect_client|login_ensign_connect|login_pathwayu_admin|pathwayu_admin_client'
```

Expected before deletion: only retired files, comments, or tests reference them. Delete the four listed files. If an unrelated active feature imports one, stop and report that exact reference instead of deleting it.

- [ ] **Step 7: Run backend tests and static source scan**

Run: `python -m unittest tests.test_readiness_routes tests.test_no_live_sources -v && python -m unittest discover -v`

Run: `git grep -nE 'lookup_student_connect|lookup_student_completion|lookup_student_report|refresh_pathwayu|force_live|lookup-live|launch-login' -- '*.py'`

Expected: tests PASS; matches exist only in explicit retired-endpoint tests or 410 route constants, never as callable source logic.

- [ ] **Step 8: Commit the backend cutover**

```bash
git add -A app.py readiness_client.py tests
git commit -m "feat: make ENS lookups Student Readiness only"
```

### Task 3: Replace the Live-Source Interface with Freshness States

**Files:**
- Modify: `static/index.html`
- Modify: `static/app.js`
- Modify: `static/styles.css`
- Create: `tests/test_readiness_ui.py`

**Interfaces:**
- Consumes: `POST /api/student-readiness/lookup` response states from Task 2.
- Produces: A single Student Readiness lookup action plus visible fresh, stale, incomplete, not-found, unavailable, and manual-PDF states.

- [ ] **Step 1: Write failing static UI assertions**

```python
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]


class ReadinessUiTests(unittest.TestCase):
    def test_live_source_controls_are_absent(self):
        html = (ROOT / "static/index.html").read_text(encoding="utf-8")
        js = (ROOT / "static/app.js").read_text(encoding="utf-8")
        forbidden = ["Check live", "Checking Ensign Connect (PeopleGrove)",
                     "/api/ensign-connect/lookup-live", "launch-login",
                     "refresh_pathwayu"]
        for value in forbidden:
            self.assertNotIn(value, html + js)

    def test_freshness_copy_and_unified_endpoint_are_present(self):
        content = (ROOT / "static/index.html").read_text(encoding="utf-8") + \
                  (ROOT / "static/app.js").read_text(encoding="utf-8")
        self.assertIn("/api/student-readiness/lookup", content)
        self.assertIn("Last updated", content)
        self.assertIn("Student Readiness", content)
```

- [ ] **Step 2: Run the focused UI tests and verify failure**

Run: `python -m unittest tests.test_readiness_ui -v`

Expected: FAIL because live controls and copy still exist.

- [ ] **Step 3: Remove source session and login UI**

Delete Career Explorer/Ensign Connect service badges, login buttons, the “Check live” control, and JavaScript session polling. Replace the main action label with `Check Student Readiness` and progress text with `Checking previously retrieved readiness data…`.

- [ ] **Step 4: Render response states without changing mentor workflow order**

For `fresh`, show a neutral “Last updated” timestamp. For `stale`, show a persistent warning: `Student Readiness data is older than 36 hours. Showing the last successful import from {timestamp}.` For `incomplete`, list only missing source/module names. For `not_found`, state that no retrieved record is available and point to the separate PDF fallback when appropriate. For 503, state that Student Readiness is temporarily unavailable and offer retry of the same endpoint only.

- [ ] **Step 5: Keep PDF upload visually and behaviorally separate**

Label it `Manual fallback: use a student-provided Career Explorer PDF`. It must not appear as an automatic second stage of the Student Readiness lookup and must not alter the displayed import timestamp.

- [ ] **Step 6: Run UI and complete tests**

Run: `python -m unittest tests.test_readiness_ui -v && python -m unittest discover -v`

Expected: all tests PASS.

- [ ] **Step 7: Commit the interface cutover**

```bash
git add static/index.html static/app.js static/styles.css tests/test_readiness_ui.py
git commit -m "feat: show Student Readiness lookup freshness"
```

### Task 4: Contract, Privacy, and Regression Verification

**Files:**
- Modify: `README.md`
- Create: `tests/test_readiness_contract.py`

**Interfaces:**
- Consumes: Deployed Student Readiness test endpoint/fixture and the completed ENS changes.
- Produces: Reproducible evidence that the apps agree on `ens101.v1` and ENS has no source-system code path.

- [ ] **Step 1: Add a contract fixture matching the deployed synthetic response**

Store a synthetic `ens101.v1` response inside the test module or `tests/fixtures/ens101_v1.json`. Assert every required field and accepted status enum. Add rejection tests for an unknown top-level contract version and missing freshness timestamp.

- [ ] **Step 2: Add a network allowlist regression test**

Patch `urllib.request.urlopen` and assert that all readiness lookup scenarios call only a URL beginning with configured `READINESS_HUB_URL`; any URL containing `peoplegrove`, `pathwayu`, or `ensign.pathwayu.com` fails the test immediately.

- [ ] **Step 3: Update README operating guidance**

Document Student Readiness as the sole source integration, the `ens101.v1` dependency, 36-hour stale behavior, manual PDF separation, and the absence of source credentials/login procedures in ENS. Include the Student Readiness outage behavior and rollback boundary.

- [ ] **Step 4: Run all tests and scans**

```bash
python -m unittest discover -v
git grep -niE 'peoplegrove|pathwayu|ensign\.pathwayu\.com|lookup-live|launch-login' -- app.py static readiness_client.py README.md
git diff --check
git status --short
```

Expected: all tests PASS; source names appear only in explanatory/manual-PDF copy, retired route responses, or negative tests—not in network targets, session checks, credentials, or live controls.

- [ ] **Step 5: Commit verification and documentation**

```bash
git add README.md tests/test_readiness_contract.py
git commit -m "test: verify cache-only readiness integration"
```

### Task 5: Deploy ENS and Return Verification Evidence

**Files:**
- Modify only if already present: `HANDOFF.md`

**Interfaces:**
- Consumes: Completed Student Readiness deployment and all ENS commits.
- Produces: Deployed ENS UI and a complete handback for independent Codex review.

- [ ] **Step 1: Run tests from a clean branch**

Run: `python -m unittest discover -v && git status --short`

Expected: all tests PASS and the worktree is clean.

- [ ] **Step 2: Deploy using the existing Mac Studio ENS procedure**

Pull the reviewed ENS branch into `/Users/robbagley/CCowork-Local-Apps/ens-101-mentor-desk`, restart only the ENS service through the existing suite script/service mechanism, and preserve the prior deploy commit for rollback.

- [ ] **Step 3: Perform synthetic live browser verification**

At `/ens101/`, confirm:

- App name is `ENS 101 Mentor Desk v1.0`.
- Main action says `Check Student Readiness`.
- No source connection/login badge or “Check live” control exists.
- A synthetic/test fixture shows the last import timestamp and fresh/stale state.
- Manual PDF fallback remains separate.
- Browser console has no new errors.
- Network evidence shows no request to PeopleGrove or PathwayU.

- [ ] **Step 4: Return the handback package**

Return repository URL, branch, commit hashes, changed/deleted files, full test output, deployment and rollback commands, synthetic API and UI evidence, and unresolved risks. Do not include student data, tokens, credentials, or private logs.

- [ ] **Step 5: Stop for independent verification**

Do not call the implementation complete. Codex will inspect commits, run the local ENS suite, review Student Readiness evidence, request corrections if necessary, and repeat live browser verification before completion is claimed.
