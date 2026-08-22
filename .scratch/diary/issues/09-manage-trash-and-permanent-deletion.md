# 09 — Manage Trash and permanent deletion

**What to build:** Give the owner a recoverable deletion path and a separate deliberate destruction path. Trashed Entries leave normal Diary use immediately, can be restored, and remain indefinitely until the owner confirms permanent deletion.

**Blocked by:** 05 — Navigate history with a calendar; 07 — Restore a historical Entry Revision; 08 — Change Entry Time and regroup history.

**Status:** ready-for-agent

- [x] Moving an Entry to Trash is distinct from permanent deletion and removes it from history and calendar results.
- [x] Trash has an owner-only listing that shows enough Entry information to decide whether to restore or destroy it.
- [x] Restoring clears Trash state and returns the Entry to its correct date group without losing revision history.
- [x] No automatic age-based Trash purge exists.
- [x] Permanent deletion requires a separate explicit confirmation value and cannot be triggered by the ordinary delete action.
- [x] Permanent deletion removes the stable Entry, every Entry Revision, processing records, and any currently existing derived/index records belonging to it.
- [x] Resource lookup and destructive operations do not reveal another identity's records.
- [x] Later search, AI, and Agent tickets must treat Trash exclusion and permanent deletion as invariant acceptance behavior.
- [x] System and browser tests cover trash, normal-view exclusion, restore, confirmation failure, and permanent cascade deletion.

## Comments

### 2026-08-22 - Ticket 09 implementation

#### Fixed review bases and prerequisite evidence

- `DIARY_REVIEW_BASE_SHA=869caaa1a0eb36e8489417c9f963abfbcc2f4df7`.
- `WEBSITE_REVIEW_BASE_SHA=6a8507f59c9470b6cd8c1a67ae13609d00cddb09`.
- Both repository worktrees were clean before implementation began.
- Ticket 08 was confirmed complete and independently review-Passed. Diary
  `Backend checks` run `31909227821`, Personal Website `Website checks and
  Pages` run `31909054678`, and Pages run `31909054413` were the latest
  exact-SHA runs and all completed successfully.

#### Confirmed Ticket 09 contract

- Permanent deletion uses the exact, case-sensitive confirmation value
  `PERMANENTLY DELETE`. The owner must type it manually; the browser enables
  submission only on a full match, FastAPI requires and validates the
  `confirmation` request-body field, and PostgreSQL validates the same value
  before executing deletion. The value is not stored.
- Moving to Trash, restoring, and permanent deletion are separate operations.
  Authentication, owner authorization, and forced PostgreSQL RLS remain
  independent controls; missing or incorrect confirmation cannot cause a
  partial deletion.

#### Implementation

- Added ordered migration `20260822120000_manage_diary_trash.sql` with
  authenticated owner-scoped RPCs for move, listing, restore, and permanent
  deletion. Trash is retained indefinitely; no automatic purge exists.
- Normal History, Calendar, Entry detail, revision lookup, and Entry-centered
  History exclude trashed Entries. Restore preserves immutable revisions and
  processing records and returns the Entry to its `Asia/Taipei` owner date.
- Confirmed permanent deletion cascades through the stable Entry, all Entry
  Revisions, processing records, and the currently existing derived/index
  table `entry_history_positions` in one database statement.
- Added FastAPI contracts and owner authorization for Trash operations while
  retaining caller-token PostgREST access and forced-RLS defense in depth.
- Added the owner Trash UI, recoverable move dialog, informative listing,
  restore action, and separate irreversible dialog with manual exact-value
  entry. The ordinary Trash action never sends a permanent-delete request.
- Personal Website implementation commit:
  `246eca4483a9b9358c3dbba9f3d422b27f41d450`. Diary CI pins that exact
  frontend commit. The Diary implementation endpoint is the commit containing
  this record.

#### TDD evidence

- Backend move-to-Trash red: the focused system test reached real Supabase,
  PostgREST, and FastAPI and received the expected missing-route `404`; green:
  `1 passed in 61.59s`.
- Backend restore red: focused restore received the expected missing-route
  `404`; green: `1 passed, 1 deselected in 61.76s`.
- Backend permanent-delete red: the focused request received the expected
  missing-route `404`; green: `1 passed, 2 deselected in 61.79s`.
- Frontend red: focused Chromium tests timed out because the `Move to Trash`
  action and `Trash` surface did not exist. Green: both Trash Chromium tests
  passed with zero retries (`2 passed in 2.0s`).
- Final focused backend Trash suite: `4 passed in 39.38s`. Final real owner
  Magic Link, Supabase, PostgREST, FastAPI, Uvicorn, frontend, and Chromium
  journey: `1 passed, 2 deselected in 46.43s`.

#### Complete local verification and scope

- Personal Website TypeScript type-check passed. The complete Chromium suite
  passed: `47 passed in 19.4s`, four workers, zero retries. Production build
  completed with 78 modules transformed, and `verify:build` passed.
- Diary mypy passed with no issues in 22 source files. The complete Diary suite
  passed against real local Supabase/PostgreSQL/PostgREST/FastAPI/Uvicorn and
  Chromium seams: `94 passed`, one existing Starlette/httpx deprecation
  warning, in `445.57s`.
- Both repositories passed `git diff --check`. No new Supabase, GitHub, or
  Azure environment variable is required. No secret, service-role key, JWT,
  or other private value was added to frontend source or Git.
- Ticket 10, AI Draft, OpenRouter, RAG, direct search, and Agent implementation
  remain unstarted. No push, review, release, or deployment was performed.
- Ticket 09 remains `ready-for-agent` pending a fresh independent complete
  fixed-range code-review in a separate conversation.

### 2026-08-23 - Personal Website Actions test-environment correction

#### Blocking CI evidence and root cause

- Personal Website pull-request workflow runs `32587521825` and `32587826294`
  both failed only at `Test browser journeys`: `45 passed`, `2 failed`. Both
  failures were the Ticket 09 cases in `tests/e2e/trash-management.spec.ts`;
  dependency installation, Chromium installation, and type-check all passed.
- GitHub Actions supplied the repository variable
  `VITE_DIARY_API_URL=https://diary-api.invalid`, while the Trash listing
  mocks intentionally intercept the test seam at `**/diary-api/trash`.
  Because the runner did not control this public setting, Vite sent listing
  requests to `https://diary-api.invalid/trash`; the mocks never received
  them and both tests could not find their Trash cards.

#### TDD correction

- Red command set `CI=true` and the repository-style invalid API URL, then ran
  the two Trash tests with two workers and zero retries. Result: `2 failed`.
  The restore case could not find `#trash-entry-entry-trash-restore`; the
  permanent-delete case timed out waiting for its Trash-card action.
- The only Personal Website source change makes `scripts/run-playwright.mjs`
  set the Playwright/Vite child-process value
  `VITE_DIARY_API_URL=/diary-api`, beside its existing test-only Supabase
  overrides. It does not change the workflow variable, production code, or a
  later production build process and it never calls a real Diary API.
- The identical focused command then passed: `2 passed in 1.8s`, two workers,
  zero retries, while the parent environment still supplied
  `https://diary-api.invalid`.

#### Verification and implementation endpoints

- Personal Website type-check passed. The complete Chromium suite passed:
  `47 passed in 16.7s`, four workers. Production build passed with 78 modules
  transformed, and `verify:build` passed.
- Personal Website corrected implementation commit:
  `e2bfbfab12bf1a958f33514cd7357cc44087bf30`. Diary CI now pins this exact
  frontend SHA.
- Diary mypy passed with no issues in 22 source files. The first complete
  pytest attempt encountered only a stopped-Docker fixture setup blocker and
  did not reach the affected system assertions. After Docker was restored, a
  fresh complete run passed against the corrected local frontend and real
  Supabase/PostgreSQL/PostgREST/FastAPI/Uvicorn/Chromium seams: `94 passed`,
  one existing Starlette/httpx deprecation warning, in `388.81s`.
- This correction remains Ticket 09 implementation work. Ticket 10 has not
  started, Ticket 09 has not been marked review-Passed, and no code-review or
  push was performed as part of the correction.
