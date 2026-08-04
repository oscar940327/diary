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

### 2026-08-04 - Blocking review findings fixed; fresh review required

#### TDD evidence

- FastAPI red: the new real Uvicorn HTTP test sent
  `9999-12-31T23:59:59.999999-14:00` and received `500 Internal Server Error`
  instead of the required validation response.
- PostgREST red: the new direct owner-token RPC test received `200` and wrote
  `10000-01-01T13:59:59.999999+00:00`, proving PostgreSQL could create Entry
  metadata that Python could not safely read.
- Chromium red: with 120 lifetime Entries and 40 Entries loaded across two
  History pages, changing Entry Time from an Entry on the second page reduced
  the rendered window to the single 20-Entry initial page.
- Timestamp green: the real FastAPI and direct PostgREST boundary tests passed
  `2 passed`, including upper and lower UTC-normalization overflow, year
  `10000`, offsetless and invalid-offset timestamps, and missing `entry_at`.
- History green: the real mobile Chromium regression passed while preserving
  the 40-Entry loaded window and the reading Entry within an 8-pixel viewport
  tolerance. Subsequent newer and older requests used one new snapshot,
  produced no duplicate or omitted covered Entry, updated both Calendar
  counts, and rendered only 80 of 120 lifetime Entries.

#### Fixes and preserved invariants

- Create Entry and Change Entry Time now share one Pydantic
  UTC-normalization-safe Entry Time validator. Normalization overflow becomes
  a formal `422` validation failure rather than an uncaught exception.
- Ordered expand migration
  `20260804130000_restrict_entry_time_to_python_utc_range.sql` replaces only
  the controlled Entry Time RPC implementation, retains its restricted owner
  role and RLS path, and enforces the same Python-safe UTC range. Invalid or
  missing direct RPC input returns `400` before any Entry update.
- The frontend rebuilds the previously loaded History window around the
  preserved reading Entry or moved Entry using bounded 20-Entry requests from
  a new snapshot. It never combines old snapshot cursors with new data and
  restores the scroll anchor only after the final rebuilt window is ready.
- Failed validation leaves every Entry field, immutable Entry Revision row and
  identifier, Original Content, Revision `created_at`, AI processing
  obligation, and Entry history-position row unchanged. A successful time-only
  mutation still changes no Revision or AI processing obligation.
- Diary CI now calls the checkout step `Check out reviewed Diary frontend` and
  pins Personal Website commit
  `7898db9691d41f3f418a27250387164531359aac` exactly.
- No Ticket 09, Trash, deletion, AI generation, Queue, RAG, Agent, broad
  `EntryExperience` refactor, secret-bearing frontend data, or Git credential
  work was started.

#### Verification and review handoff

- Ordered local Supabase reset applied every migration through
  `20260804130000` successfully.
- Diary static and focused checks passed: `python -m mypy src tests`, the
  Ticket 04-08 History/Calendar/Revision/Entry Time set (`35 passed`), both
  real mobile Chromium journeys (`2 passed`), and the complete
  `python -m pytest -q` suite (`78 passed`) with the existing single
  Starlette/httpx deprecation warning.
- Personal Website checks passed: `npm.cmd run typecheck`, all `21` Playwright
  Chromium tests, `npm.cmd run build`, and `npm.cmd run verify:build`.
- Personal Website fix commit:
  `7898db9691d41f3f418a27250387164531359aac`.
- This fix session did not run code review and did not push either repository.
  The prior review remains failed until a new session reviews the original
  Ticket 08 bases against the new repository Heads. Ticket 09 remains blocked.

### 2026-08-04 - Fresh fixed-range code review still requires changes

#### Verdict and fixed ranges

- Review verdict: **CHANGES-REQUIRED**.
  - Standards: **PASS** with no hard or documented-standard violation and one
    low-severity, non-blocking maintainability judgement.
  - Spec: **FAIL** with four blocking findings.
  - Overall: **REVIEW-FAILED**.
- Diary fixed range:
  `898a6056068ce282e36399d568ea6350bb413f29...189bd18e9f498124f5282fdb37b296b82ef98c82`.
- Personal Website fixed range:
  `231ebe21ed09ec7d777f3c78ed6eb58aab396962...7898db9691d41f3f418a27250387164531359aac`.
- Both axes independently reviewed the complete three-dot ranges, including
  the original Ticket 08 implementation, prior review record, and blocker-fix
  commits rather than only the latest fix.

#### Preflight and GitHub Actions

- Both worktrees were clean at review start and both HEADs exactly matched the
  requested SHAs. Both bases resolved, both merge-bases matched the requested
  bases, both ranges were non-empty, and both `git diff --check` commands
  passed.
- GitHub contained both exact Head commits. Exact-SHA Actions were green:
  - Diary `Backend checks`, run
    [30912948403](https://github.com/oscar940327/diary/actions/runs/30912948403).
  - Personal Website `Website checks and Pages`, run
    [30912247537](https://github.com/oscar940327/my-personal-website/actions/runs/30912247537),
    and `pages build and deployment`, run
    [30912242257](https://github.com/oscar940327/my-personal-website/actions/runs/30912242257).

#### Blocking Spec findings

- **High - History rebuild is date-anchored, not Entry-anchored.** Personal
  Website `src/diary/EntryExperience.tsx:139-202,749-773` rebuilds from only an
  `anchorDate` and always follows `olderCursor` first. If at least 40 Entries
  on the target date sort ahead of the moved or reading Entry, the initial and
  older requests fill the target count before that Entry is returned. The
  active Entry then disappears, `restoreReadingAnchor` has no element to
  restore, and the viewport and loaded reading window change. This violates
  the bidirectional History and explicit scroll-anchor contract and the prior
  fix requirement to rebuild around the preserved or moved Entry. The real
  Chromium regression seeds exactly 20 Entries per date and moves the new
  date's newest Entry, so it does not exercise this case.
- **High - a failed rebuild mixes committed data with old snapshot cursors.**
  Personal Website `src/diary/EntryExperience.tsx:516-554,781-794,1015-1108`
  merges the committed Entry after a post-mutation History request fails but
  leaves the old `olderCursor` and `newerCursor` active. A subsequent Load
  newer/older action uses the pre-change snapshot; its historical row can
  overwrite the committed Entry Time in `mergeEntries`, causing wrong grouping
  and disagreement with refreshed Calendar counts. The error text suggests
  loading History again but provides no fresh-snapshot refresh action. This
  violates the explicit no-old-cursor/new-data invariant and has no regression
  test.
- **High - direct Create RPC still accepts Python-unsafe Entry Time.** Diary
  `supabase/migrations/20260728100000_run_entry_rpcs_as_authenticated_owner.sql:46-65,97-116,188-200,242-255`
  exposes `create_diary_entry(..., timestamptz, ...)` to `authenticated` and
  inserts `p_entry_at` without an offset-text check or Python-safe UTC range.
  No later migration or table constraint closes this path; the Ticket 08
  hardening migration changes only `change_diary_entry_time`. An owner token
  can therefore directly create an Entry at PostgreSQL year 10000, including
  its Revision, processing obligation, and History position, after which
  Python `EntryRecord` cannot safely parse the metadata. This violates the
  required FastAPI/PostgreSQL range invariant and the prohibition on direct
  RPC writes that FastAPI cannot read. Existing boundary tests cover only the
  Change Entry Time RPC.
- **Medium - valid lower-bound years are misordered in the browser.** Personal
  Website `src/diary/EntryExperience.tsx:74-123` passes the parsed year to
  `Date.UTC`; ECMAScript maps years 0 through 99 to 1900 through 1999. Thus a
  valid year `0001` Entry is treated as 1901 during `sortEntries` and can sort
  above a genuinely newer Entry such as year 1800. This violates reverse-
  chronological History ordering across the accepted Python-safe range. The
  new tests cover lower normalization overflow, not valid years 0001-0099.

#### Standards judgement and verification

- **Low - possible Divergent Change.** Personal Website
  `src/diary/EntryExperience.tsx:139-203,315-393,714-803,1160-1233` keeps
  History rebuilding, scroll-anchor lifecycle, Entry Time mutation/error
  recovery, Calendar invalidation, and dialog rendering in the already broad
  page component. This is a non-blocking smell judgement, not a documented-
  standard violation, and a broad refactor remains outside Ticket 08.
- Local checks passed: `python -m mypy src tests`; `19` backend unit tests;
  Personal Website typecheck, all `21` mocked Playwright tests, build, and
  build-output verification. A direct Node probe confirmed the year 0-99
  `Date.UTC` remapping.
- The focused real-system Ticket 08 run could not start locally because Docker
  Desktop was not running; all 12 selected cases stopped in fixture setup, so
  this was an environment limitation rather than a product-test failure. The
  exact-SHA GitHub Actions runs above remain green, but their passing suites do
  not cover the four scenarios identified here.
- The shared FastAPI validator, Change Entry Time RPC rejection atomicity,
  Entry Revision and AI-obligation invariants, RLS and owner checks, CI naming
  and exact frontend pin, expand-contract compatibility, ordinary
  microsecond/UUID tie ordering, and Calendar refresh showed no additional
  finding in the reviewed cases.
- No Ticket 09 scope, production/test change, committed secret, broad existing-
  site refactor, or push occurred. Ticket 08 remains `ready-for-agent`, and
  Ticket 09 must not begin until these findings are fixed and another complete
  fixed-range review passes.

### 2026-08-05 - Latest blocking findings fixed; fresh review still required

#### TDD red evidence

- Active-Entry History rebuild red: the new real 390-by-844 Chromium journey
  seeded 140 lifetime Entries, loaded two 20-Entry pages, read an Entry on page
  two, and moved it behind 40 Entries on a dense destination date. The rebuild
  stopped at the old 40-Entry target before locating the moved Entry: the test
  expected the required third bounded page and 60 rendered Entries but received
  only 40.
- Fresh-snapshot recovery red: after the mocked Change Entry Time boundary
  returned `200` and the first cursorless fresh History request returned `503`,
  the UI still rendered `Load newer Entries`. The regression expected zero old
  cursor controls but received one, proving committed data could still paginate
  through the pre-mutation snapshot.
- Direct Create RPC red: an authenticated owner called real PostgREST
  `create_diary_entry` with `10000-01-01T00:00:00+00:00`; the RPC returned
  `200` and created the Entry, Revision, AI-processing obligation and History
  position instead of rejecting before writes.
- Ancient-year ordering red: the focused Chromium History test supplied known
  UTC ordering across years `0001`, `0099`, `0100` and `1800`. The browser put
  all year-0099 Entries ahead of year 1800 because `Date.UTC` remapped 0099 to
  1999.

#### Minimal fixes and green evidence

- History rebuild now receives the preserved reading or moved Entry UUID and
  continues bounded 20-Entry requests until both the target window size and
  that exact Entry anchor are present. It fails closed if the Entry cannot be
  located within the bound. The real dense-date mobile Chromium regression
  passed, preserved the Entry within 8 pixels, rebuilt 60 Entries rather than
  shrinking the loaded window, used one new snapshot for rebuild and both
  later directions, rendered no duplicate among 100 covered Entries, kept the
  window below the 140-Entry lifetime, and updated both Calendar counts.
- A committed mutation whose rebuild fails now clears both old cursors and
  retains an explicit recovery record containing the Entry UUID, anchor date,
  target count and reading anchor. `Refresh History` performs another bounded
  rebuild; only its completed fresh window installs cursors and restores the
  anchor. The Chromium recovery regression passed with no old-snapshot request,
  consistent committed History and Calendar dates, one recovery snapshot and
  successful newer/older continuation.
- Ordered expand-contract migration
  `20260805120000_harden_create_entry_time_range.sql` adds a Python-safe UTC
  range constraint and replaces only the controlled Create RPC contract with a
  text-preserving, offset-aware implementation. Validation occurs before the
  first insert. The real direct-RPC regression passed for upper and lower UTC
  normalization overflow, PostgreSQL year 10000, offsetless input and invalid
  offset; all returned `400`, and Entries, Entry Revisions, AI obligations,
  History positions and idempotency state remained byte-for-byte unchanged.
  Omitted and null Entry Time still default to now and remain readable through
  FastAPI; the existing FastAPI application Create path still returned `201`.
- Browser ordering now converts proleptic-Gregorian civil dates and offsets
  directly to bigint microseconds. It does not use `Date` or millisecond
  precision for final sorting. The focused Chromium regression passed the
  `0001`/`0099`/`0100`/`1800` order, six-digit microseconds, offset
  normalization and equal-time descending UUID tie-break.

#### Verification and preserved boundaries

- Ordered local Supabase reset applied every migration through
  `20260805120000` successfully.
- Diary passed `python -m mypy src tests`; the Ticket 04-08 History, Calendar,
  Revision, Entry Time and real mobile Chromium focused set passed `39 passed`;
  and `python -m pytest -q` passed `80 passed` with the existing single
  Starlette/httpx deprecation warning.
- Personal Website passed `npm.cmd run typecheck`, all `23` Playwright Chromium
  tests, `npm.cmd run build`, and `npm.cmd run verify:build`.
- Create Entry and Change Entry Time continue sharing the same FastAPI
  UTC-normalization-safe validator. PostgreSQL Create and Change enforce the
  same UTC year 0001-9999 range. The Create RPC remains `security invoker`,
  owner-token authenticated, and RLS-enforced; FastAPI singleton-owner checks
  and forced PostgreSQL RLS remain independent defenses. Direct table PATCH of
  `entry_at` or immutable `created_at` remains denied.
- Successful Entry Time changes still create, alter or delete no Entry
  Revision or AI-processing obligation; Original Content, Revision
  `created_at`, immutable Entry `created_at`, microsecond/UUID History order,
  edit/restore atomicity and invalid-request rollback remain covered and green.
- No existing migration was edited. The migration is additive outside the
  controlled RPC replacement, preserves the previous application's named
  PostgREST arguments and return shape, and was exercised by the unchanged
  FastAPI store contract, satisfying ADR 0013's rollback compatibility window.
- No Ticket 09, Trash, deletion, AI generation, Queue, RAG, Agent, broad
  `EntryExperience` refactor, new secret, or unrelated site work was started.
- This implementation/fix session did not perform code review and does not
  claim Ticket 08 review passed. Ticket 08 remains `ready-for-agent`; the next
  step is a separate fresh fixed-range code-review session over the original
  Ticket 08 bases and the new exact repository Heads.
- Personal Website fix commit
  `7a480780aaf8090f0f610be0a04f25a02abb00e3` was pushed first. Its exact-Head
  `Website checks and Pages` run
  [30936484930](https://github.com/oscar940327/my-personal-website/actions/runs/30936484930)
  and `pages build and deployment` run
  [30936483458](https://github.com/oscar940327/my-personal-website/actions/runs/30936483458)
  both completed successfully before the Diary CI pin was changed.
- Diary CI now pins that exact Personal Website commit. The resulting Diary
  exact Head and its Actions result are reported in the implementation handoff
  after the Diary commit containing this record is pushed and verified.
