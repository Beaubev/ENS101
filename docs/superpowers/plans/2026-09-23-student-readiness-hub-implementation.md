# Student Readiness Hub Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make Student Readiness the sole daily PeopleGrove and PathwayU ingestion service and expose authenticated, versioned, app-specific projections from last-known-good data.

**Architecture:** The existing Python service on `127.0.0.1:5055` keeps its current PeopleGrove import but adds a staged PathwayU bulk import, canonical SQLite records, and an app-authorized projection API. Imports are validated before an atomic database transaction promotes them; lookup routes are read-only and cannot invoke source retrieval.

**Tech Stack:** Python 3, stdlib `http.server`, SQLite, existing shared PathwayU client/export capability, macOS Keychain, LaunchAgent, `unittest` or the repository's confirmed test runner.

**Spec:** `docs/superpowers/specs/2026-09-23-student-readiness-data-hub-design.md`

## Global Constraints

- Work only in `/Users/robbagley/CCowork-Local-Apps/ensign-student-readiness-hub` until the repository preflight confirms the checkout and branch.
- Never commit or print raw student email, name, student ID, assessment content, credentials, API rows, or source HTML.
- Preserve HMAC email fingerprints as the canonical student key.
- Student Readiness is the only process allowed to contact PeopleGrove or PathwayU.
- Lookup requests must never accept or honor `refresh`, `refresh_pathwayu`, `force_live`, or equivalent flags.
- Data is `fresh` for 36 hours after the relevant successful import and `stale` afterward; stale records remain usable.
- Failed or incomplete imports must not replace last-known-good records.
- The service remains private to the Mac Studio/Tailnet and binds to `127.0.0.1:5055` behind the existing gateway.
- Use synthetic fixtures only.
- Do not deploy until the complete PathwayU bulk-export contract is confirmed and the Student Readiness plan tests pass.

## Review Focus

- A malformed or partially downloaded source export must fail validation and leave the prior snapshot byte-for-byte usable; Task 2 adds this test.
- Email normalization must produce the same HMAC fingerprint for case and surrounding-space variants; Task 1 adds this test.
- A valid app token requesting another app's projection must receive HTTP 403 without projected data; Task 4 adds this test.
- A record with PeopleGrove data but missing PathwayU data must return an explicit incomplete warning without a live lookup; Task 4 adds this test.
- A daily run overlapping another PathwayU browser/profile process must exit safely without corrupting the active snapshot; Task 3 adds this test.

---

### Task 1: Verify the Checkout and Add the Canonical Schema

**Files:**
- Inspect: `/Users/robbagley/CCowork-Local-Apps/ensign-student-readiness-hub/.git/config`
- Inspect: `/Users/robbagley/CCowork-Local-Apps/ensign-student-readiness-hub/app.py`
- Create: `/Users/robbagley/CCowork-Local-Apps/ensign-student-readiness-hub/readiness_hub/__init__.py`
- Create: `/Users/robbagley/CCowork-Local-Apps/ensign-student-readiness-hub/readiness_hub/schema.py`
- Create: `/Users/robbagley/CCowork-Local-Apps/ensign-student-readiness-hub/tests/test_schema.py`

**Interfaces:**
- Consumes: Existing `readiness.sqlite3` connection and existing email HMAC key.
- Produces: `ensure_schema_v2(connection) -> None`, `normalize_email(email) -> str`, and `fingerprint_email(email, key) -> str`.

- [ ] **Step 1: Run the fail-fast repository preflight**

```bash
cd /Users/robbagley/CCowork-Local-Apps/ensign-student-readiness-hub
pwd
git remote -v
git branch --show-current
git log --oneline -1
git status --short
find . -maxdepth 3 -type f -not -path './.git/*' -not -path './venv/*' | sort
```

Expected: the checkout path is exact, the active branch and remote are reported in the handback, and `app.py` is present. If the path is absent, the tree is dirty in overlapping files, or the repository has no recoverable Git history, stop and report the evidence before editing.

- [ ] **Step 2: Write failing normalization and schema tests**

```python
import hashlib
import hmac
import sqlite3
import unittest

from readiness_hub.schema import ensure_schema_v2, fingerprint_email


class SchemaTests(unittest.TestCase):
    def test_email_fingerprint_normalizes_case_and_whitespace(self):
        key = b"k" * 32
        expected = hmac.new(key, b"student@ensign.edu", hashlib.sha256).hexdigest()
        self.assertEqual(fingerprint_email(" Student@Ensign.EDU ", key), expected)

    def test_schema_v2_creates_canonical_and_import_tables(self):
        db = sqlite3.connect(":memory:")
        ensure_schema_v2(db)
        tables = {row[0] for row in db.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        self.assertTrue({"student_readiness_v2", "source_imports_v2"}.issubset(tables))


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 3: Run the tests and confirm they fail for the missing module**

Run: `python -m unittest tests.test_schema -v`

Expected: FAIL with `ModuleNotFoundError: No module named 'readiness_hub'`.

- [ ] **Step 4: Implement the schema module**

```python
import hashlib
import hmac
import sqlite3

SCHEMA_VERSION = 2


def normalize_email(email: str) -> str:
    return email.strip().lower()


def fingerprint_email(email: str, key: bytes) -> str:
    if len(key) != 32:
        raise ValueError("fingerprint key must be exactly 32 bytes")
    return hmac.new(key, normalize_email(email).encode("utf-8"), hashlib.sha256).hexdigest()


def ensure_schema_v2(connection: sqlite3.Connection) -> None:
    connection.executescript("""
    CREATE TABLE IF NOT EXISTS source_imports_v2 (
        id INTEGER PRIMARY KEY,
        source TEXT NOT NULL CHECK(source IN ('peoplegrove', 'pathwayu')),
        started_at TEXT NOT NULL,
        completed_at TEXT,
        status TEXT NOT NULL CHECK(status IN ('running', 'succeeded', 'failed')),
        record_count INTEGER NOT NULL DEFAULT 0,
        error_code TEXT
    );
    CREATE TABLE IF NOT EXISTS student_readiness_v2 (
        fingerprint TEXT PRIMARY KEY,
        peoplegrove_json TEXT,
        pathwayu_json TEXT,
        peoplegrove_retrieved_at TEXT,
        pathwayu_retrieved_at TEXT,
        schema_version INTEGER NOT NULL DEFAULT 2,
        updated_at TEXT NOT NULL
    );
    """)
    connection.commit()
```

- [ ] **Step 5: Run the focused test and the existing suite**

Run: `python -m unittest tests.test_schema -v && python -m unittest discover -v`

Expected: all tests PASS and no existing table is dropped or rewritten.

- [ ] **Step 6: Commit the schema**

```bash
git add readiness_hub/__init__.py readiness_hub/schema.py tests/test_schema.py
git commit -m "feat: add canonical readiness schema"
```

### Task 2: Add Staged Validation and Atomic Promotion

**Files:**
- Create: `/Users/robbagley/CCowork-Local-Apps/ensign-student-readiness-hub/readiness_hub/import_pipeline.py`
- Create: `/Users/robbagley/CCowork-Local-Apps/ensign-student-readiness-hub/tests/test_import_pipeline.py`

**Interfaces:**
- Consumes: `ensure_schema_v2(connection)` and normalized source rows keyed by `fingerprint`.
- Produces: `validate_rows(source, rows) -> None` and `promote_rows(connection, source, rows, retrieved_at) -> int`.

- [ ] **Step 1: Write failing validation and rollback tests**

```python
import json
import sqlite3
import unittest

from readiness_hub.import_pipeline import ImportValidationError, promote_rows
from readiness_hub.schema import ensure_schema_v2


class ImportPipelineTests(unittest.TestCase):
    def setUp(self):
        self.db = sqlite3.connect(":memory:")
        ensure_schema_v2(self.db)

    def test_malformed_pathwayu_row_preserves_last_known_good(self):
        good = [{"fingerprint": "a" * 64, "status": "complete", "completed_count": 4,
                 "total": 4, "assessments": {"interests": {}, "values": {},
                 "personality": {}, "workplace_preferences": {}}}]
        promote_rows(self.db, "pathwayu", good, "2026-09-23T09:00:00Z")
        before = self.db.execute(
            "SELECT pathwayu_json, pathwayu_retrieved_at FROM student_readiness_v2 WHERE fingerprint=?",
            ("a" * 64,),
        ).fetchone()
        with self.assertRaises(ImportValidationError):
            promote_rows(self.db, "pathwayu", [{"fingerprint": "bad"}], "2026-09-24T09:00:00Z")
        after = self.db.execute(
            "SELECT pathwayu_json, pathwayu_retrieved_at FROM student_readiness_v2 WHERE fingerprint=?",
            ("a" * 64,),
        ).fetchone()
        self.assertEqual(after, before)

    def test_duplicate_fingerprint_rejects_entire_batch(self):
        row = {"fingerprint": "b" * 64, "status": "not_found", "completed_count": 0,
               "total": 4, "assessments": {}}
        with self.assertRaises(ImportValidationError):
            promote_rows(self.db, "pathwayu", [row, dict(row)], "2026-09-23T09:00:00Z")
```

- [ ] **Step 2: Run the focused test and verify failure**

Run: `python -m unittest tests.test_import_pipeline -v`

Expected: FAIL because `readiness_hub.import_pipeline` does not exist.

- [ ] **Step 3: Implement full-batch validation before a transaction**

Implement `validate_rows` so it rejects a non-list batch, a non-64-character lowercase hex fingerprint, duplicate fingerprints, unknown source names, invalid status values, a PathwayU total other than `4`, or missing `assessments` for a complete PathwayU record. Implement `promote_rows` so validation finishes before `BEGIN IMMEDIATE`, rows are serialized with `json.dumps(..., sort_keys=True, separators=(",", ":"))`, and any exception rolls back the whole batch.

```python
class ImportValidationError(ValueError):
    pass


def promote_rows(connection, source, rows, retrieved_at):
    validate_rows(source, rows)
    column = f"{source}_json"
    retrieved_column = f"{source}_retrieved_at"
    with connection:
        for row in rows:
            connection.execute(
                f"""INSERT INTO student_readiness_v2
                    (fingerprint, {column}, {retrieved_column}, updated_at)
                    VALUES (?, ?, ?, ?)
                    ON CONFLICT(fingerprint) DO UPDATE SET
                    {column}=excluded.{column},
                    {retrieved_column}=excluded.{retrieved_column},
                    updated_at=excluded.updated_at""",
                (row["fingerprint"], canonical_json(row), retrieved_at, retrieved_at),
            )
    return len(rows)
```

Define the serializer used above in the same module:

```python
def canonical_json(value: dict) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
```

- [ ] **Step 4: Run the import tests and complete suite**

Run: `python -m unittest tests.test_import_pipeline -v && python -m unittest discover -v`

Expected: all tests PASS.

- [ ] **Step 5: Commit the import pipeline**

```bash
git add readiness_hub/import_pipeline.py tests/test_import_pipeline.py
git commit -m "feat: promote validated readiness imports atomically"
```

### Task 3: Add the Daily PathwayU Bulk Import Gate and Scheduler Entry Point

**Files:**
- Create: `/Users/robbagley/CCowork-Local-Apps/ensign-student-readiness-hub/readiness_hub/pathwayu_import.py`
- Create: `/Users/robbagley/CCowork-Local-Apps/ensign-student-readiness-hub/scripts/refresh_readiness.py`
- Create: `/Users/robbagley/CCowork-Local-Apps/ensign-student-readiness-hub/tests/test_pathwayu_import.py`
- Create: `/Users/robbagley/CCowork-Local-Apps/ensign-student-readiness-hub/tests/fixtures/pathwayu_complete.json`
- Create: `/Users/robbagley/CCowork-Local-Apps/ensign-student-readiness-hub/config/com.rob.ensign-student-readiness-refresh.plist`

**Interfaces:**
- Consumes: A confirmed PathwayU admin bulk export/API that returns all four assessment details for the daily population; `promote_rows` from Task 2.
- Produces: `fetch_pathwayu_export(source_client) -> list[dict]`, `run_pathwayu_import(...) -> ImportResult`, and `scripts/refresh_readiness.py --source pathwayu|peoplegrove|all`.

- [ ] **Step 1: Prove the source contract before writing importer code**

In the Mac Studio checkout notes, record the official admin export/API operation, its source file/function, pagination behavior, rate limits, and a redacted field list. The contract must provide all four modules' completion and detailed results for the daily population without performing 3,000+ interactive browser searches.

Expected: a reproducible export/API contract. If PathwayU offers only single-student browser lookup, stop this task and report `BLOCKED_PATHWAYU_BULK_EXPORT`; do not substitute a loop over `lookup_student_report` or deploy the ENS cache-only change.

- [ ] **Step 2: Write failing bulk-import and lock tests**

```python
import unittest

from readiness_hub.pathwayu_import import ImportAlreadyRunning, run_pathwayu_import


class FakeSource:
    def fetch_all(self):
        return [{"email": "synthetic@ensign.edu", "status": "complete",
                 "completed_count": 4, "total": 4,
                 "assessments": {"interests": {}, "values": {},
                 "personality": {}, "workplace_preferences": {}}}]


class PathwayUImportTests(unittest.TestCase):
    def test_import_fingerprints_then_discards_email(self):
        captured = []
        result = run_pathwayu_import(FakeSource(), b"k" * 32, captured.extend,
                                     now=lambda: "2026-09-23T09:00:00Z")
        self.assertEqual(result.record_count, 1)
        self.assertNotIn("email", captured[0])
        self.assertEqual(len(captured[0]["fingerprint"]), 64)

    def test_existing_lock_prevents_overlapping_profile_use(self):
        with self.assertRaises(ImportAlreadyRunning):
            run_pathwayu_import(FakeSource(), b"k" * 32, lambda rows: None,
                                lock_held=lambda: True)
```

- [ ] **Step 3: Run the focused test and verify failure**

Run: `python -m unittest tests.test_pathwayu_import -v`

Expected: FAIL because `readiness_hub.pathwayu_import` does not exist.

- [ ] **Step 4: Implement the importer without retaining raw email**

The importer must validate the full export, fingerprint each normalized email in memory, remove `email` before passing rows to persistence, acquire a non-blocking file lock under `~/Library/Application Support/Ensign Student Readiness Hub/`, and release the lock in `finally`. It must record a failed `source_imports_v2` row with a non-sensitive error code on failure.

```python
from dataclasses import dataclass


@dataclass(frozen=True)
class ImportResult:
    source: str
    record_count: int
    retrieved_at: str


class ImportAlreadyRunning(RuntimeError):
    pass
```

- [ ] **Step 5: Add a scheduler entry point and checked-in LaunchAgent template**

`scripts/refresh_readiness.py` must return exit code `0` only when requested imports succeed, `75` when another import owns the lock, and nonzero for validation/source failures. The plist template must run `--source all` daily at `04:15`, use absolute paths, and send stdout/stderr to local Application Support logs that are excluded from Git.

Create `tests/fixtures/pathwayu_complete.json` with one synthetic record:

```json
[{"email":"synthetic@ensign.edu","status":"complete","completed_count":4,"total":4,"assessments":{"interests":{},"values":{},"personality":{},"workplace_preferences":{}}}]
```

- [ ] **Step 6: Run tests and a synthetic dry run**

Run: `python -m unittest tests.test_pathwayu_import -v && python -m unittest discover -v`

Run: `python scripts/refresh_readiness.py --source pathwayu --fixture tests/fixtures/pathwayu_complete.json --dry-run`

Expected: PASS; the dry run reports counts and validation status only, never emails or assessment content.

- [ ] **Step 7: Commit the importer and scheduler**

```bash
git add readiness_hub/pathwayu_import.py scripts/refresh_readiness.py tests/test_pathwayu_import.py tests/fixtures/pathwayu_complete.json config/com.rob.ensign-student-readiness-refresh.plist
git commit -m "feat: add validated daily PathwayU import"
```

### Task 4: Add Authenticated Versioned Projections

**Files:**
- Create: `/Users/robbagley/CCowork-Local-Apps/ensign-student-readiness-hub/readiness_hub/projections.py`
- Create: `/Users/robbagley/CCowork-Local-Apps/ensign-student-readiness-hub/tests/test_projections.py`
- Modify: `/Users/robbagley/CCowork-Local-Apps/ensign-student-readiness-hub/app.py`

**Interfaces:**
- Consumes: `student_readiness_v2`, the existing `X-Readiness-Token` mechanism, and the existing fingerprint key.
- Produces: `projection_lookup_response(app_id, projection, email, store, now) -> tuple[int, dict]` and `POST /api/v1/projections/ens101.v1/lookup` with request `{"email":"synthetic@ensign.edu"}`.

- [ ] **Step 1: Write failing projection and authorization tests**

```python
import unittest
from readiness_hub.projections import (
    ProjectionForbidden,
    build_projection,
    projection_lookup_response,
)


class ProjectionTests(unittest.TestCase):
    def test_ens101_projection_excludes_unapproved_fields(self):
        record = {
            "peoplegrove": {"status": "current", "retrieved_at": "2026-09-23T09:00:00Z"},
            "pathwayu": {"status": "complete", "completed_count": 4, "total": 4,
                         "assessments": {"interests": {}, "values": {},
                         "personality": {}, "workplace_preferences": {}},
            "private_note": "must-not-leak",
        }
        result = build_projection("ens101", "ens101.v1", record,
                                  now="2026-09-23T10:00:00Z")
        self.assertEqual(result["projection"], "ens101.v1")
        self.assertNotIn("private_note", str(result))

    def test_cross_app_projection_is_forbidden(self):
        with self.assertRaises(ProjectionForbidden):
            build_projection("resume", "ens101.v1", {}, now="2026-09-23T10:00:00Z")

    def test_missing_pathwayu_is_incomplete_and_never_refreshes(self):
        result = build_projection("ens101", "ens101.v1",
                                  {"peoplegrove": {"status": "current"}},
                                  now="2026-09-23T10:00:00Z")
        self.assertEqual(result["record_status"], "incomplete")
        self.assertNotIn("refresh", str(result).lower())

    def test_lookup_never_calls_a_source_client(self):
        class Store:
            def get_by_email(self, email):
                return {"peoplegrove": {"status": "current"}}
        status, body = projection_lookup_response(
            "ens101", "ens101.v1", "synthetic@ensign.edu", Store(),
            now="2026-09-23T10:00:00Z",
        )
        self.assertEqual(status, 200)
        self.assertEqual(body["record_status"], "incomplete")
```

- [ ] **Step 2: Run the tests and verify failure**

Run: `python -m unittest tests.test_projections -v`

Expected: FAIL because `readiness_hub.projections` does not exist.

- [ ] **Step 3: Implement the explicit projection allowlist**

```python
PROJECTION_ACCESS = {
    "ens101": {"ens101.v1"},
    "career-exploration": {"career-exploration.v1"},
    "resume": {"resume.v1"},
}

ENS101_PATHWAYU_FIELDS = {
    "status", "completed_count", "total", "missing", "assessments", "retrieved_at"
}


class ProjectionForbidden(PermissionError):
    pass
```

`build_projection` must copy only allowlisted keys, calculate freshness from the oldest required source timestamp, set `record_status` to `complete`, `incomplete`, or `not_found`, and include `projection`, `projection_version`, `freshness`, `last_successful_import_at`, source timestamps, and non-sensitive warnings.

- [ ] **Step 4: Route the projection endpoint in `app.py`**

Authenticate `X-Readiness-Token`, map the token to an app identity without logging the token, reject unauthorized projection access with HTTP 403, validate `@ensign.edu` email, fingerprint it, read the canonical record, and call `build_projection`. Explicitly reject request keys named `refresh`, `refresh_pathwayu`, or `force_live` with HTTP 400.

- [ ] **Step 5: Add response-level and route-level tests**

Test `projection_lookup_response` directly for 200 fresh, 200 stale, 200 incomplete, 404 not found, 403 cross-app projection, and 409 incompatible version. At the handler boundary, add requests for 400 refresh flag and 401 unknown token. The route body must contain only parsing/authentication plus this call:

```python
status, payload = projection_lookup_response(
    authenticated_app_id,
    requested_projection,
    request_json["email"],
    canonical_store,
    now=utc_now_iso(),
)
self._json(payload, status)
```

Monkeypatch every source client to raise if invoked and assert each response still completes from the database.

- [ ] **Step 6: Run the API and complete suites**

Run: `python -m unittest tests.test_projections -v && python -m unittest discover -v`

Expected: all tests PASS; source-client spies have zero calls.

- [ ] **Step 7: Commit the projection API**

```bash
git add readiness_hub/projections.py tests/test_projections.py app.py
git commit -m "feat: expose authorized readiness projections"
```

### Task 5: Retire Consumer-Triggered PathwayU Writes and Update Data Sources UI

**Files:**
- Modify: `/Users/robbagley/CCowork-Local-Apps/ensign-student-readiness-hub/app.py`
- Modify: `/Users/robbagley/CCowork-Local-Apps/ensign-student-readiness-hub/static/app.js`
- Modify: `/Users/robbagley/CCowork-Local-Apps/ensign-student-readiness-hub/static/index.html`
- Create: `/Users/robbagley/CCowork-Local-Apps/ensign-student-readiness-hub/tests/test_retired_live_routes.py`

**Interfaces:**
- Consumes: Projection API and daily import status from Tasks 3–4.
- Produces: Cache-only lookup UI, import-health display, and retired `/api/v1/pathwayu-result` write behavior.

- [ ] **Step 1: Write failing route-retirement tests**

Add tests asserting `POST /api/v1/pathwayu-result` returns HTTP 410 with `{"status":"retired"}` and does not change SQLite; `POST /api/v1/lookup` rejects `refresh_pathwayu: true`; and no public route invokes the shared PathwayU client.

```python
def test_pathwayu_writeback_is_retired(self):
    before = canonical_row_count(self.db)
    status, body = dispatch_api_for_test(
        "POST", "/api/v1/pathwayu-result",
        {"email": "synthetic@ensign.edu", "status": "complete"},
    )
    self.assertEqual((status, body), (410, {"status": "retired"}))
    self.assertEqual(canonical_row_count(self.db), before)

def test_lookup_rejects_refresh_flag(self):
    status, body = dispatch_api_for_test(
        "POST", "/api/v1/lookup",
        {"email": "synthetic@ensign.edu", "refresh_pathwayu": True},
    )
    self.assertEqual(status, 400)
    self.assertEqual(body["status"], "invalid_request")
```

If the current app has no test dispatcher, extract only its path/body decision logic into `dispatch_api_for_test(method, path, body) -> tuple[int, dict]` in `app.py`; the HTTP handler must delegate to it so these tests exercise production routing.

- [ ] **Step 2: Run the focused test and verify it fails**

Run: `python -m unittest tests.test_retired_live_routes -v`

Expected: FAIL because the current route still accepts consumer write-back or refresh.

- [ ] **Step 3: Retire write-back and refresh semantics**

Return HTTP 410 for `/api/v1/pathwayu-result` during one compatibility release. Keep `/api/v1/lookup` cache-only for existing consumers, ignore no fields silently, and return HTTP 400 if any live-refresh field is supplied.

- [ ] **Step 4: Update the Data Sources page**

Replace “Shared cache + Live lookup” with “Daily managed import.” Remove the PathwayU live-refresh button and source-login controls. Show latest successful import time, record count, source state, and failure code without student data. Show that stale begins after 36 hours.

- [ ] **Step 5: Add static-content assertions**

Assert `static/index.html` and `static/app.js` do not contain `refresh_pathwayu`, `live lookup`, or the retired route as an active fetch target, and do contain `Daily managed import` and `36 hours`.

- [ ] **Step 6: Run all tests**

Run: `python -m unittest discover -v`

Expected: all tests PASS.

- [ ] **Step 7: Commit route retirement and UI status**

```bash
git add app.py static/app.js static/index.html tests/test_retired_live_routes.py
git commit -m "feat: make readiness lookups cache only"
```

### Task 6: Verify, Deploy Student Readiness First, and Hand Back Evidence

**Files:**
- Modify: `/Users/robbagley/CCowork-Local-Apps/ensign-student-readiness-hub/HANDOFF.md`
- Modify: `/Users/robbagley/CCowork-Local-Apps/ensign-student-readiness-hub/PROGRESS.md`

**Interfaces:**
- Consumes: All Student Readiness tasks.
- Produces: A deployed, tested projection service and a handback package that gates the ENS plan.

- [ ] **Step 1: Run the full automated suite from a clean checkout state**

Run: `python -m unittest discover -v`

Expected: all tests PASS with zero real student data printed.

- [ ] **Step 2: Run privacy and source-call scans**

```bash
git grep -nE 'refresh_pathwayu|force_live|/api/v1/pathwayu-result'
git grep -nE '@ensign\.edu' -- ':!tests/fixtures/*' ':!tests/*'
git status --short
```

Expected: live-control strings exist only in rejection/retirement tests; no real addresses or generated data files are tracked; worktree is clean.

- [ ] **Step 3: Run a synthetic projection smoke test**

Use a temporary test database and token to call `POST /api/v1/projections/ens101.v1/lookup`. Confirm fresh, stale, incomplete, unauthorized, and unavailable fixtures; do not use a real student.

- [ ] **Step 4: Install the checked-in LaunchAgent template and run one supervised import**

Copy the reviewed plist template to `~/Library/LaunchAgents/com.rob.ensign-student-readiness-refresh.plist`, load it with the existing Mac deployment procedure, and run one supervised daily import. This step is permitted only after the PathwayU bulk contract gate and all tests pass.

- [ ] **Step 5: Deploy Student Readiness and verify the live API/UI**

Verify `/readiness-hub/` reports “Daily managed import,” has no PathwayU refresh/login action, and the synthetic/test-mode projection response includes `ens101.v1`, timestamps, and freshness. Do not query a real student for deployment proof.

- [ ] **Step 6: Update handoff files and commit**

Record repository URL, branch, commit hashes, changed files, test output, import result counts, projection contract, deployment commands, and unresolved risks. Exclude credentials and student data.

```bash
git add HANDOFF.md PROGRESS.md
git commit -m "docs: record readiness projection deployment"
```

- [ ] **Step 7: Return the ENS integration gate evidence**

Hand back: remote URL, branch, all commit hashes, full test output, live import timestamp, projection sample using synthetic values, proof that lookup requests made zero source-client calls, and rollback command. ENS implementation must not begin until this evidence is reviewed.
