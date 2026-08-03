# 08 — Change Entry Time and regroup history

**What to build:** Let the owner move an Entry to the intended date and time while preserving the distinction between metadata and Original Content. The Entry moves across history and calendar groups without creating a content revision.

**Blocked by:** 04 — Browse continuous bidirectional history.

**Status:** ready-for-agent

- [x] The owner can edit Entry Time through an explicit Entry action.
- [x] A valid change updates Entry metadata without creating or changing an Entry Revision.
- [x] Immutable capture time remains unchanged and is distinguishable from Entry Time.
- [x] The Entry disappears from its former date group and appears in the correct new `Asia/Taipei` group.
- [x] Calendar presence or counts update for both affected dates.
- [x] History cursor ordering remains correct after moving an Entry across a date or across an equal timestamp.
- [x] Invalid timestamps are rejected without partial changes.
- [x] Changing Entry Time alone does not invalidate or regenerate AI interpretation of unchanged Original Content.
- [x] System and browser tests cover same-day changes, cross-day moves, timezone boundaries, and unchanged revision count.

## Comments

### 2026-08-04 - Ticket 08 implementation complete

#### Fixed review bases and preflight

- Diary review base:
  `898a6056068ce282e36399d568ea6350bb413f29`.
- Personal Website review base:
  `231ebe21ed09ec7d777f3c78ed6eb58aab396962`.
- Ticket 07's fixed-range review is recorded as `PASSED`, with no blocking
  Standards or Spec finding.
- Both repositories were clean on `main`, their HEADs exactly matched the
  fixed review bases, and they matched `origin/main` before Ticket 08 began.
- Latest required GitHub Actions were green at both bases:
  - Diary `Backend checks`, run
    [30763641174](https://github.com/oscar940327/diary/actions/runs/30763641174).
  - Personal Website `Website checks and Pages`, run
    [30762095151](https://github.com/oscar940327/my-personal-website/actions/runs/30762095151),
    and `pages build and deployment`, run
    [30762094606](https://github.com/oscar940327/my-personal-website/actions/runs/30762094606).

#### TDD evidence

- Backend action red: the new real-system metadata-only test reached
  Supabase, PostgREST and Uvicorn, then received HTTP `404 Not Found` because
  `/entries/{entry_id}/entry-time` did not exist.
- History snapshot red: after moving an Entry already returned on page one,
  the existing cursor returned it again on page two because v4 froze Entry
  membership but not its ordering position.
- Browser red: the real mobile Chromium journey completed Magic Link sign-in,
  capture, edit and restore, then timed out waiting for the missing
  `Change Entry Time` Entry action.
- Backend green: the complete Ticket 08 focused system set passed `9 passed`,
  and the ordered Ticket 04-08 History, Calendar and Revision regression set
  passed `33 passed`.
- Browser green: the real Supabase/Auth/PostgreSQL/PostgREST/Uvicorn/Vite
  mobile Chromium journey changed Entry Time across a date, regrouped
  History, preserved Captured time and kept all three revisions unchanged.

#### Implementation and boundaries

- Ordered expand-contract migration
  `20260804120000_change_entry_time_and_stabilize_history.sql` adds the
  owner-token, RLS-enforced atomic Entry Time RPC and a snapshot-visible
  metadata position history. The latter versions only History ordering
  positions and never creates or changes an Entry Revision.
- History v5 chooses the Entry Time position visible to the cursor snapshot,
  so a concurrent move cannot duplicate a visited Entry or omit an unvisited
  Entry. Fresh History, Calendar and direct Entry reads use the current
  `entry_at`, with microsecond ordering and UUID equal-time tie-breaking.
- FastAPI rejects invalid, missing or offsetless timestamps before mutation.
  The database RPC independently requires an explicit offset, and direct
  owner-token table PATCH of `entry_at` or immutable `created_at` remains
  denied. FastAPI authorization and forced PostgreSQL RLS remain independent
  defenses.
- The frontend exposes a separate `Change Entry Time` action and dialog that
  explicitly distinguishes Entry Time, Captured time and Original Content
  revisions. A successful change regroups local History, refreshes from a new
  snapshot, refreshes Calendar data and preserves the active reading anchor.
- Revision identities, revision rows, immutable revision capture times,
  Original Content and the existing AI processing obligation remain byte-for-
  byte unchanged; no obligation is staled or created.
- Personal Website implementation commit:
  `3d1e27ea3d78eb20d44b1ef0a63defd64f0dd1b5`.
- Diary GitHub Actions now pins that exact reviewed frontend implementation
  commit, so the repositories must be pushed in Personal Website, then Diary
  order.
- No new Supabase, GitHub or Azure environment variable is required. No secret
  was added to frontend code or Git.
- Ticket 09, Trash, permanent deletion, AI Draft generation, Queue
  publication, RAG and Agent work were not started.
- This implementation session did not run code review and did not push either
  repository.

#### Full verification

- Diary: `python -m mypy src tests` passed; `python -m pytest -q` passed
  `75 passed` with one existing Starlette/httpx deprecation warning. The full
  suite reset and migrated the real local Supabase database and included the
  real mobile Chromium journey.
- Personal Website: `npm.cmd run typecheck` passed; the complete four-spec
  Playwright set passed all `21` Chromium tests with four workers;
  `npm.cmd run build` and `npm.cmd run verify:build` passed.
- On this Windows checkout, the nested `npm.cmd test` wrapper displayed all
  `21` tests as `ok` but did not return after Playwright's reusable local Vite
  server teardown. Running the same complete spec set directly through
  `npm.cmd run test:e2e -- <all four spec files>` returned exit code zero.

### 2026-08-04 - Fixed-range code review requires changes

#### Verdict and fixed ranges

- Review verdict: **CHANGES-REQUIRED**.
  - Standards: **PASS** with no blocking or documented-standard violation and
    three low-severity, non-blocking maintainability judgements.
  - Spec: **FAIL** with two blocking findings.
  - Overall: **REVIEW-FAILED**.
- Diary fixed range:
  `898a6056068ce282e36399d568ea6350bb413f29...5f7362f2ccaf0174dd9e74cf346d4bd20a5a08f4`.
- Personal Website fixed range:
  `231ebe21ed09ec7d777f3c78ed6eb58aab396962...3d1e27ea3d78eb20d44b1ef0a63defd64f0dd1b5`.
- Both review axes ran independently and in parallel against only these fixed
  three-dot ranges and inspected all 13 changed files.

#### Preflight and GitHub Actions

- Both worktrees were clean at review start, and both HEADs exactly matched
  their specified implementation endpoints on `main` and `origin/main`.
- GitHub contained both implementation commits. Both fixed ranges were
  non-empty, with one implementation commit in each, and both exact-range
  `git diff --check` commands passed.
- Exact-SHA GitHub Actions were green:
  - Diary `Backend checks`, run
    [30838455294](https://github.com/oscar940327/diary/actions/runs/30838455294),
    completed successfully for
    `5f7362f2ccaf0174dd9e74cf346d4bd20a5a08f4`.
  - Personal Website `Website checks and Pages`, run
    [30838197198](https://github.com/oscar940327/my-personal-website/actions/runs/30838197198),
    and `pages build and deployment`, run
    [30838188357](https://github.com/oscar940327/my-personal-website/actions/runs/30838188357),
    completed successfully for
    `3d1e27ea3d78eb20d44b1ef0a63defd64f0dd1b5`.

#### Blocking Spec findings

- **High - loaded History window and reading anchor are lost after Entry Time
  save.** Personal Website `src/diary/EntryExperience.tsx:349-352,673-686`
  first merges the moved Entry and consumes the pending reading anchor, then
  starts a cursorless refresh that replaces every previously loaded History
  page and both cursors with only the new initial page. After loading an older
  page and changing an Entry there, the Entry or its reading neighbor can
  disappear and the viewport can jump. This violates the specification's
  bidirectional History and explicit scroll-anchoring contract and the Ticket
  08 no-regression requirement. Reconstruct the loaded window from a new
  snapshot around the preserved or moved Entry, restore the anchor after the
  final data is present, and add a real Chromium case with more than one
  History page.
- **Medium - normalization-overflow and direct-RPC timestamp ranges are not
  rejected safely.** Diary `src/diary_api/app.py:101-111` lets an offset-aware
  boundary value such as
  `9999-12-31T23:59:59.999999-14:00` raise an uncaught `OverflowError` during
  UTC normalization, producing HTTP 500 rather than a validation response.
  Migration
  `supabase/migrations/20260804120000_change_entry_time_and_stabilize_history.sql:33-48`
  independently accepts PostgreSQL timestamps beyond Python's readable range
  through the owner-token RPC. This violates invalid-input rejection and lets
  the controlled mutation path create Entry metadata that FastAPI cannot read.
  Enforce one UTC-normalization-safe range in FastAPI and PostgreSQL, translate
  overflow into validation failure, and cover both HTTP and direct-RPC paths
  while asserting the Entry, revisions, and processing remain unchanged.

#### Non-blocking Standards judgements

- **Low - possible Divergent Change.** Personal Website
  `src/diary/EntryExperience.tsx:249,276-299,640-692,1051-1119` adds Entry Time
  state, mutation orchestration, anchor handling, and dialog rendering to the
  already broad component. A focused Entry Time editor/controller module would
  improve locality.
- **Low - Duplicated Code.** Diary `src/diary_api/app.py:67-77,106-111`
  repeats the offset-aware Entry Time validation and UTC normalization between
  create and change requests. A shared validator would prevent semantic drift.
- **Low - Mysterious Name.** Diary `.github/workflows/ci.yml:22-26` still names
  the step `Check out Ticket 07 frontend` while pinning the Ticket 08 Website
  commit. Rename the step to identify the reviewed Diary frontend accurately.

No Ticket 09 scope creep, committed secret, or additional blocking finding was
found. Ticket 08 remains `ready-for-agent` for the two Spec fixes, and Ticket
09 must not begin until a fresh fixed-range review passes.
