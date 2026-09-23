# Student Readiness Data Hub Design

**Date:** September 23, 2026  
**Status:** Approved in conversation; awaiting written-spec review  
**Primary consumers:** ENS 101, Major and Career Exploration, Resume applications, and future mentor applications

## Purpose

Make Student Readiness the only application that retrieves student data from PeopleGrove and PathwayU. Student Readiness will retain a complete normalized student record and expose versioned, app-specific projections. Consumer applications will look up already retrieved data and will never initiate a live PeopleGrove or PathwayU request.

This design reduces duplicate source integrations, protects student data through least-privilege responses, makes freshness visible, and prevents a source-system outage from blocking mentor workflows when a prior successful snapshot exists.

## Current State

- Student Readiness imports PeopleGrove data daily and stores protected student lookup keys.
- Student Readiness currently treats PathwayU as a 24-hour shared cache with an optional live refresh. It does not yet perform a complete daily PathwayU import.
- ENS 101 first consults Student Readiness for PeopleGrove data but falls back to a live PeopleGrove browser lookup.
- ENS 101 performs PathwayU lookups itself and publishes selected results back to Student Readiness.
- ENS 101 exposes source-service status, login, refresh, and live-check controls in its interface.
- ENS 101 uses detailed PathwayU results, including assessment completion, Holland-code interests, values, personality, and workplace preferences, to prepare personalized guidance.

## Goals

1. Student Readiness owns all PeopleGrove and PathwayU retrieval and source credentials.
2. Student Readiness retrieves the complete dataset required by present and anticipated mentor applications on a daily schedule.
3. Student Readiness stores one canonical normalized record for each student.
4. Each consuming application receives only an explicitly approved, versioned projection of that record.
5. Consumer applications use last-known-good records with visible freshness information and never fall back to a live source lookup.
6. A failed import cannot replace a valid prior snapshot.
7. ENS 101 retains its manual student-provided PDF workflow as an explicit, independent fallback that does not modify Student Readiness data.

## Non-Goals

- Redesigning unrelated ENS 101 mentor workflows.
- Moving AI guidance generation into Student Readiness.
- Making Student Readiness an editable system of record for PeopleGrove or PathwayU.
- Allowing consumer applications to request arbitrary fields.
- Adding an on-demand source refresh API for consumer applications.

## Architecture

### Source ownership

Student Readiness is the sole integration owner for PeopleGrove and PathwayU. It holds source credentials, runs scheduled retrieval jobs, validates results, records import history, and promotes successful snapshots.

Consumer applications must not contain source credentials, browser-automation clients, source login routes, session checks, refresh flags, or live fallback code.

### Canonical student record

Student Readiness stores a complete normalized student record keyed by the existing protected email-fingerprint/HMAC mechanism. Raw email addresses must not become database lookup keys or appear in import logs.

The canonical record must be capable of retaining:

- PeopleGrove account/readiness state and relevant timestamps.
- PathwayU completion state for all four assessments.
- Holland/RIASEC interests and codes.
- Values and core-motivation results.
- Personality and work-trait results.
- Workplace-preference/environment-fit results.
- Source-specific retrieval timestamps and import identifiers.
- Validation state, schema version, and data-quality warnings.

The stored record is private to Student Readiness. No consumer receives the entire canonical record by default.

### Versioned app projections

Student Readiness exposes a versioned projection API. The authenticated application identity determines which named projections it may request. Initial projection names are:

- `ens101.v1`
- `career-exploration.v1`
- `resume.v1`

The projection name is part of the response contract and is versioned independently from the canonical storage schema. Adding or changing a consumer does not require another source integration.

The `ens101.v1` projection includes only the PeopleGrove readiness state and PathwayU completion and detailed assessment fields required by the current ENS 101 workflow. Resume and Career Exploration projections will be defined in their own application changes and must expose only their approved fields.

### Lookup contract

A consumer sends its authenticated app identity, requested projection, and the student's institutional email to Student Readiness over the local service boundary. Student Readiness normalizes and fingerprints the email, authorizes the projection, and returns the projected record.

Every successful record response includes:

- `projection` and `projection_version`
- `record_status`
- `freshness` (`fresh` or `stale`)
- `last_successful_import_at`
- source-specific `retrieved_at` values
- projected data
- non-sensitive validation warnings

Student Readiness must not accept `refresh`, `refresh_pathwayu`, `force_live`, or equivalent consumer-controlled source-access options.

### Freshness

Data is fresh through 36 hours after the latest successful relevant import. After 36 hours, Student Readiness returns the last-known-good projected data with `freshness: "stale"` and the original timestamps. Consumer applications display a clear stale-data warning while allowing the mentor to continue.

Stale or missing data never triggers a source-system request from a consumer application.

## Daily Import Flow

1. The Student Readiness scheduler starts the PeopleGrove and PathwayU import jobs.
2. Each job writes to a staging snapshot and an import-audit record.
3. Student Readiness validates required structure, source timestamps, record counts, and projection-critical fields.
4. A valid import is promoted atomically to become the latest successful snapshot.
5. An invalid or failed import is recorded but does not replace the prior successful snapshot.
6. The canonical record is assembled from the latest successful source snapshots.
7. Projection responses are generated from the canonical record; no projection response initiates source retrieval.

The scheduler may run source imports independently so that one source failure does not discard a successful import from the other source. Freshness and warnings remain source-aware within the response.

## ENS 101 Changes

### Backend

- Replace direct PathwayU and PeopleGrove calls with one Student Readiness `ens101.v1` projection lookup.
- Remove the live PeopleGrove fallback from the normal and forced-live lookup routes.
- Remove PathwayU live lookup from the Career Explorer route.
- Remove the ENS-to-Student-Readiness PathwayU result write-back path.
- Remove or disable source login, session, and live-refresh endpoints that are no longer used.
- Remove source-client imports and credentials from the ENS runtime after confirming no other ENS feature depends on them.
- Reject an unsupported projection version rather than silently accepting partial data.
- Keep PDF parsing as a separate mentor-initiated workflow. PDF-derived data is session/application data and is not written into Student Readiness.

### Frontend

- Replace “Check Explorer & Connect” with wording that clearly describes a Student Readiness lookup.
- Remove source connection badges, source login controls, live-check controls, and “checking PeopleGrove/PathwayU live” progress messages.
- Display the record's latest successful import time and freshness state.
- Support distinct fresh, stale, incomplete, not-found, temporarily unavailable, and incompatible-schema messages.
- Keep the PDF upload option visually separate and label it as a manual fallback.

## Error Semantics

| Condition | Student Readiness behavior | Consumer behavior |
| --- | --- | --- |
| Latest import succeeds | Promote staged snapshot atomically | Use fresh projected data |
| Import fails validation or retrieval | Preserve prior snapshot and record failure | Use prior data; show stale warning when older than 36 hours |
| Record is older than 36 hours | Return data with `freshness: "stale"` | Continue workflow with visible warning |
| Student is absent | Return `not_found` without source access | Show not-found state and offer the separate manual workflow when applicable |
| Projection is unauthorized | Return HTTP 403 and audit the denial | Show configuration error; do not retry another projection |
| Student Readiness is unavailable | No source fallback | Show temporary-unavailability state and allow retry of Student Readiness only |
| Projection version is incompatible | Return or surface an explicit version error | Stop use of the response and show configuration error |
| One source is unavailable | Return available projected data with source-aware completeness warnings | Show incomplete state without attempting source access |

Errors and audit records must not expose raw email addresses, source credentials, assessment details, or other unnecessary student information.

## Security and Privacy

- Use the existing protected email fingerprint/HMAC lookup design.
- Authenticate each consuming application separately.
- Authorize named projections per app identity.
- Return the minimum fields required by the requested projection.
- Keep source credentials only in Student Readiness.
- Do not log raw lookup payloads or full projected student records.
- Record projection name, app identity, outcome, timestamps, and non-sensitive diagnostic codes for auditing.
- Keep the service local/private; this design does not authorize public Internet exposure.

## Migration and Deployment

1. Implement and test Student Readiness canonical storage, daily PathwayU import, and `ens101.v1` projection without changing the current ENS production path.
2. Backfill or perform the first complete PathwayU import and verify record completeness.
3. Deploy the Student Readiness projection API and confirm it returns fresh and stale fixtures correctly.
4. Update ENS 101 to use only `ens101.v1`.
5. Remove ENS source controls and fallback code after contract tests pass.
6. Deploy ENS 101 and perform browser verification on the Mac Studio/Tailscale installation.
7. Remove retired ENS source secrets and automation dependencies only after verifying rollback is not required.

During migration, the deployment must not create a state in which a newly modified ENS instance can silently return to live source access. If Student Readiness is not ready, keep the prior ENS deployment rather than deploying an incomplete cache-only client.

## Testing and Verification

### Student Readiness automated tests

- Successful imports promote staged data atomically.
- Failed imports preserve the prior successful snapshot.
- Freshness changes to stale after 36 hours without discarding data.
- Projection authorization prevents cross-app or arbitrary-field access.
- `ens101.v1` contains the required assessment and readiness fields and excludes unapproved fields.
- Lookup routes never invoke source retrieval code.
- Source-aware partial-data warnings are stable and documented.
- Logs and errors do not contain raw student emails or record contents.

### ENS 101 automated tests

- The standard lookup makes only a Student Readiness request.
- Not-found, stale, incomplete, unavailable, and incompatible-version responses never call PeopleGrove or PathwayU.
- No force-live or refresh flag can be supplied through the ENS API or interface.
- The PDF workflow remains independent and does not write to Student Readiness.
- Removed session/login/live endpoints return the agreed retired-endpoint response or no longer exist.
- UI tests confirm removal of source login, session, and live-check controls.
- UI tests confirm display of Student Readiness timestamps and freshness.

### Final live verification

- Inspect the deployed ENS interface for removed source controls and updated wording.
- Complete a lookup using known test data and verify the displayed freshness timestamp matches Student Readiness.
- Verify stale and unavailable states using controlled fixtures or a non-production test mode.
- Review network activity to confirm ENS communicates with Student Readiness and does not contact PeopleGrove or PathwayU.
- Confirm the PDF manual fallback still functions separately.

No real student names, emails, or assessment results may be included in screenshots, test fixtures, logs, commits, or handoff messages.

## Coding Handoff and Review Responsibilities

Rob's Coding Helper will implement the Student Readiness and ENS changes in the repositories and Mac Studio environment it can access. Its handback must include:

- repository and branch names
- commit hashes
- changed-file list
- schema and endpoint contract
- test commands and complete results
- migration and deployment commands
- confirmation that no student data was committed
- unresolved risks or manual steps

Codex will monitor the handoff using GPT-5.6 Sol at medium reasoning, raising effort for final cross-app review when available. Codex will inspect the returned changes, run the locally available ENS tests, review Student Readiness evidence, send correction requests when required, and perform final browser verification against the deployed Mac Studio applications.

Implementation is complete only when automated tests pass, the live ENS interface no longer exposes source-system controls, and runtime/network evidence confirms that consumer lookups cannot contact PeopleGrove or PathwayU.

