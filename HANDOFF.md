# Handoff: ENS 101 → Student Readiness cutover

**For:** Rob Bagley (Mac Studio deployment)
**From:** Rodrigo Mollocondo
**Date:** 2026-09-29
**Status:** Merged to `main` (PR #1, merge `2687df0`). **Not deployed.** Do not deploy until Part 1 passes.

## What changed

ENS 101 no longer contacts PeopleGrove or Career Explorer (PathwayU). It reads
student readiness from one place: the Student Readiness Hub `ens101.v1`
projection on the same Mac.

```
Mentor browser ──► ENS 101 (/api/student-readiness/lookup)
                      └──► Hub  POST http://127.0.0.1:5055/api/v1/projections/ens101.v1/lookup
                                 (X-Readiness-Token, email only, cache-only, no live source calls)
```

| Commit | Change |
|---|---|
| `c1ff8a9` | Plan Task 1 aligned with the deployed `ens101.v1` contract |
| `4e044cd` | `readiness_client.py`: strict client, validates every response field |
| `459c1df` | New route `/api/student-readiness/lookup`; live source routes retired (410) |
| `31f662f` | Optional `READINESS_CONSUMER_TOKEN_PATH` override |
| `b39efa0` | UI: one "Check Student Readiness" action with fresh / stale / incomplete / not-found / unavailable states |

**Removed from ENS:** `ensign_connect_client.py`, `login_ensign_connect.py`,
`login_pathwayu_admin.py`, `pathwayu_admin_client.py`,
`pathwayu_admin_client.py.local-replaced-by-shared`, the OneDrive snapshot
fallback, publishing results back to the Hub, and the "Check live" / "Authenticate" controls.

**Retired endpoints (return `410 {"status":"retired"}`):**
`/api/career-explorer/{session,admin-status,launch-login,lookup}` and
`/api/ensign-connect/{session,admin-status,launch-login,lookup,lookup-live}`.

**Kept:** the manual Career Explorer PDF upload (parsed locally, never sent to the Hub).

## Part 1: Hub gate (must pass before deploying ENS)

If ENS is deployed before these pass, mentors see **"temporarily unavailable"**
(A1 or A3) or **every student as "Incomplete: Career Explorer record"** (A2).

**A1. The running Hub serves `ens101.v1`.** On the Mac Studio:

```bash
curl -s -o /dev/null -w "%{http_code}\n" -X POST http://127.0.0.1:5055/api/v1/projections/ens101.v1/lookup
```

`401` = ready (endpoint exists, no token sent). `404` = the Hub needs `git pull` and a restart.

**A2. Career Explorer nightly import is installed and has run for a few nights.**
Follow "Nightly Career Explorer download" in the Hub `README.md` (venv with
Playwright, `career_explorer_download.py --login`, test run, install the 04:10 AM
LaunchAgent). Then confirm both sources imported recently:

```bash
cd <hub folder> && python3 app.py --sources
```

Both PeopleGrove and Career Explorer need a successful import within the last
36 hours; otherwise every lookup shows a stale warning.

**A3. ENS can read the consumer token.** ENS reads
`~/Library/Application Support/Ensign Student Readiness Hub/consumer-token`
from the home folder of the user that runs ENS. If ENS runs as the same macOS
user as the Hub, nothing to do. Otherwise add to ENS `.env`:

```
READINESS_CONSUMER_TOKEN_PATH=/Users/<hub user>/Library/Application Support/Ensign Student Readiness Hub/consumer-token
```

`READINESS_HUB_URL` defaults to `http://127.0.0.1:5055` and needs no change.

## Part 2: Deploy ENS

```bash
cd /Users/robbagley/CCowork-Local-Apps/ens-101-mentor-desk
git status                                   # must be clean (see warning)
git rev-parse HEAD > ~/ens101-rollback-commit.txt
git pull origin main
python3 -m unittest discover                 # expect: Ran 48 tests ... OK
```

Then restart **only** the ENS service with the existing suite script or service mechanism.

> **Warning:** this deploy deletes `pathwayu_admin_client.py`. If that file was
> replaced locally on the Mac Studio (the repo had a
> `pathwayu_admin_client.py.local-replaced-by-shared` backup), `git pull` stops with
> "local changes would be overwritten". ENS no longer imports it, so it is safe to
> remove the local copy (`git checkout -- pathwayu_admin_client.py`) and pull again.
> The Hub uses its own shared copy and is not affected.

## Part 3: Verify

1. From the ENS folder, test the token and Hub connection (prints only the status):
   ```bash
   python3 -c "from readiness_client import lookup_ens101_projection as l; print(l('<a staff test @ensign.edu email>')['record_status'])"
   ```
   Any of `complete`, `incomplete`, or `not_found` means ENS reached the Hub. `ReadinessConfigError` means fix A3.
2. At `https://mac-studio-2.tail299fc7.ts.net/ens101/`:
   - The main button reads **Check Student Readiness**; no "Check live" or "Authenticate" controls.
   - Look up a consenting staff or student test account (Rodrigo volunteered his own `@ensign.edu` address). Expect "Last updated …", the Ensign Connect status, and Career Explorer cards; personality shows as scores out of 5.
   - Browser console shows no new errors.
3. `curl -s http://127.0.0.1:5050/api/status` includes `"readiness_source": "Student Readiness ens101.v1"`.

## Rollback

```bash
cd /Users/robbagley/CCowork-Local-Apps/ens-101-mentor-desk
git checkout "$(cat ~/ens101-rollback-commit.txt)"
```

Then restart ENS. The Hub needs no rollback; its `/api/v1/lookup` and
`/api/v1/pathwayu-result` compatibility routes are unchanged.

## Evidence

- ENS test suite: 48 tests pass (client contract, route mapping, retired
  endpoints, no source modules loaded, manual PDF stays local, UI copy).
- End to end on 2026-09-28: the real Hub code (sandboxed data directory,
  synthetic PeopleGrove and Career Explorer exports loaded with the Hub's own
  `--import-peoplegrove` / `--import-career-explorer`) behind ENS. Results:
  `complete` 200, three `incomplete` variants 200, `not_found` 404; a wrong token
  is rejected with 401; the Hub received only `ens101.v1` lookups. The UI was
  checked in a browser with the synthetic complete record.

## Known issues (not blockers for this deploy)

1. **Personality guidance wording.** The Hub sends 1–5 scores. The guidance
   engine needs level words (high / moderate / low), so personality paragraphs
   stay generic until the Hub adds a level per trait. Needs official PathwayU cutoffs.
2. **Hub staff screen.** `/api/lookup` still uses the legacy Career Explorer path
   (cache plus live Playwright lookup), not `career_explorer_records`, so it can show
   "unavailable" while ENS shows full data.
3. **Report download privacy.** `/api/career-explorer/download-report` falls back
   to the most recent PDF of *any* student when no match is found. The UI no
   longer calls it without a stored link, but the server fallback should be removed.
4. **Old cached emails.** The ENS `feedback.db` table `ensign_connect_cache` still
   holds emails and results from the old lookups and is no longer read. Delete once
   approved.
5. **"Local only" behind the proxy.** ENS and Hub loopback checks pass every
   request that arrives through a reverse proxy on the same Mac, so they
   effectively allow anyone on the tailnet.
6. **Plan Task 4** (README update and contract regression test) is still open.
