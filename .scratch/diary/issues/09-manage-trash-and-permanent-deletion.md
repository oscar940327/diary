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

### 2026-08-23 - Fresh independent complete fixed-range review requires changes

#### Fixed review ranges

- Diary Base: `869caaa1a0eb36e8489417c9f963abfbcc2f4df7`.
- Diary Head: `aa1c38cca425c275c02c154c312e99cfbfd4c803`.
- Personal Website Base: `6a8507f59c9470b6cd8c1a67ae13609d00cddb09`.
- Personal Website Head: `e2bfbfab12bf1a958f33514cd7357cc44087bf30`.
- Both merge bases equal the specified Bases, both fixed-range diffs were
  non-empty, and both worktrees were clean before and after the review.

#### Standards review - Passed

- No documented-standard violation, secret exposure, production-content
  logging, unrelated legacy-site change, or Ticket 10 scope creep was found.
- Ticket 10, AI Draft, OpenRouter, direct search, RAG, and Agent implementation
  remain unstarted. Both fixed ranges passed `git diff --check`.
- One non-blocking Fowler judgement call remains: Personal Website
  `src/diary/TrashView.tsx:19-25` duplicates the existing `formatTaipei`
  formatter in `src/diary/EntryExperience.tsx:75-81`. This possible
  Duplicated Code smell is not a documented-standard breach and does not
  affect Ticket 09 correctness or security.

#### Spec review - Changes Required

- **High - blocking - restoring an Entry mixes new data into an old bounded
  History snapshot.** Personal Website
  `src/diary/EntryExperience.tsx:1370-1372` immediately merges every restored
  Entry into the currently loaded `entries`, while retaining the existing
  `anchorDate`, `olderCursor`, and `newerCursor`. If History is anchored around
  one date with usable cursors and the owner restores a far-away Entry from
  Trash, returning to History renders a date group that does not belong to the
  bounded window and continues pagination through the old snapshot cursors.
  This violates the bounded cursor History contract in
  `.scratch/diary/spec.md:200,247` and regresses Ticket 08's explicit rule at
  `.scratch/diary/issues/08-change-entry-time-and-regroup.md:228-231` that the
  frontend never combines old snapshot cursors with new data.
- The current browser regression at Personal Website
  `tests/e2e/trash-management.spec.ts:55-180` uses an Entry on the same anchor
  date and returns both cursors as `null`, so it does not exercise the defect.
- Minimal correction scope: after a successful restore, do not merge the
  restored Entry into the old History window. Invalidate or rebuild History
  from a fresh bounded response and install its Entries and both cursors
  atomically. Add one browser regression that restores an Entry far from the
  current anchor while both old cursors are non-null, then proves the UI never
  renders new data with those old cursors. No backend, database, Ticket 10, AI,
  search, RAG, or Agent change is required for this finding.
- All other Ticket 09 requirements reviewed correctly: Move to Trash and
  permanent deletion are separate; active History, Calendar, Entry detail,
  revision lookup, and Entry-centered History exclude Trash; the owner-only
  listing carries current content, Entry Time/date, Trash time, and revision
  count; restore preserves revision and processing rows and the original
  Entry Time; no purge exists; browser, FastAPI, and PostgreSQL require exact
  case-sensitive `PERMANENTLY DELETE`; invalid confirmation reaches no
  destructive statement; one database `DELETE` cascades through `entries`,
  `entry_revisions`, `ai_processing`, and the currently existing derived/index
  table `entry_history_positions`; lookup and destructive operations are
  non-disclosing; and FastAPI authorization plus forced RLS remain independent
  defenses. Future AI, citation, search, and retrieval tables do not yet exist,
  so their Trash and cascade rules remain future invariants rather than Ticket
  09 implementation scope.
- `scripts/run-playwright.mjs` overrides `VITE_DIARY_API_URL=/diary-api` only
  inside the test-runner process. The production build still reads the GitHub
  repository variable, and the Ticket 09 browser mocks do not call a hosted or
  production Diary API. Diary CI pins the reviewed Website Head exactly:
  `e2bfbfab12bf1a958f33514cd7357cc44087bf30`.

#### Fresh local verification

- Personal Website `npm.cmd run typecheck`: passed.
- Personal Website `npm.cmd run test:e2e`: `47 passed` with four workers and
  zero retries in `22.3s`. Existing negative/recovery cases emitted local
  `127.0.0.1:8000 ECONNREFUSED` proxy diagnostics; the Ticket 09 Trash mocks
  matched and no hosted Diary API was contacted.
- Personal Website `npm.cmd run build`: passed with 78 modules transformed.
- Personal Website `npm.cmd run verify:build`: passed.
- Diary `python -m mypy src tests`: passed with no issues in 22 source files.
- Diary `python -m pytest -q --tb=short`: after an initial sandbox-only Docker
  named-pipe setup failure, the identical command ran with Docker access and
  passed `94 passed`, with one existing Starlette/httpx deprecation warning,
  in `365.41s`.
- Supabase `db lint --local --level warning`: passed with `No schema errors
  found`. The temporary local Supabase stack was stopped after lint.

#### Exact-SHA GitHub Actions

- Personal Website Head `e2bfbfab12bf1a958f33514cd7357cc44087bf30`:
  `Website checks and Pages` pull-request run
  [32590938026](https://github.com/oscar940327/my-personal-website/actions/runs/32590938026)
  completed successfully. Type-check, browser journeys, build, and build
  verification all succeeded; the PR-only deploy job was correctly skipped.
- Diary Head `aa1c38cca425c275c02c154c312e99cfbfd4c803`:
  `Backend checks` push run
  [32591185370](https://github.com/oscar940327/diary/actions/runs/32591185370)
  and pull-request run
  [32591325227](https://github.com/oscar940327/diary/actions/runs/32591325227)
  both completed successfully. Each checkout, type-check, and complete test
  step succeeded, including checkout of the exact reviewed Website Head.

#### Verdict

- Standards: Passed with zero hard findings and one non-blocking smell.
- Spec: Changes Required with one High blocking finding.
- **Ticket 09 review Changes Required.** Ticket 09 is not ready for document
  closeout or PR merge. Apply only the minimal frontend History invalidation or
  fresh-window correction and its far-date/non-null-cursor browser regression,
  then run a new independent complete fixed-range review. Do not start Ticket
  10 while Ticket 09 remains review-blocked.

### 2026-08-23 - Blocking History snapshot restore correction

#### Finding fix and scope

- Fixed the review's only High blocking finding in Personal Website. A
  successful Trash restore no longer merges the restored Entry into the
  currently loaded bounded History window.
- Restore now retires old History request ownership and fully invalidates the
  loaded Entries, anchor, both cursors, adjacent state, and recovery state
  before requesting a fresh bounded response for the selected History anchor.
  The fresh response installs its Entries, anchor, `older_cursor`, and
  `newer_cursor` together through the existing root History refresh path.
- The Restore success message remains visible in Trash. Existing browser and
  system coverage continues to prove revision preservation and the restored
  Entry's correct `Asia/Taipei` owner date.
- No backend, migration, RLS, API-contract, permanent-deletion, or database
  code changed. The non-blocking `formatTaipei` duplication was deliberately
  left unchanged.

#### TDD red and green evidence

- Added a browser regression with History anchored on `2050-04-05`, a restored
  Entry on distant date `2040-01-02`, and both old History cursors non-null. It
  pauses the restore-triggered fresh response and proves that the old Entry,
  distant restored Entry, and old pagination controls are absent during full
  invalidation. After releasing the response, it proves that only the fresh
  bounded Entries render and that newer and older pagination send
  `fresh-newer-cursor` and `fresh-older-cursor` respectively.
- Red command:
  `npm.cmd run test:e2e -- tests/e2e/trash-management.spec.ts --grep "restoring a distant Entry" --workers=1 --retries=0`.
  Before the source fix it failed at the expected invariant assertion because
  `Loading Diary history…` never appeared after returning from Trash; the old
  History snapshot remained installed. Result: `1 failed` in `5.7s` for the
  test body.
- Green with the identical command: `1 passed (1.8s)`, one worker, zero
  retries. The complete focused Trash browser file also passed: `3 passed
  (3.0s)`, one worker, zero retries.

#### Complete verification and implementation endpoints

- Personal Website `npm.cmd run typecheck`: passed.
- Personal Website `npm.cmd run test:e2e`: `48 passed (18.7s)`, four workers,
  zero retries. Existing negative/recovery cases emitted only their expected
  local `127.0.0.1:8000 ECONNREFUSED` proxy diagnostics.
- Personal Website `npm.cmd run build`: passed with 78 modules transformed.
- Personal Website `npm.cmd run verify:build`: passed with GitHub Pages output
  verified.
- Personal Website implementation commit:
  `b15316f814b516622d85c315c7769557d0f11edb`. Diary CI pins this exact SHA.
- Diary `python -m mypy src tests`: passed with no issues in 22 source files.
- The first Diary `python -m pytest -q --tb=short` attempt encountered only a
  stopped-Docker/local-Supabase fixture setup blocker (`20 passed, 74 setup
  errors`) and did not reach the affected system assertions. After Docker was
  started, the identical complete command passed against real local
  Supabase/PostgreSQL/PostgREST/FastAPI/Uvicorn/frontend/Chromium seams: `94
  passed`, one existing Starlette/httpx deprecation warning, in `377.14s`.
- The first exact Supabase lint command could not connect after pytest teardown
  stopped the fixture stack. After starting the same minimal temporary local
  stack, the identical
  `npm.cmd run supabase -- db lint --local --level warning` passed with
  `No schema errors found`; the temporary stack was then stopped.
- The Diary implementation endpoint is the commit containing this appended
  record and the exact Website CI pin. Ticket 10 remains unstarted, Ticket 09
  remains `ready-for-agent` and review-blocked, and no code-review, push, merge,
  release, or deployment was performed.

### 2026-08-23 - New independent complete fixed-range review requires changes

#### Fixed review ranges and method

- Diary Base: `869caaa1a0eb36e8489417c9f963abfbcc2f4df7`.
- Diary Head: `5f3858c12c1e5ed9b8b08dc1fe647a3998100ca2`.
- Personal Website Base:
  `6a8507f59c9470b6cd8c1a67ae13609d00cddb09`.
- Personal Website Head:
  `b15316f814b516622d85c315c7769557d0f11edb`.
- Both Bases resolve and are ancestors of their specified Heads; both exact
  fixed-range diffs are non-empty. This review re-read every product, test,
  workflow and documentation hunk in both complete ranges. It did not limit
  review to the last History snapshot finding fix. Both `git diff --check`
  commands passed, and both worktrees were clean before review and before this
  required Comments-only append.

#### Standards review - Passed

- No blocking or hard documented-standard finding was found against
  `AGENTS.md`, `CONTEXT.md`, the complete Spec and Ticket 09, `docs/agents/`,
  every ADR, and both repositories' documented build and test conventions.
- The ranges remain confined to Ticket 09 Trash management, its tests, the
  Playwright public test-configuration correction, and the requested History
  finding fix. Ticket 10, AI Draft, OpenRouter, direct search, RAG and Agent
  implementation have not started.
- No production logging, secret exposure, hosted-API test bypass, unrelated
  legacy-site change or defense-in-depth regression was found. FastAPI still
  requires the singleton owner, caller-token PostgREST still reaches forced
  PostgreSQL RLS independently, and the additive migration keeps the preceding
  application contract.
- Diary `.github/workflows/ci.yml` pins the exact reviewed Website Head
  `b15316f814b516622d85c315c7769557d0f11edb`.
- One non-blocking Fowler judgement remains: Personal Website
  `src/diary/TrashView.tsx:19-25` duplicates the existing `formatTaipei`
  formatter in `src/diary/EntryExperience.tsx:75-81`. This possible
  Duplicated Code smell is not a documented-standard breach and does not
  affect Ticket 09 correctness or security.

#### Spec review - Changes Required

- **High - blocking - Restore can add an Entry to another client's old
  bounded History snapshot.** Migration
  `20260822120000_manage_diary_trash.sql:295-300` restores an Entry by clearing
  `trashed_at` but does not create a new History membership generation.
  `list_diary_history_v5` in
  `20260804120000_change_entry_time_and_stabilize_history.sql:319-356` tests
  the current `trashed_at is null` state while continuing to admit the Entry's
  immutable creation `history_membership_xid` and original visible
  `entry_history_positions` generation against the cursor snapshot.
- Adversarial sequence: the Entry exists, is moved to Trash, and client A then
  opens a bounded History snapshot with non-null older and newer cursors.
  Client B restores the Entry. When client A follows either old cursor, the
  now-current null Trash state combines with the old membership/position XIDs,
  so the restored Entry can enter snapshot A even though it was excluded when
  A was created. This violates Ticket 04's requirement that between-request
  changes not add, duplicate or omit snapshot members and Ticket 08's rule
  that one snapshot governs membership and both continuation cursors.
- The Personal Website fix itself correctly retires same-client History
  request ownership, clears old Entries, anchor, both cursors and recovery
  state, and installs the fresh bounded response together. Its browser
  regression uses a distant restored date and two non-null old cursors, pauses
  the fresh response, proves old data and controls are gone, and then proves
  both fresh cursors are used. However, that regression is mock-only and
  cannot detect the real PostgreSQL cross-client old-cursor path above.
- Minimal correction scope: add one ordered additive Diary migration that
  makes active History membership lifecycle snapshot-visible. Moving to Trash
  must close the current `entry_history_positions` generation at the Trash
  transaction XID, and Restore must open a new generation at the unchanged
  Entry Time and Restore transaction XID. Preserve Entry Time, all Entry
  Revisions and processing records; do not change frontend behavior or begin
  Ticket 10. Add one real FastAPI/PostgREST/PostgreSQL regression in which a
  trashed distant Entry is absent when a snapshot with both cursors is created,
  Restore occurs through the public API, both old cursor traversals remain
  exactly free of that Entry, and a fresh bounded traversal includes it with
  both fresh cursors usable.
- All other Ticket 09 acceptance behavior passed review: Move to Trash and
  permanent deletion are separate; active History, Calendar, Entry detail,
  revision lookup and Entry-centered History exclude Trash; the owner-only
  listing includes complete current content, Entry Time/date, Trash time and
  revision count; restore preserves revisions, processing rows, Entry Time and
  the correct `Asia/Taipei` owner date; no automatic purge exists; browser,
  FastAPI and PostgreSQL require exact case-sensitive `PERMANENTLY DELETE`;
  missing or incorrect confirmation reaches no destructive statement and
  causes no partial deletion; one owner-scoped database `DELETE` cascades the
  Entry, Entry Revisions, processing rows and current derived/index table
  `entry_history_positions`; foreign-owner, wrong-state and nonexistent
  resources remain non-disclosing; and FastAPI authorization plus forced RLS
  remain independent defenses.
- `scripts/run-playwright.mjs` sets `VITE_DIARY_API_URL=/diary-api` only in the
  test-runner process. The later production build still reads its production
  workflow configuration. Ticket 09 browser tests intercept the local
  `/diary-api` seam and do not contact a hosted or production Diary API.

#### Fresh complete local verification

- Personal Website `npm.cmd run typecheck`: passed.
- Personal Website `npm.cmd run test:e2e`: passed `48 passed (21.6s)`, four
  workers and zero retries. Existing negative/recovery cases emitted only
  expected local `127.0.0.1:8000 ECONNREFUSED` proxy diagnostics.
- Personal Website `npm.cmd run build`: passed with 78 modules transformed;
  only the existing classic-script notices were emitted.
- Personal Website `npm.cmd run verify:build`: passed and verified the GitHub
  Pages output.
- Diary `python -m mypy src tests`: passed with no issues in 22 source files.
- The first sandboxed Diary `python -m pytest -q --tb=short` attempt could not
  access the Docker named pipe and ended `20 passed, 74 setup errors`; no
  affected system assertion ran. The identical command with local
  Docker/Supabase access then passed `94 passed`, with one existing
  Starlette/httpx deprecation warning, in `378.09s`.
- The first exact Supabase lint command ran after pytest teardown had stopped
  the fixture stack and could not connect. After starting the same minimal
  local stack, the identical
  `npm.cmd run supabase -- db lint --local --level warning` passed with
  `No schema errors found`. The temporary stack was then stopped and its local
  data remained backed up.

#### Exact-SHA GitHub Actions

- Personal Website Head `b15316f814b516622d85c315c7769557d0f11edb`:
  `Website checks and Pages` pull-request run
  [32620331811](https://github.com/oscar940327/my-personal-website/actions/runs/32620331811)
  completed `success` on attempt 1. The build job and its checkout, type-check,
  browser journeys, production build and preserved-output verification steps
  all succeeded; PR-only Pages configure/upload and deploy were correctly
  skipped.
- Diary Head `5f3858c12c1e5ed9b8b08dc1fe647a3998100ca2`:
  `Backend checks` push run
  [32624771653](https://github.com/oscar940327/diary/actions/runs/32624771653)
  and pull-request run
  [32624773628](https://github.com/oscar940327/diary/actions/runs/32624773628)
  both completed `success` on attempt 1. Each test job succeeded through Diary
  checkout, exact reviewed Website checkout, type-check and complete test.

#### Verdict

- Standards: Passed with zero blocking/hard findings and one non-blocking
  Duplicated Code judgement.
- Spec: Changes Required with one High blocking History membership finding.
- **Ticket 09 review Changes Required.** Ticket 09 is not ready for document
  closeout or PR merge. Apply only the additive backend membership-lifecycle
  correction and its real old-snapshot/two-cursor regression described above,
  then run another new independent complete fixed-range review. Do not start
  Ticket 10 while Ticket 09 remains review-blocked.

### 2026-08-23 - Restore History membership lifecycle correction

#### Finding fix and regression scope

- Fixed the latest review's only High blocking finding without changing the
  FastAPI contract or Personal Website behavior. A Restore can no longer add
  an Entry to a bounded History snapshot that was created while that Entry was
  in Trash.
- Added a real FastAPI/PostgREST/PostgreSQL system regression. It creates a
  bounded History snapshot with non-null older and newer cursors while a
  distant `1901-01-01` Entry remains in Trash, restores that Entry through the
  public FastAPI endpoint, and completely continues both old cursor
  traversals. The test proves the restored Entry is absent from both, the old
  traversal has neither duplicates nor omissions, and a fresh bounded
  traversal includes the Entry while both fresh cursors remain usable.
- Existing owner authorization, caller-token PostgREST access, forced RLS,
  and non-disclosing foreign-owner, wrong-state, and nonexistent behavior are
  unchanged. The complete Trash system file continues to cover those seams.

#### TDD red and green evidence

- Red command:
  `python -m pytest -q --tb=short tests/system/test_trash_management.py -k
  "restore_starts_a_new_history_snapshot_membership_generation"`.
  Against the prior membership lifecycle it failed at the expected invariant:
  the old `older_cursor` response contained the distant restored Entry.
  Result: `1 failed, 4 deselected in 65.41s`.
- Green with the identical command after the additive migration:
  `1 passed, 4 deselected in 27.78s`.
- The complete focused Trash system file then passed:
  `5 passed in 29.23s`.

#### Additive migration and membership lifecycle

- Added ordered migration
  `20260823120000_stabilize_trash_history_membership.sql`; the existing
  `20260822120000_manage_diary_trash.sql` migration was not modified or
  rewritten.
- A `trashed_at` lifecycle trigger now uses `pg_current_xact_id()` in the same
  database transaction as the authorized Entry update. Move to Trash closes
  the current active `entry_history_positions` generation at the Trash XID;
  Restore opens a new generation at the Restore XID with exactly the unchanged
  Entry Time. This continues to use the existing History XID and PostgreSQL
  snapshot semantics rather than adding another cursor model.
- Migration installation explicitly locks Entry writes and reconciles any
  already-trashed pre-migration rows in the same migration transaction before
  installing the trigger, so their previously active position is closed and
  a later Restore can open a new generation safely.
- Restore still does not modify Entry Time, Entry Revisions, or delete
  processing records. Permanent deletion still cascades from `entries`
  through every History position generation, all Entry Revisions, and
  processing records.

#### Complete verification and implementation endpoints

- Diary `python -m mypy src tests`: passed with no issues in 22 source files.
- Diary `python -m pytest -q --tb=short`: `95 passed`, with one existing
  Starlette/httpx deprecation warning, in `329.07s`.
- Diary `npm.cmd run supabase -- db lint --local --level warning`: passed with
  `No schema errors found`.
- Diary `git diff --check`: passed.
- Personal Website `npm.cmd run typecheck`: passed.
- Personal Website `npm.cmd run test:e2e`: `48 passed (18.3s)`, four workers
  and zero retries. Existing negative/recovery cases emitted only their
  expected local `127.0.0.1:8000 ECONNREFUSED` proxy diagnostics.
- Personal Website `npm.cmd run build`: passed with 78 modules transformed;
  only the existing classic-script notices were emitted.
- Personal Website `npm.cmd run verify:build`: passed and verified the GitHub
  Pages output. Personal Website `git diff --check` also passed.
- Personal Website remained clean at the requested unchanged SHA
  `b15316f814b516622d85c315c7769557d0f11edb`.
- The Diary implementation endpoint is the commit containing this record.
  Ticket 10, AI Draft, OpenRouter, search, RAG, and Agent implementation remain
  unstarted. Ticket 09 remains `ready-for-agent` and review-blocked; it was not
  marked review-Passed. No code-review, push, merge, release, or deployment was
  performed.
