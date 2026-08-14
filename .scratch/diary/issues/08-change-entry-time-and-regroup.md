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

### 2026-08-05 - Fresh fixed-range code review requires changes

#### Findings and verdicts

- Overall verdict: **CHANGES-REQUIRED**.
- Standards verdict: **CHANGES-REQUIRED** with three blocking correctness or
  lifecycle defects, no separate documented-style violation, and two
  non-blocking smell judgements.
- Spec verdict: **CHANGES-REQUIRED** with two blocking findings.
- The two axes ran independently and inspected all 17 changed files across both
  complete fixed ranges. Passing tests were treated as evidence, not as a
  substitute for code inspection.

##### Blocking Standards findings

1. **High - the active-Entry search bound can be both too short and
   lifetime-sized.** Personal Website
   `src/diary/EntryExperience.tsx:173-182,212-216` derives the request budget
   from the previously rendered Entry count. With only the initial 20 Entries
   loaded and the moved active Entry ranked 41st on its destination date, the
   rebuild permits only the initial request plus one older request, stops after
   ranks 1-40, and throws before requesting the bounded third page containing
   the anchor. Every `Refresh History` retry repeats the same deterministic
   failure. At the other extreme, if 500 lifetime Entries were previously
   loaded, the same formula permits re-downloading approximately all 500.
   This can leave a committed Entry Time change without a recoverable History
   window or download the full lifetime History, violating the explicit
   active-Entry, bounded-search and incremental-History requirements in this
   review and `.scratch/diary/spec.md:200`.
2. **High - a pre-mutation root refresh can reinstall an old snapshot after
   rebuild or recovery.** Personal Website
   `src/diary/EntryExperience.tsx:435-460,791-822` keeps the initial/midnight
   cursorless `refreshHistory` outside `historyGeneration`, and its local
   controller cannot be aborted by the Entry Time mutation. Delay a midnight
   refresh after it obtains the old snapshot, commit the mutation, then let the
   fresh rebuild succeed or fail into cursor-cleared recovery before releasing
   the delayed response. Lines 449-453 unconditionally reinstall old Entry
   data and cursors. Stale pagination can then overwrite the committed Entry
   Time and contradict refreshed Calendar counts. This violates the required
   React async-generation and cursor/snapshot ownership lifecycle, including
   the explicit rule that old-generation responses cannot overwrite recovery.
3. **Medium - Calendar navigation does not retire stale recovery ownership.**
   Personal Website `src/diary/EntryExperience.tsx:842-872,1018-1035` leaves
   `historyRecovery` intact when the owner selects a different Calendar date
   after a rebuild failure. The normal date jump loads the newly selected
   History, but the still-visible `Refresh History` action can later replace it
   with the old recovery window and cursors while the URL and `anchorDate`
   continue to identify the selected date. This produces incoherent Calendar
   navigation and History ownership, violating the specification's
   Calendar-as-History-anchor and fresh-snapshot recovery requirements.

##### Blocking Spec findings

1. **High - the rank-41 active Entry is not found from an initial 20-Entry
   window.** Personal Website
   `src/diary/EntryExperience.tsx:173-182,212-216` allows exactly two requests
   when `targetEntryCount` is 20. If 40 destination-date Entries sort before
   the active Entry, the permitted pages return only those 40 and the rebuild
   fails before the third bounded request. The dense regression first loads 40
   Entries, which raises its budget to three and masks this initial-only case.
   Recovery retries retain the same insufficient bound. This directly violates
   this review's requirement that an active Entry behind at least 40 peers is
   actually found without downloading lifetime History.
2. **High - an in-flight old-generation cursorless response can overwrite
   recovery state.** Personal Website
   `src/diary/EntryExperience.tsx:421-471,791-831` does not give the root
   refresh a generation check or a controller shared with the mutation. The
   delayed-midnight-refresh scenario above restores old Entries and cursors
   after the committed mutation, allowing stale responses to disagree with
   Calendar and the committed Entry Time. This violates the explicit
   no-old-cursor/new-data, old-generation isolation and correct-regroup
   invariants.

The first and second items appear once under each axis because Standards and
Spec were deliberately reviewed and reported independently. There are three
unique blocking defects and five axis-specific blocking findings.

#### Non-blocking Standards judgements

- **Low - Duplicated Code.** Personal Website
  `src/diary/EntryExperience.tsx:804-809,866-872` repeats the fresh History
  window installation sequence. A small shared helper could reduce lifecycle
  drift, but this is a judgement, not mandatory Ticket 08 work.
- **Low - possible Divergent Change.** Personal Website
  `src/diary/EntryExperience.tsx:81-223,336-885,1189-1290` continues to contain
  timestamp conversion, pagination/recovery orchestration and Entry Time dialog
  rendering. This is a non-blocking smell judgement only; this review does not
  request or authorize a broad `EntryExperience` refactor.
- One verification-order observation is recorded but is not a Ticket 08 range
  finding: running `test_continuous_history.py` before
  `test_calendar_navigation.py` left shared 2099 rows visible to a pre-existing
  2090 "after last Entry" assertion, producing `38 passed, 1 failed`. The
  changed hunk in that existing test file only adapts an RPC argument cast.
  Running the same 39 focused cases in repository order passed, and the full
  suite passed in its normal order.

#### Fixed ranges and implementation Heads

- Diary implementation Head:
  `432ed2f353d86359b1810d19772a5bda6870a748`.
- Diary fixed three-dot range:
  `898a6056068ce282e36399d568ea6350bb413f29...432ed2f353d86359b1810d19772a5bda6870a748`.
- Personal Website implementation Head:
  `7a480780aaf8090f0f610be0a04f25a02abb00e3`.
- Personal Website fixed three-dot range:
  `231ebe21ed09ec7d777f3c78ed6eb58aab396962...7a480780aaf8090f0f610be0a04f25a02abb00e3`.

#### Preflight and exact-Head GitHub evidence

- Both repositories were clean at review start. Each local `HEAD` exactly
  matched its expected SHA and `origin/main`.
- Both review bases existed locally. Each `git merge-base` exactly equalled
  the requested base, both ranges were non-empty (five Diary commits and three
  Personal Website commits), and both complete-range `git diff --check`
  commands returned zero.
- GitHub contained both exact implementation commits.
- Diary `Backend checks` run
  [30936747912](https://github.com/oscar940327/diary/actions/runs/30936747912)
  matched Head `432ed2f353d86359b1810d19772a5bda6870a748` and was
  `completed/success`.
- Personal Website `Website checks and Pages` run
  [30936484930](https://github.com/oscar940327/my-personal-website/actions/runs/30936484930)
  and `pages build and deployment` run
  [30936483458](https://github.com/oscar940327/my-personal-website/actions/runs/30936483458)
  both matched Head `7a480780aaf8090f0f610be0a04f25a02abb00e3` and were
  `completed/success`. Every job returned by GitHub for all three runs was also
  `completed/success`.

#### Local verification

- Ordered Supabase `db reset` passed and applied the complete migration chain
  through `20260805120000_harden_create_entry_time_range.sql`.
- `python -m mypy src tests` passed with no issue.
- The Ticket 04-08 History, Calendar, Revision, Entry Time and real mobile
  Chromium focused set passed `39 passed in 53.57s` in repository order.
  The alternate-order `38 passed, 1 failed` observation is preserved above and
  is not reported as a pass.
- `python -m pytest -q` passed `80 passed` in `79.33s`, with the existing one
  Starlette/httpx deprecation warning.
- Personal Website `npm.cmd run typecheck` passed.
- Personal Website `npm.cmd run test:e2e` passed all `23` Chromium tests.
- Personal Website `npm.cmd run build` passed; the existing non-module-script
  Vite warnings remained informational.
- Personal Website `npm.cmd run verify:build` passed after that build.
- The green suites do not exercise the three blocking lifecycle scenarios
  above, so the review remains `CHANGES-REQUIRED`.

#### Confirmed scope and next step

- Diary backend validation, ordered migrations, Create/Change RPC
  authentication and RLS, immutable `created_at`, unchanged Entry Revisions and
  AI obligations, microsecond/UUID ordering, Python-safe direct Create
  rejection, previous application RPC compatibility, CI checkout naming and
  exact frontend pin showed no additional blocking finding.
- No secret-bearing frontend value or unrelated HOME, PROJECT, JOURNEY,
  MktAgent or VideoNote change was found. Ticket 09, Trash, deletion, AI
  generation, Queue, RAG and Agent work remain outside this range. No broad
  `EntryExperience` refactor was requested or performed.
- This session changed only this Ticket 08 review documentation. It did not fix
  findings, modify product code, tests, migrations or the CI pin, modify the
  Personal Website repository, start Ticket 09, or create a PR.
- Ticket 08 remains `ready-for-agent`; another independent Ticket 08 fix/TDD
  session is required. Ticket 09 remains blocked. The next allowed session is
  only that Ticket 08 fix/TDD session, followed later by another fresh
  fixed-range review; Ticket 09 must not begin in this review session.

### 2026-08-09 - Latest blocking review findings fixed; fresh review required

#### TDD red and green evidence

- Active Entry red used the real local Supabase, PostgreSQL RLS, PostgREST,
  FastAPI, Uvicorn and mobile Chromium seam. Starting with exactly the initial
  20 rendered Entries, moving that visible Entry behind 40 Entries on its
  destination date left only 20 rendered Entries instead of the required
  rebuilt 60-Entry window, proving the rank-41 anchor was not found.
- Stale-root red delayed a pre-mutation Taipei-midnight cursorless response.
  Releasing it after both a successful rebuild and a failed rebuild recovery
  replaced the committed `2026-07-29` Entry with the old snapshot in both
  Chromium cases.
- Calendar red first forced a committed Entry Time change into fresh-snapshot
  recovery, selected another Calendar date, and observed that the obsolete
  `Refresh History` action still had count one on the new date.
- The three exact async ownership regressions then passed `3 passed`; the
  corrected real-system initial-20/rank-41 journey passed `1 passed`.
- The existing recovery journey now also places its active Entry at rank 41,
  finds it on the bounded third page, restores a 60-Entry reading window and
  preserves fresh newer and older cursors. The complete History and Calendar
  Chromium specs passed `13 passed`, and both real-system Entry Time window
  journeys passed `2 passed`.

#### Blocking fixes and preserved scope

- Active-Entry search now has a fixed five-page budget of 20 Entries per page,
  independent of lifetime Entry count and previously loaded count. Ordinary
  window reconstruction is capped at 60 Entries; a deeper active anchor can
  use only the remaining fixed search pages. Save rebuild and `Refresh
  History` recovery call the same bounded function and keep one new snapshot,
  the reading anchor, and the resulting newer and older cursors.
- Initial refresh, Taipei-midnight refresh, Calendar jump, adjacent loading,
  Entry Time rebuild and recovery now share one History generation and one
  abort owner. Every new workflow retires the previous controller, and every
  response proves current controller and generation ownership before changing
  Entries, cursors, errors or recovery state. A delayed old cursorless response
  can no longer reinstall an old snapshot after a committed mutation.
- Calendar navigation explicitly retires and clears old-date History recovery
  before loading the newly selected date, so the old recovery action cannot
  replace the new URL, History window or cursors.
- Personal Website implementation commit:
  `774787b16b0da864100080ecd5d11a59932be6cf`. Diary CI pins that exact
  frontend commit. Neither repository was pushed in this session.
- Entry Time remains metadata-only. Capture time, Entry Revisions, Original
  Content, AI processing obligations, Asia/Taipei regrouping and counts,
  microsecond/UUID ordering, exact-once snapshots, Python-safe ranges, owner
  authorization, RLS and invalid-request atomic rollback were not weakened.
- No Ticket 09, Trash, deletion, AI Draft, Queue, RAG, Agent, non-blocking
  duplicate cleanup or broad `EntryExperience` architecture refactor was
  started. No code review ran in this implementation session.

#### Full verification

- Personal Website: `npm.cmd run typecheck` passed; the complete four-spec
  Playwright suite passed all `26` Chromium tests with four workers;
  `npm.cmd run build` and `npm.cmd run verify:build` passed.
- Diary: `python -m mypy src tests` passed; the complete
  `python -m pytest -q` suite reset and migrated real local Supabase and passed
  `80 passed` with the existing single Starlette/httpx deprecation warning.
- No new Supabase, Azure, GitHub or frontend environment variable is required.
  Ticket 08 remains `ready-for-agent` until a new fixed-range code-review
  session reviews the original Ticket 08 bases through the new repository
  Heads. Ticket 09 remains blocked and unstarted.

### 2026-08-09 - Fresh complete fixed-range code review requires changes

#### Verdicts and reviewed ranges

- Standards verdict: **CHANGES-REQUIRED**. Two blocking correctness/lifecycle
  findings were found. There was no separate documented-style violation; two
  Fowler smell judgements are non-blocking.
- Spec verdict: **CHANGES-REQUIRED**. Two blocking correctness findings and one
  non-blocking scope-drift finding were found.
- Overall verdict: **REVIEW-FAILED / CHANGES-REQUIRED**. There are three unique
  blocking defects; the midnight lifecycle defect appears independently under
  both axes.
- Diary fixed range:
  `898a6056068ce282e36399d568ea6350bb413f29...a9ca31125c18177c246799e413e9032542258ca8`
  (seven commits).
- Personal Website fixed range:
  `231ebe21ed09ec7d777f3c78ed6eb58aab396962...774787b16b0da864100080ecd5d11a59932be6cf`
  (five commits).
- Both independent reviewers and the primary reviewer inspected the complete
  ranges, including the original implementation and every blocker-fix commit,
  rather than only the latest fixes. Passing tests were treated as evidence,
  not as a substitute for code inspection.

#### Blocking Standards findings

1. **High - the accepted UTC maximum can create a Python-unreadable Taipei
   date.** Diary
   `supabase/migrations/20260804130000_restrict_entry_time_to_python_utc_range.sql:48-50,95`,
   `supabase/migrations/20260805120000_harden_create_entry_time_range.sql:1-5,70-72,137,189`,
   `src/diary_api/app.py:54-68` and `src/diary_api/entries.py:23-32` accept
   `9999-12-31T23:59:59.999999Z` as Python-safe UTC. Both Create and Change
   then derive `(entry_at at time zone 'Asia/Taipei')::date`, which is
   PostgreSQL date `10000-01-01`. The transaction commits, but Pydantic cannot
   parse that value into `EntryRecord.owner_date: date`; FastAPI returns `503`
   and detail, History and Calendar cannot read the committed Entry. The
   current tests cover `9999...-14:00` normalization overflow and PostgreSQL
   year 10000, not this valid UTC value whose owner date overflows. Enforce one
   Taipei-grouping-safe range in FastAPI, the table constraint, Create RPC and
   Change RPC (the current fixed-zone upper instant is
   `9999-12-31T15:59:59.999999Z`), and add exact-boundary Create/Change
   rollback and readback coverage.
2. **Medium - Taipei-midnight root takeover permanently strands adjacent-load
   UI ownership.** Personal Website
   `src/diary/EntryExperience.tsx:410-420,468-504,594-639,561-565,1162-1170,1235-1243`.
   Start a delayed newer/older load just before Taipei midnight. The timer's
   cursorless root refresh aborts and replaces that request's generation. The
   stale adjacent catch returns, its `finally` cannot clear `adjacentLoad`
   because it no longer owns the generation, and the root success/failure path
   does not clear it either. Fresh Entries and cursors may install, but both
   pagination controls remain disabled and the IntersectionObserver refuses
   further loads until an unrelated navigation or mutation resets state.
   Retire transport ownership and its operation-specific loading/anchor state
   together without allowing a stale `finally` to clear a newer owner, and add
   delayed-adjacent-at-midnight success/failure regressions.

#### Blocking Spec findings

1. **High - bounded rebuild searches the reading Entry instead of requiring
   the changed active Entry.** Ticket 08 requires the initial-20/rank-41 search
   to find the active moved Entry and then preserve the reading anchor, window,
   snapshot and cursors. Personal Website
   `src/diary/EntryExperience.tsx:156-225,244-258,781-786,818-845` captures the
   first visible card and prefers that unrelated `readingEntry.id` over
   `changed.id` as the sole rebuild anchor. With card A first-visible, edit the
   visible card B below it and move B behind 40 destination Entries. The first
   fresh page can already contain A and the target count, so rebuild reports
   success without searching for committed B; B disappears from the installed
   History window and recovery records the same wrong anchor. The real rank-41
   regression masks this by scrolling the moved card itself to the top before
   opening the editor
   (`tests/system/test_owner_browser_authentication.py:351-380`). Make the
   changed Entry identity mandatory in the fixed bounded search while
   separately preserving the reading anchor/window, and cover save plus
   recovery when the first-visible card differs from the moved card.
2. **Medium - Taipei-midnight root takeover can wedge bidirectional History.**
   This independently violates the explicit initial/midnight/adjacent shared
   generation-and-abort contract and the incremental bidirectional History
   requirement. The reproduction, impact and fix are the same as Standards
   finding 2. Existing delayed-root tests cover old root response versus Entry
   Time mutation success/recovery, not root takeover of an adjacent request.

#### Non-blocking findings and scope audit

- **Low - Duplicated Code (judgement only).** Personal Website
  `src/diary/EntryExperience.tsx:854-859,927-933` repeats the rebuilt History
  installation sequence. A small helper could reduce lifecycle drift, but this
  is not blocking Ticket 08 work.
- **Low - possible Divergent Change (judgement only).** Personal Website
  `src/diary/EntryExperience.tsx:153-235,338-945,1078-1096` still combines
  timestamp ordering, pagination/recovery ownership, Entry Time mutation and
  navigation. A large `EntryExperience` refactor remains explicitly outside
  this review.
- **Low - unrelated scope drift.** Personal Website `index.html:132`, commit
  `18dc585`, adds a Note Garden homepage link. It is not Ticket 08 or Ticket 09
  behavior and is not a secret, but it is unrelated work inside the fixed
  Ticket 08 range; split it from this ticket or record separate authorization.
- No Ticket 09 Trash, delete, permanent-delete, AI Draft generation, Queue,
  RAG or Agent implementation was found. A redacted added-line scan found no
  secret-like credential addition in either range, and no environment variable
  was added. No unrelated existing-site refactor was found beyond the Note
  Garden link above.

#### Preflight and exact-SHA Actions evidence

- Both worktrees were clean at review start on `main`. Local `HEAD`, local
  `origin/main`, and GitHub's remote `main` all exactly matched the requested
  Heads: Diary `a9ca31125c18177c246799e413e9032542258ca8`; Personal Website
  `774787b16b0da864100080ecd5d11a59932be6cf`.
- Both bases and Heads resolved. `git merge-base` exactly equalled each
  requested base, both ranges were non-empty (seven Diary commits and five
  Website commits), and both complete three-dot `git diff --check` commands
  returned zero.
- Diary `Backend checks` run
  [31271905570](https://github.com/oscar940327/diary/actions/runs/31271905570)
  matched the exact Head and was `completed/success`; its sole `test` job was
  also `completed/success`.
- Personal Website `Website checks and Pages` run
  [31271716205](https://github.com/oscar940327/my-personal-website/actions/runs/31271716205)
  and `pages build and deployment` run
  [31271715759](https://github.com/oscar940327/my-personal-website/actions/runs/31271715759)
  matched the exact Head and were `completed/success`. All five returned jobs
  (`build`, `deploy`, `build`, `deploy`, `report-build-status`) were
  `completed/success`.

#### Local verification

- Diary `python -m mypy src tests` passed with no issue.
- Diary unit files `tests/test_health.py tests/test_auth.py` passed `19 passed`
  with the existing Starlette/httpx deprecation warning.
- The complete Diary pytest attempt passed the locally runnable tests but all
  60 real-system cases stopped in session-fixture setup. The sandboxed attempt
  hit Supabase CLI/Bun `EPERM`; the approved non-sandbox retry established the
  external cause: Docker Desktop's Linux engine was not running. No affected
  case reached a product assertion, so this is an environment limitation, not
  a product-test failure or a local full-suite pass. Exact-SHA Actions above
  remain green.
- Personal Website `npm.cmd run typecheck` passed.
- The two complete History/Calendar Playwright specs displayed all `13` cases
  as `ok` with four workers, including rank 41, both delayed-root outcomes,
  Calendar recovery retirement and bounded recovery. The Playwright process
  did not return after the reusable Vite server teardown and was stopped by the
  outer 180-second timeout, so it is recorded as `13 cases ok`, not an exit-code
  pass. No workers, assertions, retries or serial mode were changed in range.
- Personal Website `npm.cmd run build` and `npm.cmd run verify:build` passed;
  the existing non-module script warnings remained informational.
- A direct Pydantic probe rejected `10000-01-01` as a Python `date`, confirming
  the application-side half of Standards finding 1. A 200,000-pair UUID probe
  found no disagreement between the frontend equal-time comparator and raw
  canonical UUID lexical order; this does not mitigate the blockers above.

#### Review boundary and next step

- This review changed only this Ticket 08 documentation. It did not modify
  product code, tests, migrations, CI, or the Personal Website implementation;
  it did not push, create a PR, or start Ticket 09.
- Ticket 08 **cannot close** and is not ready to prepare Ticket 09. It remains
  `ready-for-agent` for a separate fix/TDD session addressing the three unique
  blockers, followed by another fresh complete fixed-range review over the
  same original bases and new exact Heads.

### 2026-08-09 - Latest three blockers fixed; fresh review required

#### Independent session preflight

- The latest review record was preserved in an independent docs commit
  `0ebb90d08af18b5afbd26520baade43204b54ddb` before product work began.
  Its exact-SHA `Backend checks` run
  [31273774751](https://github.com/oscar940327/diary/actions/runs/31273774751)
  and `test` job completed successfully.
- Both repositories began on `main`; each local Head and `origin/main`
  matched the requested implementation Head. Personal Website had no tracked
  change. Diary had only the expected uncommitted review record, whose diff
  contained the complete latest review and no overwritten prior evidence.
- Docker Desktop's Linux engine was started and confirmed as `linux`. Existing
  ACL-denied Playwright result directories were not added to Git and no
  product code was changed to clean them.

#### Blocker 1 - Taipei-safe Entry Time range

- FastAPI red reached real Uvicorn, PostgREST, PostgreSQL RLS and Supabase:
  Change with `9999-12-31T23:59:59.999999Z` returned `503` instead of `422`
  after the database returned owner date `10000-01-01`. Direct owner-token
  Change and Create RPC calls both returned `200` and wrote the same unreadable
  owner date.
- The root cause was a UTC/Python-year upper bound that did not account for
  the fixed `Asia/Taipei` grouping conversion. The shared FastAPI validator,
  controlled Create RPC, controlled Change RPC and new table constraint now
  use `0001-01-01T00:00:00Z` through
  `9999-12-31T15:59:59.999999Z`, inclusive. Offset-required parsing and UTC
  normalization remain unchanged and validation precedes mutation.
- Ordered migration
  `20260809120000_enforce_taipei_safe_entry_time_range.sql` adds the
  `entries_entry_at_taipei_grouping_safe_range` constraint without editing or
  removing the preceding broad constraint. It replaces the two controlled RPC
  implementations with the same named arguments, security/RLS modes and
  return columns. The immediately previous FastAPI store contract continued
  to call both RPCs successfully, preserving ADR 0013 compatibility.
- Green evidence was `4 passed` across the focused real FastAPI/direct-RPC
  cases. Invalid Create and Change left Entries, Entry Revisions, AI processing
  obligations, History positions, idempotency metadata and Entry metadata
  byte-for-byte unchanged. The exact upper and lower boundaries were accepted
  and read through detail, History and Calendar with owner dates
  `9999-12-31` and `0001-01-01`; immutable capture time, Revisions and AI
  obligations remained unchanged.

#### Blocker 2 - active Entry and reading anchor are separate

- Mocked Chromium recovery red installed only `20` Entries instead of `60`:
  page one contained reading card A and met the target count, while changed
  card B appeared only on the bounded third page. The real mobile Chromium red
  used Supabase, PostgreSQL RLS, PostgREST, FastAPI and Uvicorn; after the
  committed mutation, B disappeared while A and the old date window remained.
- The root cause was the single rebuild identifier preferring A over B.
  `HistoryRecovery` now stores `activeEntryId = changed.id` independently from
  the reading anchor. Save rebuild and `Refresh History` recovery still share
  one bounded function; its loop and fail-closed condition require the active
  Entry, while A independently selects and restores the reading viewport.
- Mocked failed-rebuild recovery passed `1 passed`. The real initial-20 mobile
  journey passed `1 passed`, requested at least the bounded third page, found B
  exactly once, preserved A within the existing 8-pixel tolerance, used only
  one new snapshot, continued through fresh newer/older cursors, and kept the
  explicit rebuilt bound at no more than 100 Entries and below the 140-Entry
  lifetime fixture.

#### Blocker 3 - midnight root takeover retires adjacent state

- Clock-controlled red reproduced both outcomes. After delayed Load older and
  a successful Taipei-midnight root, `Loading older Entries` remained forever.
  After delayed Load newer and a failed root, there was no retryable History
  control. Neither failure used a larger timeout, retry, serial mode, reduced
  worker count or removed assertion.
- Root cause was transport-only retirement: the old controller/generation was
  aborted, but its `adjacentLoad`, pending reading anchor and related operation
  state stayed owned by nobody. `beginHistoryRequest` now retires those states
  together. A root request retires old cursors before loading; success installs
  fresh cursors, failure enters `unavailable` with `Retry History`, and a
  committed Entry Time recovery explicitly retires a superseded root's
  loading state. Stale `finally` blocks still require matching controller and
  generation, so they cannot clear newer state.
- The two new midnight cases passed `2 passed`; the complete delayed lifecycle
  set passed `4 passed`. Stale adjacent responses were released or aborted,
  never installed, no loading label remained, retry/root success restored
  enabled manual pagination with fresh cursors, and no old cursor was requested
  after takeover.

#### Complete local verification

- Personal Website `npm.cmd run typecheck` passed. The complete suite retained
  all prior 26 Chromium cases and added the two midnight regressions; all `28`
  passed with exactly four workers. `npm.cmd run build` and
  `npm.cmd run verify:build` passed with only the existing informational Vite
  non-module-script warnings.
- Ordered Supabase `db reset` applied every migration through
  `20260809120000_enforce_taipei_safe_entry_time_range.sql`. `python -m mypy
  src tests` passed. The Ticket 04-08 Calendar, History, Revision, Entry Time
  and real mobile set passed `40 passed`. Complete `python -m pytest -q`
  passed `81 passed` with the existing single Starlette/httpx deprecation
  warning.
- Personal Website commit
  `ee25f7e0b03a21aaa78b587f2aa19c69b9cdd767` was pushed first. Its exact-SHA
  `Website checks and Pages` run
  [31275576912](https://github.com/oscar940327/my-personal-website/actions/runs/31275576912)
  and `pages build and deployment` run
  [31275576701](https://github.com/oscar940327/my-personal-website/actions/runs/31275576701)
  were both `completed/success`. All five jobs (`build`, `deploy`, `build`,
  `deploy`, `report-build-status`) were also `completed/success` before Diary
  pinned that exact Website SHA.

#### Scope and review handoff

- Entry Time remains metadata-only. Immutable capture time, Entry Revisions,
  AI obligations, Asia/Taipei regrouping and Calendar counts,
  microsecond/UUID ordering, History snapshot exact-once, owner authorization,
  PostgreSQL RLS, invalid-request rollback and existing Create/edit/restore
  behavior remain covered and green.
- No secret or environment variable was added. Ticket 09, Trash, delete,
  permanent delete, AI Draft, Queue, RAG and Agent work were not started. The
  Note Garden link and unrelated site pages were not modified. No broad
  `EntryExperience` refactor or non-blocking duplicated-code cleanup occurred.
- This blocker-fix/TDD session did not execute code review, does not claim
  Ticket 08 review passed, and did not create a PR. Ticket 08 remains
  `ready-for-agent`; the next allowed step is a new independent complete
  fixed-range review from the original Ticket 08 bases through the new exact
  repository Heads. Ticket 09 remains blocked and must not begin.

### 2026-08-09 - Independent complete fixed-range review still requires changes

#### Verdicts and exact reviewed ranges

- Overall verdict: **REVIEW-FAILED / CHANGES-REQUIRED**. Ticket 08 remains
  `ready-for-agent`; Ticket 09 remains blocked.
- Standards axis: **CHANGES-REQUIRED**, with two blocking findings, one
  non-blocking workflow finding and two non-blocking Fowler smell judgements.
- Spec axis: **CHANGES-REQUIRED**, with two blocking findings and one
  non-blocking scope-drift finding. The newer-direction rebuild defect appears
  independently under both axes.
- Primary validation found one additional blocking regression-test defect.
  There are four unique blockers in total: three product/migration defects and
  one test-reliability defect.
- Diary fixed range:
  `898a6056068ce282e36399d568ea6350bb413f29...b8d719fddb73d7088a918453b12e4242ce7fbb7e`
  (nine commits).
- Personal Website fixed range:
  `231ebe21ed09ec7d777f3c78ed6eb58aab396962...ee25f7e0b03a21aaa78b587f2aa19c69b9cdd767`
  (six commits).
- Both independent axes and the primary reviewer inspected the complete fixed
  ranges, including the original implementation, every earlier review record
  and every blocker-fix commit. Prior implementation claims and green CI were
  treated as evidence, not as a review PASS.

#### Blocking findings

1. **High - latest Taipei-safe CHECK is not an upgrade-safe expand step.**
   Diary
   `supabase/migrations/20260809120000_enforce_taipei_safe_entry_time_range.sql:1-6`
   immediately validates the new narrower table constraint. The immediately
   preceding released contract in
   `20260805120000_harden_create_entry_time_range.sql:1-6,70-76` and the prior
   FastAPI accepted UTC instants through
   `9999-12-31T23:59:59.999999Z`. If even one such previously valid row exists,
   applying `20260809120000` fails before its RPC replacements run, blocking
   the ordered production migration. A transaction-scoped local reproduction
   removed only the new constraint, set one existing Entry to that prior-valid
   instant and attempted the exact new CHECK; PostgreSQL returned
   `check constraint ... is violated by some row`. The aborted transaction
   restored the constraint and left zero out-of-range rows. A clean `db reset`
   cannot detect this upgrade-over-existing-data case. This violates ADR 0013
   and the Ticket requirement for an ordered expand-contract migration and a
   usable immediately previous revision. The migration needs an explicit
   compatible validation/remediation sequence; this review did not implement
   one.
2. **High - bounded active-Entry rebuild can spend its entire budget in the
   wrong direction.** Personal Website
   `src/diary/EntryExperience.tsx:181-218,837-855,915-955` always follows
   `olderCursor` while it exists and consults `newerCursor` only after the older
   side is exhausted. Reproduce with reading card A on date D, editable card B
   below it, both cursors present and at least 80 older Entries; move B to D+1.
   The fresh page anchored on A excludes committed B but exposes it through the
   newer cursor. All four remaining requests go older, the five-page bound is
   exhausted, save enters recovery and every `Refresh History` repeats the
   same deterministic failure with cursors cleared. The committed active Entry
   never regains a successful fresh window. The real rank-41 regression
   `tests/system/test_owner_browser_authentication.py:259-435` covers only B
   moving to an older dense date. This violates cross-date regrouping, the
   mandatory `changed.id` search and shared bounded save/recovery behavior.
3. **Medium - Taipei-midnight root takeover can orphan a committed Entry Time
   rebuild.** Personal Website
   `src/diary/EntryExperience.tsx:410-427,478-515,848-911`. After the mutation
   commits and save starts its fresh rebuild, let the midnight timer start a
   root refresh. `beginHistoryRequest` aborts and supersedes the rebuild. The
   save catch no longer owns the generation, so it executes neither its
   successful-install path nor its committed-recovery path: the editor can
   remain open, Calendar invalidation is skipped and a root failure leaves no
   mutation-specific recovery. Existing tests cover adjacent request -> root
   takeover and old root -> mutation takeover, not root takeover after the
   committed rebuild has begun. This violates the required complete and
   consistent generation/abort ownership across root refresh, Entry Time
   rebuild and recovery.
4. **Medium - both new midnight regressions expire their owner session while
   advancing the clock.** Personal Website
   `tests/e2e/continuous-history.spec.ts:727-738,898-932` gives the synthetic
   session exactly 3,600 seconds of remaining lifetime and then advances the
   page clock by 3,601 seconds. In the required complete four-worker local run,
   both new cases returned to `Sign in to Diary`: the success case could not
   find the fresh root Entry, and the failure case repeatedly lost the
   `Retry History` button as the DOM was replaced. The result was `26 passed,
   2 failed`; the Vite server also recorded an unhandled History proxy attempt.
   The test therefore races authentication expiry instead of reliably proving
   blocker 3. No timeout, retry, serial mode, worker reduction or assertion
   weakening was used in this review.

#### Non-blocking findings

- **Low - unrelated scope drift.** Personal Website `index.html:132` adds the
  Note Garden homepage link inside the Ticket 08 range. It is not Ticket 08 or
  Ticket 09 behavior. This review preserved it exactly as instructed and did
  not request its removal.
- **Low - judgement-only smells.** Personal Website
  `src/diary/EntryExperience.tsx:864-875,938-944` duplicates fresh-window
  installation, and the component continues to combine timestamp ordering,
  pagination ownership, mutation/recovery and navigation concerns. These are
  non-blocking Fowler judgements; no duplicated-code cleanup or broad
  architecture refactor is authorized by this review.

#### Blocker and invariant audit

- Blocker 1's current-state range is consistent across FastAPI, the table
  constraint and Create/Change RPCs at
  `0001-01-01T00:00:00Z` through
  `9999-12-31T15:59:59.999999Z`. Exact boundaries read through detail,
  History and Calendar, while `9999-12-31T23:59:59.999999Z`, offsetless input,
  normalization overflow and PostgreSQL year 10000 are rejected before
  mutation. Create/Change invalid-input checks preserve Entry, Revision, AI
  obligation, History position, idempotency and metadata state. Named
  PostgREST arguments, permissions/security modes and return columns remain
  compatible in the fresh schema. **The upgrade-over-existing-data and ADR
  0013 conclusion fails because of finding 1.**
- Blocker 2's older-direction initial-20/rank-41 path passed the real seam: it
  requested a third page, found B exactly once, preserved A within eight
  pixels, used one new snapshot and fresh continuation cursors, stayed within
  the fixed 100-Entry search bound and below the 140-Entry lifetime, shared
  save/recovery behavior and failed closed when absent. **Bidirectional active
  search fails for a newer move because of finding 2.**
- Blocker 3's delayed adjacent -> midnight ownership code retires adjacent
  loading and pending anchor state, guards stale `finally`, clears old cursors
  and exposes retry after root failure. **The required regression is not
  reliable because of finding 4, and the reverse root -> committed rebuild
  takeover remains broken because of finding 3.**
- Entry Time remains metadata-only; immutable Entry capture time, Entry
  Revision rows/content/timestamps and AI processing obligations are unchanged
  by successful time changes. Asia/Taipei grouping/counts, microsecond plus UUID
  order, History membership/time-position exact-once behavior, owner FastAPI
  authorization, PostgreSQL RLS, invalid-request rollback and direct metadata
  PATCH denial passed the inspected code and real-system tests.
- Existing Create, Original Content edit and historical restore behavior passed
  the full suite. No old snapshot cursor is installed after the covered save,
  recovery, Calendar and adjacent takeover cases; the uncovered cases above
  prevent a general invariant PASS.

#### Local verification

- Docker Desktop Linux engine was available (`linux`, server 29.6.2), and
  Supabase CLI 2.109.1 was available through the project toolchain.
- Ordered `npx.cmd supabase db reset` passed and applied all migrations through
  `20260809120000_enforce_taipei_safe_entry_time_range.sql` on a clean local
  database.
- `python -m mypy src tests` passed with no issue.
- The Ticket 04-08 History, Calendar, Revision, Entry Time and three real
  mobile Chromium journeys passed `40 passed in 56.29s` in repository order.
  An initial alternate file order reproduced the already documented shared
  fixture contamination (`39 passed, 1 failed`): earlier 2099 rows invalidated
  a Calendar test's pre-existing 2090-last-Entry assumption.
- Complete `python -m pytest -q` passed `81 passed` with one existing
  Starlette/httpx deprecation warning. This exercised real local Supabase,
  PostgreSQL RLS, PostgREST, FastAPI, Uvicorn and mobile Chromium.
- Personal Website `npm.cmd run typecheck`, `npm.cmd run build` and
  `npm.cmd run verify:build` passed. Build emitted only the existing
  informational non-module-script warnings.
- The complete `npm.cmd run test:e2e -- --workers=4` ran all 28 Chromium tests
  with exactly four workers and failed `26 passed, 2 failed` for finding 4.
  Output was directed to a new review-only directory because the known old
  Playwright result directories are ACL-denied; the new directory was removed
  afterward and none of the ignored artifacts was added to Git.

#### Exact implementation-SHA GitHub Actions evidence

- Personal Website `Website checks and Pages` run
  [31275576912](https://github.com/oscar940327/my-personal-website/actions/runs/31275576912)
  matched `ee25f7e0b03a21aaa78b587f2aa19c69b9cdd767` and was
  `completed/success`; jobs `build` and `deploy` were both
  `completed/success`.
- Personal Website `pages build and deployment` run
  [31275576701](https://github.com/oscar940327/my-personal-website/actions/runs/31275576701)
  matched the same exact SHA and was `completed/success`; jobs `build`,
  `deploy` and `report-build-status` were all `completed/success`.
- Diary `Backend checks` run
  [31275722246](https://github.com/oscar940327/diary/actions/runs/31275722246)
  matched `b8d719fddb73d7088a918453b12e4242ce7fbb7e` and was
  `completed/success`; its `test` job was `completed/success`.
- The green implementation-SHA runs do not cover findings 1-3, and local
  no-retry four-worker execution exposed finding 4, so CI does not establish a
  fixed-range review PASS.

#### Scope, residual risk and next step

- No product code, test, migration or CI file was modified in this review.
  Only this Ticket 08 review record changed. No finding was fixed.
- No secret or environment variable was added. Added-line inspection found
  only existing publishable-key/access-token plumbing and synthetic test
  tokens, not credential literals.
- No Ticket 09, Trash/delete/permanent-delete, AI Draft, Queue, RAG or Agent
  implementation was found or started. The Note Garden link was not modified.
  No large refactor was performed.
- Residual coverage gaps are the exact reproductions in findings 1-3: upgrade
  with a preceding-valid late-year row, active Entry moved newer than the
  reading anchor while both cursors exist, and midnight root takeover after a
  committed rebuild starts. The latest midnight tests additionally require a
  non-expiring synthetic session before they can provide stable evidence.
- Ticket 08 is **not PASS** and remains `ready-for-agent`. The next allowed work
  is a separate Ticket 08 fix/TDD session for these blockers, followed by a new
  independent complete fixed-range review. Do not start Ticket 09.

### 2026-08-09 - Blocker-fix session stopped at required metadata-policy decision

#### Independent preflight and TDD boundary

- This was a new Ticket 08 blocker-fix/TDD implementation session, not a code
  review. It did not run a fixed-range review and does not claim Ticket 08
  passed.
- Diary started clean on `main` at
  `2db44e7526ab216f4301a1ce9cffcbe10e98935a`; Personal Website started clean
  on `main` at `ee25f7e0b03a21aaa78b587f2aa19c69b9cdd767`.
  In both repositories `HEAD` exactly matched `origin/main` and the requested
  starting SHA. The original Ticket 08 bases
  `898a6056068ce282e36399d568ea6350bb413f29` and
  `231ebe21ed09ec7d777f3c78ed6eb58aab396962` were present, were the exact
  merge-bases, and remained available for a later fresh review.
- The confirmed public seams were the ordered PostgreSQL migration boundary,
  FastAPI detail/History/Calendar, browser save/recovery, clock-controlled
  root takeover, and the real Supabase/RLS/PostgREST/FastAPI/Uvicorn/mobile
  Chromium journey. TDD began with blocker 1 because its decision gate can
  prohibit all product implementation.
- Docker Desktop's Linux engine was started and confirmed as `linux` server
  `29.6.2`. Known ignored ACL-denied Personal Website Playwright result
  directories were not read, cleaned, modified or added to Git.

#### Blocker 1 red evidence and required decision

- A real local Supabase reset stopped exactly at the immediately preceding
  schema version `20260805120000_harden_create_entry_time_range.sql`.
- PostgreSQL then held one preceding-version-valid Entry at
  `9999-12-31T16:00:00Z`, with stable Entry UUID, current Revision UUID,
  Original Content, revision number and timestamp, pending AI processing UUID
  and both obligations, attempt count, immutable capture/update metadata,
  idempotency key and current `entry_history_positions` row all recorded before
  upgrade.
- Red: `npx.cmd supabase migration up --local` returned exit code `1` while
  applying `20260809120000_enforce_taipei_safe_entry_time_range.sql`. Its first
  `alter table ... add constraint
  entries_entry_at_taipei_grouping_safe_range` statement failed because the
  preceding-version-valid row exceeds
  `9999-12-31T15:59:59.999999Z`. No RPC replacement ran.
- The failed migration transaction preserved the Entry, Entry Revision,
  Original Content, AI processing obligation, History position, idempotency
  state and metadata byte-for-byte. It did not record migration
  `20260809120000`, and the Taipei-safe constraint was absent afterward. A
  subsequent clean current `db reset` applied the complete existing chain,
  confirming again that fresh reset alone cannot cover this upgrade defect.
- No green implementation was attempted. Making the row satisfy the published
  CHECK necessarily changes, removes or relocates its current `entry_at`.
  Neither the specification nor ADR 0013 defines whether such metadata must be
  clamped, quarantined, exposed through a legacy representation, or handled by
  another owner-visible correction workflow. Preserving the old value in an
  audit column/table would retain evidence but would still require an explicit
  policy for the active Entry Time seen by current and immediately previous
  applications.
- The session therefore followed the ticket's mandatory rule not to guess an
  irreversible metadata transformation policy. Product implementation stopped
  pending an owner decision that specifies the active safe Entry Time and
  owner-visible/auditable treatment of every preceding-version-valid unsafe
  value.

#### Remaining blockers, validation and scope audit

- Blockers 2, 3 and 4 did not enter their red/green cycles because blocker 1's
  explicit decision gate stopped product implementation. No fixed-direction
  rebuild, committed-mutation takeover, or synthetic-session code/test change
  was made, and no green evidence is claimed for any blocker.
- No Personal Website product code or tests changed. No Diary product code,
  test, migration or CI file changed. The requested complete local suites,
  commits, pushes and exact-SHA GitHub Actions sequence were not run because a
  four-blocker green implementation was not available.
- No secret or environment variable was added. Ticket 09, Trash, delete,
  permanent delete, AI Draft, Queue, RAG and Agent work were not started. The
  Note Garden link and unrelated site pages were not modified. No broad
  `EntryExperience` refactor or non-blocking duplicated-code cleanup occurred.
- Ticket 08 remains `ready-for-agent`. This stopped session is not a review and
  is not Ticket 08 PASS. After the metadata policy is decided and all four
  blockers are fixed and verified in a new/continued TDD implementation
  session, Ticket 08 still requires another independent complete fixed-range
  code-review session from the original bases. Ticket 09 remains blocked.

### 2026-08-09 - Four-blocker TDD implementation completed; fresh review required

#### Session boundary and exact starting state

- This continued the Ticket 08 blocker-fix/TDD implementation session after
  the owner authorized the metadata transformation policy. It was not a code
  review, did not perform the formal fixed-range review and does not claim
  Ticket 08 PASS.
- Diary started at `2db44e7526ab216f4301a1ce9cffcbe10e98935a` with
  only the preserved stopped-session record above modified. Personal Website
  started clean at `ee25f7e0b03a21aaa78b587f2aa19c69b9cdd767`.
  Both matched `origin/main`. The original future-review bases remain Diary
  `898a6056068ce282e36399d568ea6350bb413f29` and Personal Website
  `231ebe21ed09ec7d777f3c78ed6eb58aab396962`.
- TDD used the public migration, FastAPI, History/Calendar browser and
  clock-controlled seams. Each blocker retained or obtained a failure for the
  intended reason before the smallest scoped production/test change was made.

#### Blocker 1 - upgrade-safe expand-contract migration

- **Red:** from an actual local schema stopped exactly after
  `20260805120000_harden_create_entry_time_range.sql`, two complete
  preceding-version-valid Entries above the Taipei-safe maximum caused the
  ordered upgrade to fail on the existing `20260809120000` table CHECK. The
  first red fixture proved that the failed transaction left Entry, Revision,
  Original Content, pending AI obligation, History position, idempotency and
  metadata intact. Setup-only auth-FK failures were corrected before this red
  was accepted.
- **Minimal fix:** added the new ordered expand step
  `20260807120000_audit_and_transform_taipei_unsafe_entry_times.sql`; no
  published migration was edited. In one explicit transaction it locks
  Entries, writes every unsafe original value and exact transformed value to
  immutable `entry_time_migration_audits`, then changes only active unsafe
  `entry_at` values by exactly minus 24 hours. The audit stores Entry and owner
  identity, reason, migration version and migration evidence. Its constraints
  encode the old-valid/new-safe ranges and exact shift; RLS plus grants permit
  authenticated owner reads while denying anonymous, cross-owner and owner
  writes, and a trigger rejects update/delete. Existing History positions are
  retained and the normal trigger creates the new current position.
- **Green:** the permanent system regression now creates two unsafe rows plus
  a safe control through the preceding RPC, applies the ordered upgrade and
  verifies exact microseconds and unsafe-row relative order; Entry UUID,
  Entry Revision and Original Content; AI obligation; idempotency; immutable
  capture metadata; old/new History positions; audit evidence; and current
  detail, History and Calendar reads. It verifies owner/non-owner/anonymous
  audit access, denied owner mutation, named PostgREST arguments and exact
  Create/Change return shapes, then replays the expand migration and proves all
  state unchanged. A clean zero-row reset also applies the complete order.
- Final FastAPI validation, table constraint, Create RPC and Change RPC all use
  `0001-01-01T00:00:00Z` through
  `9999-12-31T15:59:59.999999Z`. RPC permissions, RLS/security mode, named
  arguments, return shape and ordinary behavior remain compatible. Both the
  immediately previous application and current application remain usable
  after expansion; the later contract step is safe over existing data. This
  satisfies ADR 0013's expand-contract and rollback-compatibility requirement.

#### Blocker 2 - bounded rebuild direction

- **Red:** a Chromium regression gave fresh root both cursors, used reading
  card A and distinct changed Entry B, moved B from A's date to the next day
  where only the newer cursor could find it, and supplied at least 80 older
  Entries. The existing older-first logic spent all five requests without one
  newer request, so deterministic save/recovery failed to find committed B.
- **Minimal fix:** rebuild search now receives the complete committed active
  Entry, compares its new date/microsecond/UUID rank with the fresh window,
  chooses the necessary direction, and fairly searches both sides when rank is
  ambiguous. Save rebuild and Refresh History recovery use the same function.
  The existing total budget remains exactly five pages; it is independent of
  lifetime/loaded count and never downloads lifetime History.
- **Green:** both save and recovery regressions requested the required newer
  page, used one fresh snapshot and only its fresh continuation cursors, found
  B exactly once, preserved A as an independent reading anchor within viewport
  tolerance, and kept manual continuation usable. The search remained bounded
  and fail-closed: it cannot install a window missing the committed active
  Entry.

#### Blocker 3 - midnight root ownership after commit

- **Red:** clock-controlled success and failure cases committed Change Entry
  Time, delayed the new rebuild, then started Taipei-midnight root takeover.
  The old generation ownership left the editor open in the success case and
  omitted the committed mutation's `Refresh History` recovery in the failure
  case.
- **Minimal fix:** committed-mutation recovery is handed off explicitly before
  root takeover. Root success installs only its fresh snapshot/window and
  clears recovery only when it contains committed B. Root failure retains an
  explicit retryable committed recovery. Operation refs and generation checks
  prevent stale `finally` from clearing newer state; editor, pending anchor,
  Calendar invalidation and operation-specific loading state are retired or
  transferred at the ownership boundary.
- **Green:** root-success and root-failure regressions passed. They prove no old
  snapshot cursor is installed, Calendar/editor/History state agrees with the
  committed mutation, retry survives failure, and manual pagination plus
  IntersectionObserver can continue from fresh cursors. A real mobile seam
  exposed and drove removal of an early old-snapshot merge; the resulting
  relevant real-browser journey passed.

#### Blocker 4 - synthetic auth across simulated midnight

- **Red:** both midnight-adjacent cases reproduced `Sign in to Diary` after a
  3,601-second clock advance while their synthetic JWT/session had only 3,600
  seconds remaining. Saved error-context DOM showed authentication expiry, not
  a root-lifecycle assertion failure.
- **Minimal fix:** only the synthetic sessions that advance across midnight
  now receive a 48-hour lifetime. Product authentication behavior is unchanged.
  No timeout, retry, serial mode, worker reduction, lifecycle mock or relaxed
  assertion was introduced.
- **Green:** both cases remained in authenticated Diary and verified the
  History lifecycle; the complete final suite ran exactly four workers and all
  32 Chromium tests passed with exit code 0.

#### Preserved invariants and local green evidence

- Entry Time remains metadata-only. No Entry Revision is created, changed or
  deleted; immutable capture time, Original Content, AI processing obligation,
  idempotency and other metadata are preserved. Asia/Taipei regrouping and
  Calendar counts, microsecond/UUID ordering, exact-once History positions,
  cross-date/equal-timestamp cursors, reading anchor/window behavior, owner
  authentication/FastAPI authorization/PostgreSQL RLS and invalid-request
  atomic rollback remain covered. Create, edit, restore and Ticket 03-07
  behavior did not regress.
- Docker Desktop Linux engine was available (`linux`, server `29.6.2`). A clean
  ordered Supabase reset passed through the new expand step and existing
  contract migration. The true upgrade-over-existing-data regression passed.
- Diary `python -m mypy src tests` passed (`21` files); ordered Ticket 04-08
  Calendar, History, Revision, Entry Time, auth and upgrade regressions passed
  `41 passed in 99.90s`; complete `python -m pytest -q` passed `82 passed` in
  `120.69s` with only the existing Starlette/httpx deprecation warning. These
  runs exercised real Supabase, PostgreSQL RLS, PostgREST, FastAPI, Uvicorn and
  mobile Chromium.
- Personal Website typecheck, build and build verification passed. The final
  complete Chromium run was exactly `32` tests with exactly four workers:
  `32 passed` in `11.7s`, exit code `0`. Build emitted only existing
  informational non-module-script warnings. Only this session's named ignored
  result directories were eligible for cleanup; existing ACL-denied artifacts
  were untouched and nothing from them was added to Git.

#### Exact Website SHA gate and scope audit

- Personal Website was committed and pushed as
  `6a04e418fc0c3e14fdb14cfa590f39825e83c0d4`. Exact-SHA
  [Website checks and Pages run 31308076193](https://github.com/oscar940327/my-personal-website/actions/runs/31308076193)
  completed successfully; its `build` and `deploy` jobs were both
  `completed/success`.
- Exact-SHA
  [pages build and deployment run 31308075493](https://github.com/oscar940327/my-personal-website/actions/runs/31308075493)
  completed successfully; its `build`, `report-build-status` and `deploy` jobs
  were all `completed/success`. Only after those gates passed was Diary CI
  pinned to that exact Website SHA.
- Product scope stayed within the four blockers: Website changed only
  `src/diary/EntryExperience.tsx` and
  `tests/e2e/continuous-history.spec.ts`; Diary adds only the ordered migration
  and permanent upgrade regression, updates the exact Website CI pin and
  appends this preserved ticket record. No secret or production environment
  variable was added. Ticket 09, Trash/delete/permanent-delete, AI Draft,
  Queue, RAG and Agent work were not started. The Note Garden link was not
  changed. No broad `EntryExperience` refactor or non-blocking duplicated-code
  cleanup occurred, and no PR was created.
- Ticket 08 remains `ready-for-agent`. This implementation record is not a
  code review and is not Ticket 08 PASS. A separate, fresh, complete
  fixed-range code-review session must still review the original bases before
  Ticket 08 can advance. Do not start Ticket 09.

### 2026-08-09 - Fresh formal complete fixed-range review requires changes

#### Verdict and fixed review boundary

- Overall verdict: **REVIEW-FAILED / CHANGES-REQUIRED**. Ticket 08 is not
  PASS, remains `ready-for-agent`, and Ticket 09 remains blocked.
- Standards axis: **CHANGES-REQUIRED** with one blocking test-quality finding,
  one low documented-workflow violation and two non-blocking Fowler
  judgements.
- Spec axis: **CHANGES-REQUIRED** with one blocking reading-anchor finding and
  one low non-blocking scope-drift finding.
- The primary runtime finding appears independently under both axes because it
  is both unreliable required validation and an observed failure of the
  reading-anchor behavior. The axes remain separate and are not cross-ranked.
- Diary fixed range:
  `898a6056068ce282e36399d568ea6350bb413f29...b4d0e434e05ffbbf016b6905fb75fac9520737de`.
- Personal Website fixed range:
  `231ebe21ed09ec7d777f3c78ed6eb58aab396962...6a04e418fc0c3e14fdb14cfa590f39825e83c0d4`.
- Two independent read-only sub-agents reviewed Standards and Spec in
  parallel. Both inspected the complete three-dot ranges, including the
  original implementation, all fixes, migrations, tests, CI pin and preserved
  records rather than only the latest blocker-fix commits. The primary
  reviewer separately performed code inspection and local validation.

#### Fixed-range preflight

- Both repositories began clean on `main`. Local `HEAD` and `origin/main`
  exactly matched Diary
  `b4d0e434e05ffbbf016b6905fb75fac9520737de` and Personal Website
  `6a04e418fc0c3e14fdb14cfa590f39825e83c0d4`.
- Both fixed bases and endpoints resolved. Each `git merge-base` exactly
  equalled its specified base, both ranges were non-empty, and both complete
  `git diff <base>...<endpoint> --check` commands returned exit code zero.
- Diary's range contains 11 commits, newest first:
  `b4d0e43`, `2db44e7`, `b8d719f`, `0ebb90d`, `a9ca311`, `662c0b1`,
  `432ed2f`, `9946709`, `189bd18`, `8e7eb60`, `5f7362f`.
- Personal Website's range contains seven commits, newest first:
  `6a04e41`, `ee25f7e`, `774787b`, `18dc585`, `7a48078`, `7898db9`,
  `3d1e27e`.
- Diary changed files were `.github/workflows/ci.yml`, this Ticket 08 record,
  `README.md`, `src/diary_api/app.py`, `src/diary_api/entries.py`, five
  ordered Ticket 08 migrations from `20260804120000` through
  `20260809120000`, `tests/system/test_continuous_history.py`,
  `tests/system/test_entry_time.py`, `tests/system/test_migration_upgrade.py`
  and `tests/system/test_owner_browser_authentication.py`.
- Personal Website changed files were `README.md`, `index.html`,
  `src/diary/CalendarView.tsx`, `src/diary/EntryExperience.tsx`,
  `src/diary/api.ts`, `tests/e2e/calendar-navigation.spec.ts`,
  `tests/e2e/continuous-history.spec.ts` and
  `tests/e2e/diary-tracer.spec.ts`.

#### Standards report

1. **Medium - blocking test-quality finding: the required four-worker browser
   validation is not reliable.** Personal Website
   `tests/e2e/continuous-history.spec.ts:976-980` failed in the required full
   32-test Chromium run while polling the recovered reading card's viewport
   position. It expected `127.578125`, repeatedly received `99.359375`, and
   timed out after a 28.21875-pixel displacement. The run ended `31 passed,
   1 failed`, exit code 1. A no-retry isolated invocation later displayed the
   same case as `ok` in 973 ms but the Playwright/Vite process never exited and
   was terminated by the outer 180-second command deadline, exit code 124.
   Thus the changed regression cannot reliably establish its claimed green
   result, and the complete validation gate did not succeed. No timeout,
   retry, serial mode, worker reduction or assertion weakening was applied.
2. **Low - documented-standard violation, non-blocking scope drift.** Personal
   Website `index.html:132`, commit `18dc585`, adds a Note Garden homepage
   link. Diary `docs/agents/development-workflow.md:11,19` requires exactly one
   selected ticket as the active implementation unit. This unrelated retained
   change is inside the fixed Ticket 08 range. The review preserves it and
   does not request a change in this session.
3. **Low - Fowler Duplicated Code, judgement only.** Personal Website
   `src/diary/EntryExperience.tsx:917-925,982-988` repeats the rebuilt-window
   installation sequence. This is not a blocker and this review does not ask
   for cleanup.
4. **Low - possible Fowler Divergent Change, judgement only.** Personal
   Website `src/diary/EntryExperience.tsx:158-257,442-578,649-999` combines
   timestamp ordering, bounded search, generation/abort ownership, mutation
   recovery and pagination. A broad refactor remains explicitly outside
   Ticket 08 and is not requested.

The independent Standards sub-agent found no static migration, transaction,
authorization, RLS or security blocker. Primary inspection agreed: the ordered
`20260807120000` expand step locks Entries, audits every preceding-valid unsafe
row, subtracts exactly 24 hours only from active `entry_at`, preserves the old
and trigger-created current History positions, and uses forced RLS, owner-only
select grants and an update/delete rejection trigger for immutable evidence.
The later constraint and both controlled RPCs share FastAPI's Taipei-safe
range and preserve their named arguments, security mode, permissions and
return shape. Residual Standards gaps are direct DELETE-rejection coverage for
the audit and launching a separately built immediately previous FastAPI
binary; these are coverage gaps, not findings.

#### Spec report

1. **Medium - blocking: recovery does not reliably preserve the loaded
   History reading anchor.** The required full four-worker run reproduced an
   owner-visible 28.21875-pixel displacement in Personal Website
   `tests/e2e/continuous-history.spec.ts:976-980` after a committed Entry Time
   change entered `Refresh History` recovery. The implementation assigns the
   saved reading anchor at
   `src/diary/EntryExperience.tsx:982` and attempts restoration immediately
   plus once in `requestAnimationFrame` at
   `src/diary/EntryExperience.tsx:483-494`, but it did not converge within the
   existing five-second assertion window in the complete run. The later
   isolated `ok` makes the behavior timing-dependent rather than curing the
   observed failure. This violates `.scratch/diary/spec.md:47,200`, which
   requires explicit visual scroll anchoring in bidirectional History, and it
   prevents the mandatory complete local validation from succeeding. This
   review records the finding without diagnosing or implementing a fix.
2. **Low - non-blocking scope drift.** Personal Website `index.html:132` adds
   the Note Garden homepage link, while Ticket 08
   `.scratch/diary/issues/08-change-entry-time-and-regroup.md:3-17` is limited
   to Entry Time mutation/regrouping and the MVP preserves unrelated existing
   site behavior (`.scratch/diary/spec.md:15,158,193`). The link is retained
   exactly as instructed and is not a Ticket 09 change.

Apart from the runtime anchor finding, the independent Spec sub-agent and
primary inspection found the complete Ticket 08 contract implemented:

- Entry Time remains metadata-only; immutable Entry capture time, every Entry
  Revision, Original Content, AI processing obligations, idempotency and other
  metadata are preserved.
- Asia/Taipei regrouping and Calendar counts, microsecond/UUID ordering,
  cross-date and equal-time cursors, snapshot membership exact-once,
  stale-cursor exclusion, owner FastAPI authorization, PostgreSQL RLS and
  invalid-request atomic rollback are covered.
- The true upgrade begins from the schema immediately after
  `20260805120000_harden_create_entry_time_range.sql`, handles zero and
  multiple unsafe rows transactionally, stores exact before/after timestamps,
  Entry/owner identity, reason, migration version/time evidence, and replays
  idempotently without changing preserved state.
- Table, FastAPI, Create RPC and Change RPC use inclusive
  `0001-01-01T00:00:00Z` through
  `9999-12-31T15:59:59.999999Z`; offsets are required and UTC normalization
  overflow is rejected. Current detail, History and Calendar reads, and both
  current and immediately previous application RPC contracts remain usable,
  consistent with ADR 0013.
- Bounded rebuild treats reading A and changed B separately, requires B,
  fairly searches the necessary newer side despite at least 80 older Entries,
  uses one fresh snapshot and its cursors, keeps a fixed total five-page
  budget, installs B exactly once, shares save/recovery behavior and fails
  closed when B is absent.
- Midnight root success/failure retains committed-mutation ownership or an
  explicit retryable recovery, retires editor/loading/pending-anchor state,
  blocks stale finally cleanup and continues manual pagination and
  IntersectionObserver from fresh cursors.
- Only synthetic sessions that cross simulated midnight use the 48-hour
  lifetime. Product authentication is unchanged, and no retry, serial mode,
  worker reduction or weakened assertion was added.
- Existing Create, Original Content edit, revision restore and Ticket 03-07
  behavior passed the backend system suites. Residual Spec gaps are exact-
  extrema execution through an actual previous FastAPI binary and browser
  editing of a year-0001 Entry; real backend boundary coverage exists, so
  these are not findings.

#### Local read-only validation

- Docker Desktop was available as Linux engine `29.6.2`.
- `npx.cmd supabase db reset` passed and applied the complete ordered chain
  through `20260807120000_audit_and_transform_taipei_unsafe_entry_times.sql`
  and `20260809120000_enforce_taipei_safe_entry_time_range.sql`.
- The true upgrade-over-existing-data command
  `python -m pytest -q tests/system/test_migration_upgrade.py` passed
  `1 passed in 75.81s`.
- `python -m mypy src tests` passed with no issue in 21 source files.
- The ordered focused Calendar, History, Create, Revision, Entry Time,
  migration, owner-auth and real mobile Chromium set passed
  `62 passed in 107.27s`.
- Complete `python -m pytest -q` passed `82 passed in 126.93s` with the one
  existing Starlette/httpx deprecation warning. These tests exercised the
  real local Supabase, PostgreSQL RLS, PostgREST, FastAPI, Uvicorn and mobile
  Chromium seam.
- Personal Website `npm.cmd run typecheck`, `npm.cmd run build` and
  `npm.cmd run verify:build` passed. Build emitted only existing informational
  non-module-script warnings.
- The required full browser command was run with exactly four workers and only
  an ignored review-output override:
  `npm.cmd run test:e2e -- --workers=4 --output=test-results/ticket08-fixed-review-b4d0e43`.
  It ran all 32 Chromium tests and failed `31 passed, 1 failed`, exit code 1,
  for the Standards/Spec finding above. Therefore complete local validation
  did not succeed.
- The isolated no-retry diagnostic displayed the failed case as `ok` but did
  not return before the 180-second outer deadline. Both exact review-only
  ignored output directories created by this session were removed afterward.
  Existing ACL-denied Playwright result directories were not read, modified,
  added to Git or cleaned.

#### Exact implementation-SHA GitHub Actions evidence

- Personal Website `Website checks and Pages` run
  [31308076193](https://github.com/oscar940327/my-personal-website/actions/runs/31308076193)
  matched `6a04e418fc0c3e14fdb14cfa590f39825e83c0d4` and was
  `completed/success`, attempt 1. Jobs `build` (`93231495371`) and `deploy`
  (`93231606290`) were both `completed/success`; all returned steps were also
  `completed/success`.
- Personal Website `pages build and deployment` run
  [31308075493](https://github.com/oscar940327/my-personal-website/actions/runs/31308075493)
  matched the same Website SHA and was `completed/success`, attempt 1. Jobs
  `build` (`93231495530`), `report-build-status` (`93231542952`) and `deploy`
  (`93231542977`) were all `completed/success`; all returned steps were also
  `completed/success`.
- Diary `Backend checks` run
  [31308300883](https://github.com/oscar940327/diary/actions/runs/31308300883)
  matched `b4d0e434e05ffbbf016b6905fb75fac9520737de` and was
  `completed/success`, attempt 1. Its `test` job (`93232048634`) and every
  returned step were `completed/success`.
- These green exact-SHA implementation runs do not override the required local
  four-worker failure because that failed behavior is inside their claimed
  coverage and the formal review requires complete successful local
  validation.

#### Scope, secret and modification audit

- No `.env` file changed in either fixed range. A redacted added-line scan of
  implementation files found no credential-shaped token, private key, JWT or
  committed secret. References were limited to existing configuration/token
  plumbing, roles and synthetic test values. No new production environment
  variable is introduced.
- No Ticket 09, Trash, delete, permanent delete, AI Draft generation, Queue,
  RAG or Agent implementation was found or started. This review did not start
  Ticket 09.
- The pre-existing-in-range Note Garden link is the low scope finding above;
  it was not modified by the latest blocker fix or by this review. No other
  unrelated existing-site change was found.
- No broad `EntryExperience` refactor or non-blocking duplicated-code cleanup
  was performed or requested. No PR was created.
- This review changed only this Ticket 08 documentation. It did not modify
  product code, tests, migrations, CI or Personal Website files, and it did
  not fix any finding.

#### Final axis counts and next step

- Standards: four findings total — one Medium blocking test-quality finding,
  one Low documented-workflow violation and two Low non-blocking Fowler
  judgements. The most severe Standards item is the Medium unreliable required
  browser validation finding.
- Spec: two findings total — one Medium blocking reading-anchor finding and
  one Low non-blocking scope-drift finding. The most severe Spec item is the
  Medium recovery reading-anchor failure.
- There is no cross-axis winner. Because both axes contain a blocking finding
  and complete local validation failed, the final verdict is
  **CHANGES-REQUIRED**. Ticket 08 is not PASS.
- The next allowed work is a separate Ticket 08 implementation/TDD session to
  resolve and stabilize the reading-anchor/validation defect, followed by
  another fresh complete fixed-range code review. A next independent session
  may not start Ticket 09 yet, and this review session did not start it.

### 2026-08-09 - Recovery reading-anchor blocker fixed; fresh review required

#### Session boundary and preflight

- This was a new Ticket 08 blocker-fix implementation/TDD session, not a code
  review. It did not run the formal fixed-range review and does not claim
  Ticket 08 PASS.
- Diary began clean on `main` at
  `003fbcd942b128ad87776b296cd04fca644d4c77`; Personal Website began clean on
  `main` at `6a04e418fc0c3e14fdb14cfa590f39825e83c0d4`. In both repositories local
  `HEAD` and `origin/main` matched the requested starting SHA exactly.
- The governing repository documents, complete Ticket 08 history, relevant
  ADRs and the `diagnosing-bugs`, `implement` and `tdd` skills were read before
  product work. The public seam remained the existing Chromium History
  recovery journey and its original viewport assertion.
- Docker Desktop was confirmed as Linux engine `29.6.2`. Existing ignored,
  ACL-denied Playwright result directories were not read, modified, added to
  Git or cleaned. Only this session's exact ignored output directories were
  removed after validation.

#### Deterministic red and root cause

- The first fresh complete baseline ran all 32 Chromium cases with four
  workers and returned `32 passed`, exit code `0`. A subsequent independent
  full run displayed all 32 cases as `ok` but never printed the summary or
  returned; its first process reached the 180-second outer deadline and ended
  with exit code `124`, so none of the later loop iterations started.
- Runner instrumentation with `DEBUG=pw:webserver` showed the hang after
  Playwright logged `Terminating the WebServer`; Vite was available and the
  browser case had already finished. Starting Vite directly instead of
  through `npm run dev` reproduced the same boundary, falsifying an npm-wrapper
  cause. The Windows Playwright-managed webServer teardown was waiting for its
  spawned process `close` event and could not provide a reliable exit code.
- Because the original recovery case was timing-dependent, a third case was
  added at the same public UI seam. It retains the original assertion and
  tolerance, keeps reading Entry A separate from committed Entry B, disables
  native scroll-anchor compensation and releases a controlled browser font
  readiness boundary only after the existing immediate plus one-frame manual
  restoration. Red command:
  `npm.cmd run test:e2e -- --workers=4 --grep="after a delayed layout change"`
  (with a new ignored output directory). It failed for the intended viewport
  symptom with expected `127.578125`, received `126.359375`, displacement
  `1.21875px`, exit code `1`. Another independent attempt displayed the same
  case as failed before the separate teardown hang ended at exit code `124`.
- The root cause was timing-dependent anchor ownership. The History commit
  cleared `pendingHistoryAnchor` immediately and retained the captured anchor
  only through one `requestAnimationFrame`. Font metrics can settle after that
  boundary, so the final viewport position depended on Chromium's native
  scroll-anchor choice. The formal four-worker failure's `28.21875px`
  displacement and the deterministic native-compensation-off red are two
  manifestations of the same prematurely retired manual anchor.

#### Minimal green implementation

- `EntryExperience` still restores immediately and on the next animation
  frame, but the same captured anchor closure now remains owned through
  `document.fonts.ready` and performs the same immediate-plus-frame correction
  after font layout settles. Cleanup cancels every owned frame and prevents an
  obsolete effect from restoring after a later Entries generation.
- The regression controls only the browser font-loading boundary. It does not
  change the existing viewport assertion, timeout, tolerance, retry policy,
  worker count or execution mode. The new case passed with exit code `0`.
- The required npm command now starts one fresh Vite server through Vite's
  public Node API, launches Playwright as a child with all original CLI
  arguments, propagates its exact exit code, then awaits `server.close()`.
  Playwright observes that process-local server without owning its teardown.
  Debug green showed `Terminating the WebServer` immediately followed by
  `Terminated the WebServer` and exit code `0`. No server is reused across
  independent npm invocations.
- Search/rebuild code was unchanged. Save and `Refresh History` recovery still
  share the fixed five-page function, require committed B, preserve reading A
  independently, use one fresh snapshot and only its fresh cursors, install B
  exactly once and fail closed when B is absent. Manual pagination and the
  IntersectionObserver continue from the installed fresh cursors.

#### Complete local validation

- Personal Website `npm.cmd run typecheck` passed. The focused save, recovery
  and delayed-layout set passed `3 passed`, exit code `0`.
- Three independent fresh-process executions of
  `npm.cmd run test:e2e -- --workers=4` used exactly four workers, no retry and
  ran all 33 Chromium tests. They passed `33/33` in `13.9s`, `13.6s` and
  `13.1s`; every run returned exit code `0` and no run hung.
- Personal Website `npm.cmd run build` and `npm.cmd run verify:build` passed.
  Build emitted only the existing informational non-module-script warnings.
- A clean ordered local Supabase reset applied every migration through
  `20260807120000_audit_and_transform_taipei_unsafe_entry_times.sql` and
  `20260809120000_enforce_taipei_safe_entry_time_range.sql`.
- The true upgrade-over-existing-data regression passed `1 passed in 74.86s`.
  `python -m mypy src tests` passed for 21 source files.
- The explicitly ordered Ticket 03-08 Calendar, History, Create, Revision,
  Entry Time, migration, owner-auth and mobile Chromium set passed
  `62 passed in 111.99s`. Complete `python -m pytest -q` passed
  `82 passed in 134.20s` with only the existing Starlette/httpx deprecation
  warning. These runs exercised real local Supabase, PostgreSQL RLS,
  PostgREST, FastAPI, Uvicorn and mobile Chromium.

#### Preserved invariants and scope audit

- Entry Time remains metadata-only. Immutable capture time, Original Content,
  every Entry Revision and AI processing obligation remain unchanged. No
  revision is created, modified or deleted by a time-only change.
- Asia/Taipei regrouping and Calendar counts, microsecond/UUID ordering,
  cross-date and equal-timestamp cursors, exact-once snapshot history, no
  old-snapshot cursor reuse, invalid-request atomic rollback, owner FastAPI
  authorization, PostgreSQL RLS and existing Create/edit/restore plus Ticket
  03-07 behavior remained green.
- Personal Website changed only `package.json`, `playwright.config.ts`,
  `scripts/run-playwright.mjs`, `src/diary/EntryExperience.tsx` and
  `tests/e2e/continuous-history.spec.ts`. Diary changes only the exact Website
  CI pin and this appended Ticket 08 record; no Diary product, test or
  migration file changed.
- No secret or production environment variable was added. The runner's
  `DIARY_E2E_SERVER_READY` marker and existing synthetic publishable key are
  process-local test configuration only. Added-line credential-pattern scan
  returned zero.
- Ticket 09, Trash, delete, permanent delete, AI Draft, Queue, RAG, Agent,
  Note Garden and unrelated site pages were not modified or started. No broad
  `EntryExperience` refactor, non-blocking duplicated-code cleanup or PR was
  created.

#### Exact commits, Actions and fresh-review handoff

- Personal Website implementation commit
  `4f47c1d4c36a78f9c49df8885515e3143d34cbb2` was pushed first.
  [Website checks and Pages run 31320314343](https://github.com/oscar940327/my-personal-website/actions/runs/31320314343)
  was `completed/success`; jobs `build` (`93262103173`) and `deploy`
  (`93262219737`) were both `completed/success` at that exact head SHA.
- [pages build and deployment run 31320314136](https://github.com/oscar940327/my-personal-website/actions/runs/31320314136)
  was `completed/success`; jobs `build` (`93262103948`), `deploy`
  (`93262151373`) and `report-build-status` (`93262151375`) were all
  `completed/success` at the same exact SHA. Only after both exact-SHA gates
  passed was Diary CI pinned to that Website commit.
- The Diary commit containing the CI pin and this record is reported in the
  final implementation handoff after its exact-SHA `Backend checks` run and
  `test` job finish successfully.
- Ticket 08 remains `ready-for-agent`. The original bases for the next fresh
  fixed-range review remain Diary
  `898a6056068ce282e36399d568ea6350bb413f29` and Personal Website
  `231ebe21ed09ec7d777f3c78ed6eb58aab396962`; its new Website endpoint is
  `4f47c1d4c36a78f9c49df8885515e3143d34cbb2`, and the new Diary endpoint is
  the commit containing this record. The next step is only a new independent
  complete Ticket 08 fixed-range code-review session. Ticket 09 remains
  blocked and unstarted.

#### Diary exact-SHA completion evidence

- Diary implementation/pin/record commit
  `aa07c8f0eba44693dd552a6d4bac09927745e3b3` was pushed after both Website
  workflows were green.
- [Backend checks run 31320499489](https://github.com/oscar940327/diary/actions/runs/31320499489)
  matched that exact Diary SHA and was `completed/success`; its `test` job
  (`93262589771`) was also `completed/success` at the same exact head SHA.
- The documentation-only commit that adds this completion evidence is the
  final Diary endpoint reported in the implementation handoff after its own
  exact-SHA Backend checks completes successfully.

### 2026-08-10 - Fresh formal complete fixed-range review requires changes

#### Verdicts and fixed review boundary

- Overall verdict: **REVIEW-FAILED / CHANGES-REQUIRED**. Ticket 08 is not
  PASS, remains `ready-for-agent`, and Ticket 09 remains blocked.
- Standards axis: **PASS** with zero blocking findings and three non-blocking
  findings: one retained documented-workflow breach and two Fowler smell
  judgements.
- Spec axis: **CHANGES-REQUIRED** with one High blocking finding and one Low
  non-blocking scope-drift finding.
- There is one unique blocking defect. The axes were reviewed independently
  and are not cross-ranked. Passing tests were treated as evidence rather than
  as a substitute for code inspection.
- Diary fixed range:
  `898a6056068ce282e36399d568ea6350bb413f29...118985d5a891b8807be97509ca179557bc78a173`
  (14 commits).
- Personal Website fixed range:
  `231ebe21ed09ec7d777f3c78ed6eb58aab396962...4f47c1d4c36a78f9c49df8885515e3143d34cbb2`
  (8 commits).
- Two isolated read-only sub-agents reviewed Standards and Spec in parallel as
  required by the `code-review` skill. The primary reviewer separately
  inspected the complete ranges, including the original implementation, every
  blocker fix, migrations, tests, runner change, CI pin and preserved records.

#### Preflight

- Both repositories began clean. Diary local `HEAD` and `origin/main` exactly
  matched `118985d5a891b8807be97509ca179557bc78a173`; Personal Website local
  `HEAD` and `origin/main` exactly matched
  `4f47c1d4c36a78f9c49df8885515e3143d34cbb2`.
- Both requested bases and endpoints resolved. Each `git merge-base` exactly
  equalled its requested base, both ranges were non-empty, and both complete
  three-dot `git diff --check` commands returned exit code zero.
- Preflight read the complete `code-review` skill, `AGENTS.md`, development
  workflow, domain and issue-tracker guidance, `CONTEXT.md`, the complete MVP
  spec, this complete Ticket 08 record, and all 15 ADRs under `docs/adr/`.
- No stash, reset, checkout, cleanup of user files, PR creation or remote write
  occurred.

#### Standards report

1. **Low - documented workflow breach, non-blocking retained scope drift.**
   Personal Website `index.html:132`, commit `18dc585`, adds the Note Garden
   homepage link. Diary `docs/agents/development-workflow.md:3,11,19-20`
   requires one selected ticket and no unrelated feature in the active unit.
   This pre-existing-in-range change was recorded only and was not modified.
2. **Low - Fowler Duplicated Code, judgement only.** Personal Website
   `src/diary/EntryExperience.tsx:934-940,999-1005` repeats rebuilt-window
   installation. This is non-blocking and no cleanup is requested or
   authorized by this review.
3. **Low - possible Fowler Divergent Change, judgement only.** Personal
   Website `src/diary/EntryExperience.tsx:158-257,442-578,666-1017` combines
   timestamp ordering, bounded pagination, generation/abort ownership,
   midnight refresh, mutation recovery and viewport restoration. A broad
   `EntryExperience` refactor remains explicitly outside Ticket 08.

The Standards axis found no blocking migration, transaction, authorization,
RLS, security or runner-lifecycle defect. The fixed five-request budget, fresh
snapshot/cursor ownership, changed-Entry fail-closed check, guarded stale
responses/finally cleanup, manual pagination, IntersectionObserver, font-ready
manual restoration, explicit Vite close and Playwright exit-code propagation,
midnight ownership, Calendar recovery retirement, Taipei migration, metadata-
only mutation and Ticket 03-07 seams showed no additional Standards finding.

#### Spec report

1. **High - blocking: a deep reading Entry A can disappear even when changed
   Entry B is found.** The specification requires preserved visual anchoring
   for bidirectional History at `.scratch/diary/spec.md:47,200`. Personal
   Website `src/diary/EntryExperience.tsx:158-187,248-256` caps ordinary
   reconstruction at 60 Entries and terminates once that target and changed B
   are present. Save and recovery store A only as a DOM reading anchor and
   anchor date, while B alone is the mandatory active Entry at
   `src/diary/EntryExperience.tsx:890-935`; restoration returns false without
   recovery when A is absent at
   `src/diary/EntryExperience.tsx:292-301`. With more than 60 Entries already
   loaded, A can be first-visible below the reconstruction target and B can be
   immediately below it. Moving B newer lets the fresh root/newer search find
   B and stop with no A, so the required viewport cannot be restored. The
   changed regression always places A in the fresh initial page at
   `tests/e2e/continuous-history.spec.ts:776-807,923-935,985-1032`, so its green
   result does not cover this path. This also contradicts the recorded
   independent A/B preservation requirement at this ticket's lines
   1303-1319 and 1725-1729.
2. **Low - non-blocking known scope drift.** Personal Website
   `index.html:132` adds Note Garden outside Ticket 08's Entry-Time-only scope
   (`.scratch/diary/issues/08-change-entry-time-and-regroup.md:3-17`) and the
   existing-site preservation boundary (`.scratch/diary/spec.md:15,158,193`).
   It was recorded only and not modified.

No additional Spec finding was found for Entry Time metadata-only behavior,
immutable capture/Revision/Original Content/AI obligations, Taipei extrema and
true upgrade migration, History exact-once positions, five-request B search,
one fresh snapshot and only its cursors, fail-closed recovery, Calendar
retirement, midnight root success/failure, stale loading ownership, manual
pagination, IntersectionObserver, font/layout timing, fresh runner exit,
auth/RLS or Ticket 03-07 behavior. The blocker above prevents those passing
checks from establishing a complete Ticket 08 PASS.

#### Complete local validation

- Personal Website `npm.cmd run typecheck` passed, exit code zero.
- Three independent fresh-process executions of
  `npm.cmd run test:e2e -- --workers=4` each used exactly four workers, no
  retry, and ran all 33 Chromium tests:
  - run 1: `33 passed` in `15.8s`, exit code `0`, no hang;
  - run 2: `33 passed` in `12.6s`, exit code `0`, no hang;
  - run 3: `33 passed` in `12.7s`, exit code `0`, no hang.
- Each browser run used its own new ignored review-specific output directory.
  The three exact directories were removed afterward. Existing ignored,
  ACL-denied Playwright result directories were not listed, read, modified,
  added to Git or cleaned. Post-summary mock proxy `ECONNREFUSED` teardown
  messages did not affect assertions, return, or any exit code.
- Personal Website `npm.cmd run build` and `npm.cmd run verify:build` passed,
  each with exit code zero. Build emitted only existing informational Vite
  non-module-script warnings.
- Docker Desktop was available as Linux engine `29.6.2`.
- Clean ordered `npx.cmd supabase db reset` passed and applied every migration
  through `20260807120000_audit_and_transform_taipei_unsafe_entry_times.sql`
  and `20260809120000_enforce_taipei_safe_entry_time_range.sql`.
- The true upgrade-over-existing-data regression
  `python -m pytest -q tests/system/test_migration_upgrade.py` passed
  `1 passed in 72.53s`, exit code zero.
- `python -m mypy src tests` passed with no issue in 21 source files.
- The repository-safe ordered Ticket 03-08 Calendar, History, Create,
  Revision, Entry Time, migration, owner-auth and real mobile Chromium set
  passed `62 passed in 109.03s`, exit code zero.
- Complete `python -m pytest -q` passed `82 passed in 130.13s`, exit code zero,
  with the one existing Starlette/httpx deprecation warning. These runs
  exercised real local Supabase, PostgreSQL RLS, PostgREST, FastAPI, Uvicorn
  and mobile Chromium.

#### Exact-SHA GitHub Actions evidence

- Personal Website
  [Website checks and Pages run 31320314343](https://github.com/oscar940327/my-personal-website/actions/runs/31320314343)
  matched `4f47c1d4c36a78f9c49df8885515e3143d34cbb2`, attempt 1, and was
  `completed/success`. Jobs `build` (`93262103173`) and `deploy`
  (`93262219737`) matched the same head SHA and were `completed/success`.
- Personal Website
  [pages build and deployment run 31320314136](https://github.com/oscar940327/my-personal-website/actions/runs/31320314136)
  matched the same exact Website SHA, attempt 1, and was
  `completed/success`. Jobs `build` (`93262103948`), `deploy`
  (`93262151373`) and `report-build-status` (`93262151375`) matched that SHA
  and were `completed/success`.
- Diary implementation/pin record
  [Backend checks run 31320499489](https://github.com/oscar940327/diary/actions/runs/31320499489)
  matched `aa07c8f0eba44693dd552a6d4bac09927745e3b3`, attempt 1, and was
  `completed/success`; job `test` (`93262589771`) matched that SHA and was
  `completed/success`.
- Diary final documentation endpoint
  [Backend checks run 31320804698](https://github.com/oscar940327/diary/actions/runs/31320804698)
  matched `118985d5a891b8807be97509ca179557bc78a173`, attempt 1, and was
  `completed/success`; job `test` (`93263365751`) matched that SHA and was
  `completed/success`.

#### Scope, secret and modification audit

- No `.env` file changed in either range. A redacted added-line scan found no
  credential-shaped token, private key, JWT or committed secret. No new
  production environment variable was added. Website's
  `DIARY_E2E_SERVER_READY` and synthetic publishable-key/API URL assignments
  are process-local test-runner configuration only.
- No Ticket 09, Trash/delete/permanent-delete, AI Draft generation, Queue,
  RAG or Agent implementation was found or started. Ticket 09 remains blocked.
- The existing Note Garden link is the retained non-blocking scope finding
  above. It was not modified by this review. No other unrelated existing-site
  change was found.
- No broad `EntryExperience` refactor or non-blocking cleanup was performed.
  This session fixed no finding, modified no product code/test/migration/CI or
  Personal Website file, created no PR, and started no Ticket 09 work.

#### Final axis counts and next step

- Standards: three findings total, zero blocking and three non-blocking. The
  most severe Standards item is the Low retained documented-workflow breach;
  Standards verdict is **PASS**.
- Spec: two findings total, one High blocking and one Low non-blocking. The
  most severe Spec item is the deep reading-Entry A viewport-loss defect;
  Spec verdict is **CHANGES-REQUIRED**.
- Because the Spec axis contains a blocking finding, the formal final verdict
  is **CHANGES-REQUIRED** even though every required local command and exact-
  SHA Actions gate succeeded. Ticket 08 remains `ready-for-agent` and Ticket
  09 must not begin. A separate Ticket 08 implementation/TDD session is
  required before another fresh complete fixed-range review.

### 2026-08-10 - Deep reading Entry blocker fixed; fresh review required

#### Session boundary, starting state and preservation gate

- This was a new formal Ticket 08 implementation/TDD session. It did not run
  code review, does not claim Ticket 08 PASS, did not create a PR and did not
  start Ticket 09.
- The complete `implement` and `tdd` skills and required TDD references were
  read. Preflight also read `AGENTS.md`, development workflow, domain and
  issue-tracker guidance, `CONTEXT.md`, the complete MVP spec, this complete
  Ticket 08 record, and ADRs 0001, 0004, 0005, 0013, 0014 and 0015.
- Diary began on `main` at
  `118985d5a891b8807be97509ca179557bc78a173`, exactly matching
  `origin/main`, with only the specified append-only formal review record
  modified. Personal Website began clean on `main` at
  `4f47c1d4c36a78f9c49df8885515e3143d34cbb2`, exactly matching
  `origin/main`.
- Inspection proved the Diary diff was only the complete EOF append headed
  `2026-08-10 - Fresh formal complete fixed-range review requires changes`;
  no prior record was overwritten or removed. It was preserved first in the
  independent docs-only commit
  `237e0eac087aabe689ec14d8599f7d7e04221d04` and pushed to Diary `main`.
- [Backend checks run 31324913118](https://github.com/oscar940327/diary/actions/runs/31324913118)
  matched that exact docs-only SHA, attempt 1, and was `completed/success`.
  Its `test` job
  [93273625555](https://github.com/oscar940327/diary/actions/runs/31324913118/job/93273625555)
  matched the same SHA and was `completed/success`. Both tracked worktrees
  were rechecked clean before product work began.

#### Confirmed blocker, public seam and deterministic red

- The confirmed blocker was the formal review's High Spec finding: a deep
  reading Entry A could disappear from a rebuilt History window after changed
  Entry B was found. Root cause was not reopened as a broad diagnosis.
- The pre-agreed seam remained the public Playwright History UI: public Change
  Entry Time actions, History API requests, rendered Entry cards, viewport
  position, manual pagination and the existing IntersectionObserver behavior.
  No private helper or implementation-detail test was added.
- One new owner journey first used public `Load older Entries` controls to
  install 80 Entries. A was first-visible at approximately rank 78, B was a
  distinct Entry immediately below A, and B moved into the fresh newer
  direction. The fresh root and first two older pages met the ordinary
  60-Entry target without A; A remained findable only on the fifth and final
  allowed request.
- Red command used exactly the new public-seam journey, no retry and a new
  ignored session output directory. It returned exit code `1`: `1 failed`.
  Save found B and installed the rebuilt window, but
  `#entry-deep-reading-a` was owner-visibly absent: expected count `1`,
  received `0`. Authentication, fixture setup, Vite lifecycle and teardown
  were healthy; the failure was the intended Entry-presence/viewport defect.

#### Minimal implementation and green evidence

- `HistoryRecovery` now retains `readingEntry` independently from
  `activeEntry`. A remains the manual viewport owner; B remains the committed
  mutation owner. The concepts are not substituted for one another.
- Save and `Refresh History` recovery still call the same
  `rebuildHistoryWindow`. Its ordinary target remains capped at 60 Entries and
  its total budget remains exactly five pages: one fresh cursorless root plus
  at most four requests. The budget does not depend on lifetime or previously
  loaded count.
- The shared loop now treats both distinct A and B as mandatory. Direction
  selection considers every missing mandatory Entry, so it first obtains
  newer B and then continues older to deep A. The final guard throws unless
  both are present; therefore no rebuilt window missing A or B can install,
  and committed failure remains retryable through the existing recovery.
- The regression exercises both vertical paths in the same test. Save uses
  exactly five requests and succeeds. A second committed time change forces
  the first cursorless rebuild to return `503`; `Refresh History` starts
  another fresh root and uses only that root's `fresh-deep-2-*` cursors,
  exactly five total requests, and then succeeds. Neither rebuild requests an
  `old-deep-*` cursor.
- Both paths render A and B exactly once and preserve A with the unchanged
  `toBeCloseTo(..., 0)` viewport assertion. Native scroll anchoring is
  disabled in the regression. Test setup waits for the preceding manual
  pagination owner's `document.fonts.ready` and animation frames before the
  measurement; product restoration retains its existing manual
  immediate/frame/font-ready ownership.
- After recovery, public manual newer and older pagination continued through
  the installed fresh cursors. The complete suite's existing wheel-driven
  IntersectionObserver regression also remained green. Midnight root
  success/failure, stale finally, loading state, Calendar recovery retirement
  and the fresh-process Vite/Playwright runner were unchanged and green.
- Focused new journey green: `1 passed in 2.9s`, exit code `0`. The expanded
  save/recovery/font blocker set passed `4 passed in 5.6s`, exit code `0`.
  After an over-broad root-recovery condition caused an intermediate complete
  run to report `32 passed, 2 failed`, that non-required root change was
  removed. The deep-A plus midnight focused set then passed
  `3 passed in 3.8s`, exit code `0`.

#### Complete local validation

- Personal Website `npm.cmd run typecheck` passed, exit code `0`.
- Three independent fresh-process executions of
  `npm.cmd run test:e2e -- --workers=4 --retries=0` each used exactly four
  workers, ran all 34 Chromium tests (all previous 33 plus the new
  regression), did not hang and returned exit code `0`:
  - run 1: `34 passed in 15.5s`;
  - run 2: `34 passed in 15.9s`;
  - run 3: `34 passed in 13.7s`.
- Post-summary mock proxy `ECONNREFUSED` messages did not affect assertions,
  return or exit codes. Every browser invocation used its own new ignored
  session directory. All nine exact session-created directories were removed
  only after validating their absolute paths. Existing ignored, ACL-denied
  Playwright result directories were not listed, read, changed, added or
  cleaned.
- Personal Website `npm.cmd run build` and
  `npm.cmd run verify:build` both passed, exit code `0`. Build emitted only
  the existing informational non-module-script warnings.
- Docker Desktop was confirmed as Linux engine `29.6.2`. Clean ordered
  `npx.cmd supabase db reset` passed, exit code `0`, and applied all migrations
  through `20260807120000_audit_and_transform_taipei_unsafe_entry_times.sql`
  and `20260809120000_enforce_taipei_safe_entry_time_range.sql`.
- The true upgrade-over-existing-data regression passed
  `1 passed in 73.05s`, exit code `0`. `python -m mypy src tests` passed with
  no issue in 21 source files, exit code `0`.
- The repository-safe ordered Ticket 03-08 Calendar, History, Create,
  Revision, Entry Time, migration, owner-auth and real mobile Chromium set
  passed `62 passed in 103.73s`, exit code `0`.
- Complete `python -m pytest -q` passed `82 passed in 131.15s`, exit code `0`,
  with only the existing Starlette/httpx deprecation warning. These runs
  exercised real local Supabase, PostgreSQL forced RLS, PostgREST, FastAPI,
  Uvicorn and mobile Chromium.

#### Website commit, exact-SHA gates and scope audit

- Personal Website implementation commit
  `5000da4a53188e72d31add95762f6ee48f9a59cf` changes only
  `src/diary/EntryExperience.tsx` and
  `tests/e2e/continuous-history.spec.ts` and was pushed first.
- [Website checks and Pages run 31325997483](https://github.com/oscar940327/my-personal-website/actions/runs/31325997483)
  matched that exact SHA, attempt 1, and was `completed/success`. Jobs
  `build` (`93276355393`) and `deploy` (`93276478717`) matched the same SHA
  and were `completed/success`.
- [pages build and deployment run 31325997137](https://github.com/oscar940327/my-personal-website/actions/runs/31325997137)
  matched the same exact SHA, attempt 1, and was `completed/success`. Jobs
  `build` (`93276356534`), `report-build-status` (`93276403673`) and
  `deploy` (`93276403699`) matched that SHA and were `completed/success`.
  Only after both workflow gates succeeded was Diary CI pinned to the exact
  Website SHA.
- Entry Time remains metadata-only. No Diary product, migration or backend
  test changed. Immutable capture time, Original Content, Entry Revisions and
  AI obligations; Taipei grouping/counts; microsecond/UUID ordering;
  exact-once snapshots; safe migrations; owner FastAPI authorization;
  PostgreSQL RLS; PostgREST owner-token behavior; direct PATCH denial; and
  Create/edit/restore plus Ticket 03-07 behavior remain green.
- No secret, `.env` file or production environment variable was added. No
  Ticket 09, Trash/delete/permanent-delete, AI Draft, Queue, RAG or Agent work
  began. The existing Note Garden scope drift and all unrelated HOME,
  PROJECT, JOURNEY, MktAgent and VideoNote files were untouched. No broad
  `EntryExperience` refactor or non-blocking duplicated-code cleanup occurred.
- The Diary CI-pin/implementation-record commit and its exact-SHA Backend
  checks are appended as completion evidence after that remote gate finishes.
  Ticket 08 remains `ready-for-agent`. The next step is only a separate fresh,
  complete fixed-range code-review from the original bases Diary
  `898a6056068ce282e36399d568ea6350bb413f29` and Personal Website
  `231ebe21ed09ec7d777f3c78ed6eb58aab396962`; Ticket 09 remains blocked.

#### Diary exact-SHA completion evidence

- Diary CI-pin and implementation-record commit
  `f16909280ccbccc0e61c62e0321bb91d495a742e` was pushed only after both
  exact Website workflow gates succeeded.
- [Backend checks run 31326200227](https://github.com/oscar940327/diary/actions/runs/31326200227)
  matched that exact Diary SHA, attempt 1, and was `completed/success`. Its
  `test` job
  [93276860199](https://github.com/oscar940327/diary/actions/runs/31326200227/job/93276860199)
  matched the same SHA and was `completed/success`.
- The documentation-only commit that adds this completion evidence is the
  final Diary endpoint reported in the implementation handoff after its own
  exact-SHA Backend checks and all returned jobs complete successfully.

### 2026-08-10 - Fresh formal complete fixed-range code review requires changes

#### Review boundary and preflight

- Overall verdict: **CHANGES-REQUIRED**. Standards is `PASS` with no blocking
  finding. Spec is `CHANGES-REQUIRED` with two High blocking findings. Passing
  tests are supporting evidence and do not override either inspection finding.
- This was a new review from the immutable three-dot ranges:
  - Diary
    `898a6056068ce282e36399d568ea6350bb413f29...771a2f910b35d22844a21fb539ca4acdb4a2e8ac`;
  - Personal Website
    `231ebe21ed09ec7d777f3c78ed6eb58aab396962...5000da4a53188e72d31add95762f6ee48f9a59cf`.
- Before review, both repositories were on `main`, their local `HEAD` and
  `origin/main` exactly matched the required endpoints, and both tracked
  worktrees were clean. Every base and endpoint existed. Each merge-base was
  exactly the specified base. The Diary range contained 17 commits and the
  Website range contained 9 commits, so both ranges were non-empty. Complete
  three-dot `git diff --check` returned exit code `0` for each range.
- GitHub remote `main` contained both exact endpoints. Known preservation
  commit `237e0eac087aabe689ec14d8599f7d7e04221d04`, Diary pin/record commit
  `f16909280ccbccc0e61c62e0321bb91d495a742e`, and the final Diary endpoint
  were present in the reviewed Diary ancestry. Website implementation commit
  `5000da4a53188e72d31add95762f6ee48f9a59cf` was the exact Website endpoint.
- Primary review read the complete code-review skill, repository instructions,
  development workflow, domain, issue tracker, `CONTEXT.md`, full product spec,
  full Ticket 08 record and all 15 accepted ADRs (`0001` through `0015`). It
  independently inspected both complete fixed ranges and all changed product,
  test, migration and CI files. Two isolated read-only reviewers independently
  reviewed Standards and Spec; their findings were aggregated only after
  primary inspection.

#### Standards axis - PASS

Blocking findings: **0**. Non-blocking findings: **3**.

1. **Low, non-blocking - known hard workflow/scope drift remains in the fixed
   range.** Personal Website `index.html:132` adds Note Garden, contrary to the
   Diary-only boundary in `docs/agents/development-workflow.md:3,11,19-20` and
   ADR 0005. Owner-visible impact: the reviewed range contains an unrelated
   navigation/product change, so the range is not perfectly scope-isolated.
   This is the explicitly known pre-existing Note Garden drift; this review
   does not request, perform or permit its removal or cleanup.
2. **Low, non-blocking - duplicated rebuilt-window installation.** Personal
   Website `src/diary/EntryExperience.tsx:953-961` and `:1019-1025` repeat the
   Entry/cursor/state installation sequence for Save and Refresh History.
   Owner-visible impact: a later lifecycle change could update one successful
   path but not the other. Current inspected behavior and tests do not establish
   a separate present defect, so no cleanup is requested in this review.
3. **Low, non-blocking - divergent change concentration.** Personal Website
   `src/diary/EntryExperience.tsx:159-274,459-730,870-1037` owns bounded rebuild,
   request ownership, midnight refresh, Entry Time Save and recovery in one
   component. Owner-visible impact: unrelated lifecycle edits have a larger
   regression surface. This is a maintainability judgment, not permission for
   a large refactor and not a blocking defect in this fixed review.

Standards verdict: **PASS**. The known scope drift is recorded but deliberately
left untouched, and the two code-smell judgments are non-blocking.

#### Spec axis - CHANGES-REQUIRED

Blocking findings: **2**. Non-blocking findings: **1**.

1. **High, blocking - an immediately previous-version Create can permanently
   miss its initial History position during upgrade.** Diary
   `supabase/migrations/20260804120000_change_entry_time_and_stabilize_history.sql:125-134`
   backfills `entry_history_positions`, but the initial-position trigger is not
   installed until `:166-190`, and the migration does not lock out concurrent
   inserts for the interval. An old application transaction can insert an Entry
   after the backfill snapshot, commit while trigger creation waits, and never
   receive a position. The History v5 inner join at `:324-326` then hides the
   owner Entry, while a later Entry Time change reaches the missing-current
   guard at `:204-213` and fails. Owner-visible impact: a successfully captured
   Entry can disappear from continuous History during a blue-green upgrade and
   cannot be regrouped later. This violates the complete History obligation in
   `.scratch/diary/spec.md:39`, immediately-previous-version migration
   compatibility at `:169`, ADR 0013 and the Ticket's own compatibility claim
   at `08-change-entry-time-and-regroup.md:1297-1299`. The upgrade regression
   begins its old-data setup after this migration has already been installed,
   so its pass cannot cover the concurrency window.
2. **High, blocking - Taipei-midnight root takeover can install B without the
   independent reading Entry A.** The shared bounded rebuild correctly treats
   A and B as mandatory at Personal Website
   `src/diary/EntryExperience.tsx:159-266`. However, when a committed rebuild is
   superseded by the today-anchor midnight root, `:544-583` installs the fresh
   initial page and clears recovery whenever active changed Entry B is present;
   it neither requires deep reading Entry A nor restores A's pending manual
   anchor. If A is around rank 78-80 and absent from the fresh initial 60 while
   B is present, the owner loses the Entry being read and the viewport can jump,
   with no retryable `Refresh History` recovery. This bypasses the five-page
   fail-closed A/B contract and violates `.scratch/diary/spec.md:47,200` plus
   the Ticket guarantee at
   `08-change-entry-time-and-regroup.md:2061-2065`. The midnight regression at
   Personal Website `tests/e2e/continuous-history.spec.ts:1705-1991` gives the
   fresh root B and a companion but omits A, then asserts B and continuation
   only (`:1945-1990`); therefore its pass demonstrates the uncovered defect
   rather than closing it.
3. **Low, non-blocking - known Note Garden scope drift.** Personal Website
   `index.html:132` changes unrelated product navigation. Owner-visible impact
   is an impure Ticket 08 range. Per the explicit review boundary, this known
   drift is preserved and is not a requested Ticket 08 fix.

Spec verdict: **CHANGES-REQUIRED**. Both High findings affect mandatory owner
behavior. No passing local or remote gate can downgrade them.

#### Mandatory local validation evidence

- Personal Website `npm.cmd run typecheck`: exit code `0`, command duration
  `5.09s`.
- Focused deep-A, Save/recovery, font-timing and midnight Chromium regressions:
  `8 passed in 12.2s`, exactly 4 workers, no retries, command duration `26.63s`,
  exit code `0`.
- Three independent fresh-process executions of
  `npm.cmd run test:e2e -- --workers=4 --retries=0` each used exactly four
  workers, ran all 34 Chromium tests, had no hang and returned exit code `0`:
  - run 1: `34 passed in 15.6s`, command duration `25.81s`;
  - run 2: `34 passed in 14.3s`, command duration `26.48s`;
  - run 3: `34 passed in 14.0s`, command duration `24.00s`.
- Post-summary mock proxy `ECONNREFUSED` messages did not affect assertions or
  process exit. Every browser run used a newly created review-specific ignored
  output directory. Only the four exact session directories were removed after
  their absolute paths were verified. Existing ignored ACL-denied directories
  were not listed, read, modified or cleaned.
- Personal Website `npm.cmd run build`: exit code `0`, Vite `3.15s`, command
  duration `10.14s`, with only existing informational non-module-script
  warnings. `npm.cmd run verify:build`: exit code `0`, duration `0.42s`.
- Docker Desktop was confirmed as Linux engine `29.6.2`. The host had reserved
  the original local Supabase port range, so validation used a disposable
  repo-external `git archive` of the exact Diary endpoint with only local ports
  shifted from `5432x` to `5452x`; product source, migrations and repository
  tests remained the reviewed endpoint. Supabase start applied the full ordered
  migration set and returned exit code `0`. A clean ordered `supabase db reset`
  applied all 17 migrations and seed, duration `21.65s`, exit code `0`.
- The first two standalone upgrade invocations stopped in fixture setup because
  the exact test parser expected the original `54321` Magic Link while the
  disposable runtime emitted `54521`: `1 error in 36.33s`, command `38.28s`,
  exit `1`; and `1 error in 36.04s`, command `37.12s`, exit `1`. Auth returned
  the OTP successfully and local Mailpit contained the messages, proving this
  was a harness-port mismatch before the test body. A single disclosed,
  repo-external review-harness substitution changed only that literal parser
  port to `54521`; no tracked file was changed. The required true
  upgrade-over-existing-data regression then passed `1 passed in 70.04s`,
  command duration `71.12s`, exit code `0`.
- `python -m mypy src tests`: no issue in 21 source files, duration `18.81s`,
  exit code `0`.
- Repository-safe ordered Ticket 03-08 Calendar, History, Create, Revision,
  Entry Time, migration, owner-auth and mobile Chromium focused set:
  `62 passed in 105.68s`, command duration `106.84s`, exit code `0`.
- Complete `python -m pytest -q`: `82 passed, 1 warning in 123.69s`, command
  duration `124.71s`, exit code `0`; the warning was the existing
  Starlette/httpx deprecation notice.
- These Diary runs exercised real local Supabase, PostgreSQL forced RLS,
  PostgREST, FastAPI, Uvicorn and mobile Chromium. The final passing evidence
  confirms metadata-only Entry Time, revisions/Original Content/AI obligations,
  Taipei grouping, microsecond/UUID ordering, current migration data behavior,
  owner authorization/RLS and Ticket 03-07 seams, but it does not simulate the
  blocking migration concurrency window or the missing midnight deep-A case.
- The local stack was stopped without backup. The exact temporary runtime and
  four exact review-created browser output directories were removed only after
  absolute-path and junction-target verification. Original repository
  `node_modules` remained present. Both tracked worktrees were clean again
  before this record was appended.

#### Reviewed endpoint Actions and audit

- Diary exact endpoint
  `771a2f910b35d22844a21fb539ca4acdb4a2e8ac`:
  [Backend checks run 31326459725](https://github.com/oscar940327/diary/actions/runs/31326459725)
  was `completed/success`; its
  [test job 93277517152](https://github.com/oscar940327/diary/actions/runs/31326459725/job/93277517152)
  was `completed/success` at the same head SHA.
- Personal Website exact endpoint
  `5000da4a53188e72d31add95762f6ee48f9a59cf`:
  [pages build and deployment run 31325997137](https://github.com/oscar940327/my-personal-website/actions/runs/31325997137)
  was `completed/success`; jobs
  [build 93276356534](https://github.com/oscar940327/my-personal-website/actions/runs/31325997137/job/93276356534),
  [report-build-status 93276403673](https://github.com/oscar940327/my-personal-website/actions/runs/31325997137/job/93276403673)
  and
  [deploy 93276403699](https://github.com/oscar940327/my-personal-website/actions/runs/31325997137/job/93276403699)
  were all `completed/success` at the same head SHA.
- At the same Website SHA,
  [Website checks and Pages run 31325997483](https://github.com/oscar940327/my-personal-website/actions/runs/31325997483)
  and jobs
  [build 93276355393](https://github.com/oscar940327/my-personal-website/actions/runs/31325997483/job/93276355393)
  and
  [deploy 93276478717](https://github.com/oscar940327/my-personal-website/actions/runs/31325997483/job/93276478717)
  were all `completed/success`.
- Fixed-range filename audit found zero `.env` changes and zero Ticket 09
  files. A high-confidence added-line credential scan found zero matches in
  either range. Local Supabase synthetic credentials remained runtime-only and
  were not written to the repositories or this record. No production secret or
  environment value was introduced.
- No Ticket 09, Trash/deletion, AI, Queue, RAG or Agent implementation began.
  The known Note Garden change at Website `index.html:132` was neither modified
  nor removed. No unrelated-site cleanup, code fix, migration/test/CI change or
  large refactor was performed. No PR was created.
- Ticket 08 remains `ready-for-agent`. This review records
  **CHANGES-REQUIRED** only; it does not begin implementation or Ticket 09.
  The separate documentation-only commit containing this appended record and
  its exact-SHA Backend check are reported in the review handoff after that
  remote gate completes.

### 2026-08-13 - Formal blocker-fix implementation

#### Boundary, preflight and starting evidence

- This was a new implementation session limited to the two High findings in
  the 2026-08-10 formal fixed-range review. It used the complete `implement`,
  `tdd` and `diagnosing-bugs` instructions and did not invoke or begin a formal
  code review. The review's non-blocking duplicated-code, divergent-change and
  Note Garden findings were deliberately left unchanged.
- Diary began on `main` with local `HEAD`, `origin/main` and GitHub remote
  `main` all exactly
  `3a0a0337b053313ab29bd6030069431deeca1d2e`; its tracked worktree was clean.
  Personal Website began on `main` with all three refs exactly
  `5000da4a53188e72d31add95762f6ee48f9a59cf`; its tracked worktree was clean.
- Both starting SHAs were contained by remote `main`. Diary
  [Backend checks run 31405805510](https://github.com/oscar940327/diary/actions/runs/31405805510)
  and its
  [test job 93511724182](https://github.com/oscar940327/diary/actions/runs/31405805510/job/93511724182)
  were `completed/success` at the exact starting Diary SHA. Website starting
  runs
  [31325997137](https://github.com/oscar940327/my-personal-website/actions/runs/31325997137)
  and
  [31325997483](https://github.com/oscar940327/my-personal-website/actions/runs/31325997483),
  including every returned build/report/deploy job, were
  `completed/success` at the exact starting Website SHA.
- The complete repository instructions, development workflow, domain, issue
  tracker, `CONTEXT.md`, product spec, full Ticket 08 record, all 15 ADRs and
  complete product/migration/test/CI context for both findings were read before
  implementation.

#### Blocker 2 root cause, Red and implementation

- Root cause: the Taipei-midnight today-anchor path in
  `EntryExperience.tsx` directly installed a fresh cursorless root containing
  changed Entry B and cleared committed recovery. It bypassed the shared
  bounded `rebuildHistoryWindow`, did not require deep reading Entry A, and did
  not restore A's manual anchor. B could therefore survive while A disappeared
  and retryable recovery was retired.
- The two existing midnight root success and failure/retry journeys were
  expanded into combined deep-A regressions. A is the actual first-visible
  reading Entry around rank 78, absent from the fresh initial 60; B is a
  distinct changed Entry already in the fresh root. The fixture requires fresh
  newer traversal for B and older traversal for A, enforces fresh snapshot
  cursors, the fixed root-plus-four-request budget, exact-once A/B rendering,
  and retains the original `toBeCloseTo(..., 0)` viewport tolerance.
- Two preliminary test-coordination attempts timed out waiting for an animation
  frame while the test clock was paused (`2 failed`, wall `48.2s`, exit `1`;
  then `2 failed`, wall `36.59s`, exit `1`). They never reached the reviewed
  product assertion and are not counted as product Red evidence.
- Valid reviewed-endpoint Red command:
  `npm.cmd run test:e2e -- --workers=4 --retries=0 --grep "midnight root .* preserves a committed Entry Time rebuild" --output=test-results/ticket08-blocker-fix-red3-midnight-deep-a`.
  It ran two Chromium tests with two workers and zero retries; both failed on
  the intended assertion, expected A count `1` but received `0`. Playwright
  reported `6.5s`, command wall time was `19.16s`, exit code `1`, with no hang.
- Fix: `HistoryWindow` now carries its root `anchorDate`, and the midnight
  `refreshHistory` path captures committed recovery and calls the same
  `rebuildHistoryWindow` used by Save and `Refresh History`. It installs and
  clears recovery only after the shared final guard has found both independent
  mandatory concepts A and B. Any missing Entry fails closed and preserves the
  same retryable recovery. Ordinary cursorless refresh behavior is unchanged.
- The shared runner still has exactly one fresh cursorless root plus at most
  four cursored requests, caps ordinary reconstruction at 60 Entries, never
  derives budget from lifetime or loaded count, never reuses an old snapshot
  cursor, and preserves manual anchor ownership plus
  `document.fonts.ready` timing. Manual newer/older pagination,
  IntersectionObserver, stale-finally/loading ownership and Calendar recovery
  retirement remained green.
- Focused Green for the exact two tests: `2 passed in 3.2s`, two workers, wall
  `12.72s`, exit `0`. The broader deep-A/Save/recovery/font/midnight/root/stale
  set ran ten Chromium tests with exactly four workers: `10 passed in 7.0s`,
  wall `16.19s`, exit `0`.

#### Blocker 1 diagnosis, regression and defensive implementation

- The deterministic regression resets to immediately previous schema
  `20260803120000`, installs a test-only PostgreSQL DDL event trigger, and uses
  advisory locks to pause the real `supabase migration up --local` at the
  post-backfill `CREATE INDEX`, before initial-position trigger installation.
  It then starts a previous-version `create_diary_entry` transaction and
  observes actual granted/waiting PostgreSQL relation locks. No sleep or
  probabilistic race selects the interleaving.
- The first environment attempt stopped in fixture setup because the sandboxed
  Supabase CLI could not open its Windows temporary path (`EPERM`; `1 error in
  3.07s`, wall `5.13s`, exit `1`). Starting the unchanged local stack outside
  that filesystem sandbox succeeded on the repository's original ports; no
  disposable runtime, port rewrite or tracked harness adaptation was needed.
  A first helper revision then misread psql's tabular `count = 1` output and
  timed out (`1 failed in 83.89s`, wall `84.95s`, exit `1`). Neither setup
  failure is represented as a product Red.
- Crucially, two corrected executions against the unmodified reviewed
  migration were Green: the initial lock-coordinated version passed
  `1 passed in 70.87s` (wall `71.91s`, exit `0`), and the stricter event-trigger
  post-backfill/pre-trigger version passed `1 passed in 87.07s` (wall `88.58s`,
  exit `0`). The latter observed that previous-version Create waited rather
  than entering the alleged gap.
- Diagnosis: `CREATE TABLE entry_history_positions` adds a foreign key to
  `entries`, which takes a `SHARE ROW EXCLUSIVE` lock that conflicts with
  Create's `ROW EXCLUSIVE` lock. The Supabase runner retains that lock through
  the migration. Therefore the reviewed endpoint already admitted only the two
  safe states: a Create committed before the lock is included by backfill, or
  a Create waiting behind the migration is captured by the installed trigger.
  The review's third state could not be reproduced. With owner approval, this
  finding is recorded as a review false positive; no failing product Red was
  fabricated.
- A first defensive naked `LOCK TABLE` attempt correctly failed before any
  test body because PostgreSQL requires an explicit transaction block
  (`LOCK TABLE can only be used in transaction blocks`; pytest setup
  `1 error in 27.13s`, wall `28.69s`, exit `1`). The final migration explicitly
  wraps its complete contents in `BEGIN`/`COMMIT` and takes
  `SHARE ROW EXCLUSIVE` on `entries` immediately before backfill. This makes the
  Create-exclusion contract independent of the foreign key's implicit lock and
  visibly holds it through backfill, indexes, RLS and trigger installation.
- A clean ordered reset with the final SQL applied all 17 migrations and seed
  in wall `23.41s`, exit `0`. The same deterministic concurrency regression
  then passed `1 passed in 73.70s` (wall `75.35s`, exit `0`): History contained
  the concurrent Entry exactly once, it had exactly one current position with
  the microsecond timestamp, and subsequent Change Entry Time succeeded. The
  existing true upgrade-over-existing-data regression passed
  `1 passed in 71.99s` (wall `73.13s`, exit `0`).
- The transaction and explicit lock do not modify data semantics, RPC grants,
  forced RLS or owner boundaries. Backfill remains one insert from existing
  Entries, and the trigger still handles later Creates; no history position is
  lost, duplicated or reordered. Entry Time remains metadata-only and no
  revision or AI obligation is created, deleted or rescheduled.

#### Website validation, commit and exact-SHA gate

- `npm.cmd run typecheck`: wall `2.46s`, exit `0`.
- Three independent fresh-process commands
  `npm.cmd run test:e2e -- --workers=4 --retries=0` each ran all 34 Chromium
  tests with exactly four workers, zero retries, no hang and exit `0`:
  - run 1: Playwright `34 passed in 12.9s`, wall `23.59s`;
  - run 2: Playwright `34 passed in 12.9s`, wall `21.86s`;
  - run 3: Playwright `34 passed in 13.0s`, wall `23.27s`.
- Each run emitted only the known post-summary Vite mock-proxy
  `ECONNREFUSED 127.0.0.1:8000` message after assertions; there was no retry,
  hang or post-summary process error and every command exited `0`.
- `npm.cmd run build`: Vite `2.58s`, wall `8.05s`, exit `0`, with only existing
  non-module-script warnings. `npm.cmd run verify:build`: wall `0.40s`, exit
  `0`.
- Seventeen implementation-specific ignored Playwright output directories were
  created across Red/debug/Green runs. Each exact absolute path was validated
  and only those directories were removed. Existing ignored ACL-denied
  directories were not read, listed, changed or cleaned.
- Personal Website commit
  `6fb5c4e5dd8283fd9438cd3eb6ca497da1f37beb` changed only
  `src/diary/EntryExperience.tsx` and
  `tests/e2e/continuous-history.spec.ts`, was pushed to `main`, and became the
  Diary CI exact pin only after all Website gates succeeded.
- [Website checks and Pages run 31628745480](https://github.com/oscar940327/my-personal-website/actions/runs/31628745480)
  was `completed/success` at that exact SHA. Jobs
  [build 94221809049](https://github.com/oscar940327/my-personal-website/actions/runs/31628745480/job/94221809049)
  and
  [deploy 94222143519](https://github.com/oscar940327/my-personal-website/actions/runs/31628745480/job/94222143519)
  were both `completed/success`.
- [pages build and deployment run 31628744450](https://github.com/oscar940327/my-personal-website/actions/runs/31628744450)
  was also `completed/success` at the same exact SHA. Jobs
  [build 94221810698](https://github.com/oscar940327/my-personal-website/actions/runs/31628744450/job/94221810698),
  [report-build-status 94221935941](https://github.com/oscar940327/my-personal-website/actions/runs/31628744450/job/94221935941)
  and
  [deploy 94221936079](https://github.com/oscar940327/my-personal-website/actions/runs/31628744450/job/94221936079)
  were all `completed/success`.

#### Diary complete validation and scope audit

- Docker Desktop Linux engine was confirmed as `linux 29.6.2`. The final clean
  ordered Supabase reset, focused concurrency regression and existing true
  upgrade regression are recorded above, all on the original local ports.
- `python -m mypy src tests`: no issues in 21 source files, wall `1.81s`, exit
  `0`.
- Repository-safe ordered Ticket 03-08 Calendar, History, Create, Revision,
  Entry Time, migration, owner-auth and mobile Chromium/real-API set:
  `64 passed in 152.79s`, wall `153.82s`, exit `0`.
- Complete `python -m pytest -q`: `83 passed, 1 warning in 166.59s`, wall
  `167.51s`, exit `0`. The warning is the existing Starlette/httpx deprecation
  notice. These runs exercised real Supabase, PostgreSQL forced RLS, PostgREST,
  FastAPI, Uvicorn and mobile Chromium.
- Diary implementation changes are limited to
  `supabase/migrations/20260804120000_change_entry_time_and_stabilize_history.sql`,
  `tests/system/test_migration_upgrade.py`, the exact Website pin in
  `.github/workflows/ci.yml`, and this appended Ticket 08 record. Website
  changes are limited to the two files named above. `git diff --check` passed.
- Added-line audit found no secret, token, credential, Magic Link, production
  environment value or `.env` file. Local Supabase synthetic credentials were
  runtime-only and are not stored here. No Ticket 09, Trash/delete, AI Draft,
  Queue, RAG or Agent work began. Existing Note Garden scope drift was neither
  changed nor cleaned. No unrelated-site cleanup, non-blocking duplicated-code
  fix, `EntryExperience` split or large refactor occurred. No PR was created.
- The scoped Diary implementation/CI-pin commit and its exact-SHA Backend run
  and job links will be appended in a separate documentation-only completion
  commit after the remote gate succeeds. Ticket 08 remains `ready-for-agent`.
  The only next step is a separate fresh formal fixed-range code-review session;
  Ticket 09 remains blocked.

#### Diary exact-SHA blocker-fix completion evidence

- Diary blocker-fix implementation, concurrency regression, Website pin and
  implementation-record commit
  `fd41fc547645a483b7f6ff018e7c9d88821b6b4b` was pushed to `main` with only
  the four scoped files audited above.
- [Backend checks run 31632679469](https://github.com/oscar940327/diary/actions/runs/31632679469)
  matched that exact head SHA, attempt 1, and was `completed/success`.
  Its only returned job,
  [test 94235149515](https://github.com/oscar940327/diary/actions/runs/31632679469/job/94235149515),
  matched the same head SHA and was `completed/success`.
- This documentation-only completion commit is the final Diary endpoint. Its
  own exact-SHA Backend run and every returned job are required to reach
  `completed/success` before implementation handoff. Ticket 08 remains
  `ready-for-agent`; the next step remains only a new formal fixed-range code
  review, not Ticket 09.

## 2026-08-13 formal fixed-range code review — post-blocker-fix endpoint

### Session contract and verdict

- This was a fresh review-only session under the repository `code-review`
  skill. Two independent agents reviewed the complete integrated ranges in
  parallel: Standards and Spec. Neither agent was limited to the endpoint
  commit or to the blocker-fix subranges. Source inspection was performed in
  addition to local and exact-SHA CI validation.
- **Overall: CHANGES-REQUIRED.** Standards is **CHANGES-REQUIRED** and Spec is
  **CHANGES-REQUIRED**. Passing tests do not offset either source finding.
- The 2026-08-10 migration/Create High finding is **closed as originally
  stated**: it was a false positive. The foreign-key DDL lock and actual runner
  transaction already exclude the alleged backfill/trigger gap, and the new
  regression demonstrates the two permitted Create outcomes. A separate new
  migration-bookkeeping atomicity defect is recorded below.
- The 2026-08-10 Website midnight High finding is **still open**. The pending
  Save-rebuild takeover path is repaired, but a committed rebuild that has
  already failed can lose mandatory reading Entry A at the next Taipei
  midnight.
- No finding was fixed. No product, migration, test or CI code was modified.
  No PR was created and Ticket 09 was not started.

### Required preflight

- Before review edits, Diary was `main` with local `HEAD`, `origin/main` and
  GitHub remote `main` all exactly
  `c17a9665f43b9e2df124afaee52e3a533b9392f3`; its tracked worktree was clean.
- Personal Website was `main` with local `HEAD`, `origin/main` and GitHub
  remote `main` all exactly
  `6fb5c4e5dd8283fd9438cd3eb6ca497da1f37beb`; its tracked worktree was clean.
- [Website checks and Pages run 31628745480](https://github.com/oscar940327/my-personal-website/actions/runs/31628745480)
  at Website SHA `6fb5c4e5dd8283fd9438cd3eb6ca497da1f37beb`
  was `completed/success`. Jobs
  [build 94221809049](https://github.com/oscar940327/my-personal-website/actions/runs/31628745480/job/94221809049)
  and
  [deploy 94222143519](https://github.com/oscar940327/my-personal-website/actions/runs/31628745480/job/94222143519)
  were both `completed/success` at the same head SHA.
- [Pages build and deployment run 31628744450](https://github.com/oscar940327/my-personal-website/actions/runs/31628744450)
  at the same Website SHA was `completed/success`. Jobs
  [build 94221810698](https://github.com/oscar940327/my-personal-website/actions/runs/31628744450/job/94221810698),
  [report-build-status 94221935941](https://github.com/oscar940327/my-personal-website/actions/runs/31628744450/job/94221935941)
  and
  [deploy 94221936079](https://github.com/oscar940327/my-personal-website/actions/runs/31628744450/job/94221936079)
  were all `completed/success` at that SHA.
- [Diary Backend checks run 31632679469](https://github.com/oscar940327/diary/actions/runs/31632679469)
  at implementation SHA `fd41fc547645a483b7f6ff018e7c9d88821b6b4b`
  and its only returned job
  [test 94235149515](https://github.com/oscar940327/diary/actions/runs/31632679469/job/94235149515)
  were `completed/success` at that exact SHA.
- [Diary Backend checks run 31633246301](https://github.com/oscar940327/diary/actions/runs/31633246301)
  at final reviewed endpoint
  `c17a9665f43b9e2df124afaee52e3a533b9392f3` and its only returned job
  [test 94237067131](https://github.com/oscar940327/diary/actions/runs/31633246301/job/94237067131)
  were `completed/success` at that exact SHA.

### Fixed ranges and commit inventories

- Diary integrated range
  `898a6056068ce282e36399d568ea6350bb413f29...c17a9665f43b9e2df124afaee52e3a533b9392f3`:
  both objects exist; merge-base is exactly the specified base; three-dot diff
  is non-empty; `git diff --check` passed; **20 commits**:
  - `5f7362f2ccaf0174dd9e74cf346d4bd20a5a08f4` — `feat: change entry time and regroup history`
  - `8e7eb600d250919380a52a63a0e977fee7d93101` — `docs: record Ticket 08 fixed-range review`
  - `189bd18e9f498124f5282fdb37b296b82ef98c82` — `fix: resolve Ticket 08 review blockers`
  - `994670926ee45a3db781d0280845357fec3838b5` — `docs: record Ticket 08 follow-up review`
  - `432ed2f353d86359b1810d19772a5bda6870a748` — `fix: close Ticket 08 review blockers`
  - `662c0b10110daa9c8b7205dd07a3beb0454a428d` — `docs: record Ticket 08 fresh fixed-range review`
  - `a9ca31125c18177c246799e413e9032542258ca8` — `fix: close latest Ticket 08 history blockers`
  - `0ebb90d08af18b5afbd26520baade43204b54ddb` — `docs: record latest Ticket 08 review blockers`
  - `b8d719fddb73d7088a918453b12e4242ce7fbb7e` — `fix: enforce Ticket 08 blocker invariants`
  - `2db44e7526ab216f4301a1ce9cffcbe10e98935a` — `docs: record Ticket 08 fixed-range review blockers`
  - `b4d0e434e05ffbbf016b6905fb75fac9520737de` — `Fix Ticket 08 migration upgrade safety`
  - `003fbcd942b128ad87776b296cd04fca644d4c77` — `docs: record Ticket 08 formal review failure`
  - `aa07c8f0eba44693dd552a6d4bac09927745e3b3` — `Record Ticket 08 recovery anchor fix`
  - `118985d5a891b8807be97509ca179557bc78a173` — `Record Ticket 08 exact-SHA checks`
  - `237e0eac087aabe689ec14d8599f7d7e04221d04` — `docs: preserve Ticket 08 review findings`
  - `f16909280ccbccc0e61c62e0321bb91d495a742e` — `fix: pin deep History anchor implementation`
  - `771a2f910b35d22844a21fb539ca4acdb4a2e8ac` — `docs: record Ticket 08 implementation checks`
  - `3a0a0337b053313ab29bd6030069431deeca1d2e` — `docs: record Ticket 08 fixed-range review`
  - `fd41fc547645a483b7f6ff018e7c9d88821b6b4b` — `Fix Ticket 08 review blockers`
  - `c17a9665f43b9e2df124afaee52e3a533b9392f3` — `Record Ticket 08 blocker-fix checks`
- Diary blocker-fix range
  `3a0a0337b053313ab29bd6030069431deeca1d2e...c17a9665f43b9e2df124afaee52e3a533b9392f3`:
  both objects exist; merge-base is exactly the specified base; three-dot diff
  is non-empty; `git diff --check` passed; **2 commits**:
  `fd41fc547645a483b7f6ff018e7c9d88821b6b4b` and
  `c17a9665f43b9e2df124afaee52e3a533b9392f3` as listed above.
- Personal Website integrated range
  `231ebe21ed09ec7d777f3c78ed6eb58aab396962...6fb5c4e5dd8283fd9438cd3eb6ca497da1f37beb`:
  both objects exist; merge-base is exactly the specified base; three-dot diff
  is non-empty; `git diff --check` passed; **10 commits**:
  - `3d1e27ea3d78eb20d44b1ef0a63defd64f0dd1b5` — `feat(diary): change entry time and regroup history`
  - `7898db9691d41f3f418a27250387164531359aac` — `fix: preserve History window after Entry Time changes`
  - `7a480780aaf8090f0f610be0a04f25a02abb00e3` — `fix(diary): harden Entry Time history recovery`
  - `18dc585ee8fdcd022778b525520d36be998d08fd` — `feat: add note garden link`
  - `774787b16b0da864100080ecd5d11a59932be6cf` — `fix(diary): isolate Ticket 08 history ownership`
  - `ee25f7e0b03a21aaa78b587f2aa19c69b9cdd767` — `fix: close Ticket 08 history blockers`
  - `6a04e418fc0c3e14fdb14cfa590f39825e83c0d4` — `Fix Ticket 08 history rebuild ownership`
  - `4f47c1d4c36a78f9c49df8885515e3143d34cbb2` — `Fix Ticket 08 recovery anchor lifecycle`
  - `5000da4a53188e72d31add95762f6ee48f9a59cf` — `fix: preserve deep History reading anchor`
  - `6fb5c4e5dd8283fd9438cd3eb6ca497da1f37beb` — `Fix midnight deep history recovery`
- Personal Website blocker-fix range
  `5000da4a53188e72d31add95762f6ee48f9a59cf...6fb5c4e5dd8283fd9438cd3eb6ca497da1f37beb`:
  both objects exist; merge-base is exactly the specified base; three-dot diff
  is non-empty; `git diff --check` passed; **1 commit**,
  `6fb5c4e5dd8283fd9438cd3eb6ca497da1f37beb`.
- The complete three-dot diff and every added line in all four ranges were
  inspected. The blocker subranges received additional inspection; they did
  not replace the integrated-range review.

### Standards review — CHANGES-REQUIRED

1. **High — blocking — committed failure followed by midnight is not A/B
   fail-closed.** Personal Website
   `src/diary/EntryExperience.tsx:546-605,985-1001` retains React
   `historyRecovery` after the mutation commits and its first rebuild fails,
   but clears `committedHistoryRecovery.current` at line 996. If Taipei
   midnight fires before the owner presses Refresh History, lines 547-579 take
   the ordinary-root branch; lines 598-605 then retire recovery when B alone is
   present. A deep reading A outside the fresh root can disappear together
   with the retry path. The owner-visible result is loss of the reading Entry,
   visual anchor and recoverability after an otherwise successful Entry Time
   change. `tests/e2e/continuous-history.spec.ts:1065-1456` covers immediate
   manual retry, while `:1706-2153` covers midnight takeover only while the Save
   rebuild is still pending; neither triggers failed Save rebuild followed by
   midnight. This violates `.scratch/diary/spec.md:47,200`, the Ticket's
   mandatory independent A/B fail-closed contract, and reliable async
   ownership/state-transition standards.
2. **Low — non-blocking — existing hard scope drift, preserved.** Personal
   Website `index.html:132` adds Note Garden within the integrated Ticket 08
   range. The owner-visible impact is an unrelated homepage navigation change.
   It violates `docs/agents/development-workflow.md:3,11,19-20` single-Ticket
   scope and ADR 0005 existing-site preservation. It was already known and was
   deliberately neither modified nor cleaned.
3. **Low — non-blocking — existing Duplicated Code judgment, preserved.**
   Personal Website `src/diary/EntryExperience.tsx:976-982,1042-1048`
   duplicates rebuilt-window installation. There is no immediate behavioral
   owner impact; the maintenance impact is that future fixes can diverge
   between paths. This is Fowler Duplicated Code. No cleanup was authorized.
4. **Low — non-blocking — existing Divergent Change judgment, preserved.**
   Personal Website `src/diary/EntryExperience.tsx:160-275,461-752,893-1058`
   owns pagination, request ownership, midnight, mutation recovery and visual
   anchoring. There is no new owner-visible failure beyond finding 1; the
   maintenance impact is broad change coupling. This is Fowler Divergent
   Change. No split or refactor was authorized.
5. **Low — non-blocking — new Duplicated Code judgment.** Diary
   `tests/system/test_migration_upgrade.py:50-92` duplicates the full
   Docker/psql argv construction between `_psql` and `_open_psql`. There is no
   current product impact; future harness changes must remain synchronized.
   This is Fowler Duplicated Code and is not a blocker.

### Spec review — CHANGES-REQUIRED

1. **High — blocking — migration DDL and migration bookkeeping are not
   atomic.** Diary
   `supabase/migrations/20260804120000_change_entry_time_and_stabilize_history.sql:1,556`
   adds explicit `BEGIN`/`COMMIT`. Pinned Supabase CLI v2.109.1
   [`MigrationFile.ExecBatch`](https://github.com/supabase/cli/blob/v2.109.1/apps/cli-go/pkg/migration/file.go#L75-L90)
   queues every parsed migration statement and then the
   `schema_migrations` insert. Its pinned pgconn v1.14.3 documents that
   [`ExecBatch` is implicitly transactional only when SQL contains no
   transaction control](https://github.com/jackc/pgconn/blob/v1.14.3/pgconn.go#L1764-L1765).
   Migration line 556 therefore commits product DDL before the subsequently
   queued history insert. Process loss or bookkeeping-insert failure in that
   interval leaves the schema applied but unrecorded; the next push/retry can
   reapply non-idempotent DDL and require manual migration repair. Clean resets
   and the successful concurrency/upgrade paths do not inject this failure.
   This violates `.scratch/diary/spec.md:363` and
   `docs/adr/0013-use-expand-contract-database-migrations.md:19`, which require
   transactional execution and release stop on migration failure.
2. **High — blocking — failed Save recovery can still lose independent reading
   Entry A at midnight.** Personal Website
   `src/diary/EntryExperience.tsx:546-605,985-1001` has the exact trigger,
   evidence, owner-visible loss and uncovered-test gap stated in Standards
   finding 1. It violates `.scratch/diary/spec.md:47,200` and the Ticket record
   at the 2026-08-13 blocker contract: both A and B must be present before a
   rebuilt window installs and recovery clears; otherwise refresh must fail
   closed and remain retryable.
3. **Low — non-blocking — retained known scope creep.** Personal Website
   `index.html:132` changes the existing site shell with Note Garden. The
   owner-visible impact and basis are the same as Standards finding 2, plus
   `.scratch/diary/spec.md:15`. It remains unchanged as required.

### Blocker 1 independent disposition

- **2026-08-10 Blocker 1: CLOSED as originally stated; false positive.**
  `CREATE TABLE public.entry_history_positions` at migration lines 110-119
  creates the foreign key to `entries`. PostgreSQL takes the referenced-side
  `SHARE ROW EXCLUSIVE` lock for this DDL; that mode conflicts with Create's
  `ROW EXCLUSIVE`, and locks are held to transaction end. Without the new
  transaction-control statements, the actual CLI queues DDL and migration
  history in one implicitly transactional batch. Thus a previous-version
  Create can only commit before the lock and be included by backfill, or wait
  until migration completion and be captured by the initial-position trigger.
- Migration lines 127-140 additionally state the exclusion with an explicit
  `SHARE ROW EXCLUSIVE` immediately before backfill. The deterministic
  regression at `tests/system/test_migration_upgrade.py:272-545` installs an
  event trigger and advisory locks, pauses on the post-backfill/pre-trigger
  `CREATE INDEX`, and observes either pre-lock completion or a waiting Create.
  It uses no sleep-based race. It then proves History contains the Entry
  exactly once (`:497`), exactly one current position exists with the full
  microsecond timestamp (`:512-515`), and subsequent Change Entry Time works
  (`:517-535`). It does not create its fixture after migration completion.
- Source and regression inspection found no successful Create-without-position
  route and no duplicated, lost or misplaced existing position. History v5,
  Create RPC, Change Entry Time RPC, forced RLS, grants, PostgREST and FastAPI
  owner boundaries remain semantically unchanged. The new Spec finding is not
  the old race: it is rollback/bookkeeping safety introduced by the attempted
  defensive wrapper.

### Blocker 2 independent disposition

- **2026-08-10 Blocker 2: OPEN.** The new midnight path does use the shared
  `rebuildHistoryWindow` while `committedHistoryRecovery.current` exists, and
  the pending-rebuild success/failure tests verify deep A around rank 78 plus
  changed B, one fresh root plus at most four same-snapshot cursor requests,
  no old cursor, exactly-once A/B, unchanged viewport tolerance, manual anchor
  ownership, `document.fonts.ready`, and retryable failure.
- The missing interleaving begins after that Save rebuild has already failed:
  line 996 removes the only signal used by midnight. Ordinary midnight root
  then applies its B-only recovery-clear rule. Save and manual Refresh still
  share the rebuild implementation when the recovery ref survives, but they do
  not share it in this lifecycle. This is a new concrete trigger for the same
  mandatory A/B contract, so the blocker is not fully closed.

### Local validation

#### Personal Website

- `npm.cmd run typecheck`: wall `1.0s`, exit `0`.
- Focused combined deep-A/save/recovery/font/midnight Chromium command:
  `npm.cmd run test:e2e -- --workers=4 --retries=0 --grep 'committed Entry Time change|Entry Time (save|recovery) rebuild|deep reading Entry|delayed (older|newer) load retires at midnight root|midnight root (success|failure) preserves|delayed root refresh cannot overwrite' --output=test-results/ticket08-formal-review-20260813-focused`:
  exactly 4 workers, `11 passed in 10.5s`, wall `22.5s`, exit `0`, no retry,
  hang or post-summary process error.
- Three independent fresh-process full commands used
  `npm.cmd run test:e2e -- --workers=4 --retries=0` and separate
  review-specific ignored output directories:
  - run 1: exactly 4 workers, `34 passed in 14.4s`, wall `24.5s`, exit `0`;
  - run 2: exactly 4 workers, `34 passed in 13.7s`, wall `19.9s`, exit `0`;
  - run 3: exactly 4 workers, `34 passed in 13.5s`, wall `19.7s`, exit `0`.
- All three full runs had zero retries and no hang. Each emitted only the known
  post-summary Vite mock-proxy `ECONNREFUSED 127.0.0.1:8000` diagnostic after
  assertions; no process error followed the summary and every command returned
  exit `0`.
- `npm.cmd run build`: Vite `3.14s`, wall `8.2s`, exit `0`, with only existing
  non-module-script warnings. `npm.cmd run verify:build`: wall `0.6s`, exit
  `0`.
- Only the four exact directories created by this review were touched. Their
  absolute paths were validated under
  `E:\personal_website\test-results` and then removed. Existing ignored
  ACL-denied directories were not read, listed or cleaned.

#### Diary

- Docker Desktop was independently confirmed as Linux engine `linux 29.6.2`;
  the pinned local CLI was v2.109.1. The original ports were available, so no
  disposable runtime, URL adaptation or credential substitution was used.
- An initial `npx.cmd supabase db reset --local` correctly reported that the
  stack was not running. After start, the clean ordered reset completed in wall
  `33.6s`, exit `0`, applying all 17 migrations and seed. A later manually
  started full service profile caused Kong-to-Auth `502`/read-timeout
  precondition failures after internal resets: the first concurrency attempt
  failed before the race at Auth restore (`1 failed in 99.51s`); the second ran
  the race but failed HTTP/teardown readiness (`1 failed in 111.84s`). These
  are preserved as environment failures, not product Reds. The full-profile
  stack was stopped, and the repository's existing fixture started its exact
  excluded-service profile on the same original ports; no code changed.
- Deterministic previous-version concurrent Create regression:
  `python -m pytest -q --tb=short tests/system/test_migration_upgrade.py::test_previous_version_create_committing_during_history_upgrade_gets_initial_position`:
  `1 passed in 105.42s`, wall `106.6s`, exit `0`.
- Existing true upgrade-over-data regression:
  `python -m pytest -q --tb=short tests/system/test_migration_upgrade.py::test_ordered_upgrade_transforms_unsafe_entry_times_with_immutable_audit`:
  `1 passed in 102.99s`, wall `104.1s`, exit `0`.
- `python -m mypy src tests`: no issues in 21 source files, wall `2.1s`, exit
  `0`.
- Repository-safe ordered Ticket 03-08 command over
  `test_calendar_navigation.py`, `test_continuous_history.py`,
  `test_entry_capture.py`, `test_entry_revisions.py`, `test_entry_time.py`,
  `test_migration_upgrade.py`, `test_owner_authentication.py`,
  `test_owner_browser_authentication.py` and `tests/test_health.py`:
  `64 passed, 1 warning in 182.55s`, wall `183.9s`, exit `0`.
- `python -m pytest -q --tb=short`: `83 passed, 1 warning in 200.90s`, wall
  `202.1s`, exit `0`. The warning was the existing Starlette/httpx deprecation.
  These runs exercised real Supabase, PostgreSQL forced RLS, PostgREST,
  FastAPI, Uvicorn and mobile Chromium seams. The repository fixture stopped
  every session-started Supabase container at completion.

### Ticket 03-08 invariant and scope audit

- Source plus validation preserved Entry Time as Entry metadata only:
  `captured_at`, Original Content and immutable Revision history do not change;
  no AI obligation is produced, deleted or rescheduled. Asia/Taipei grouping,
  Calendar counts, microsecond timestamps and descending UUID tie-breaks
  remain correct. Existing History snapshots neither duplicate nor omit moved
  Entries.
- Create/edit/restore contracts remain backward-compatible. FastAPI owner
  boundaries, PostgreSQL forced RLS, PostgREST owner-token use and direct PATCH
  denial remain enforced. The explicit transaction did not widen RPC grants or
  RLS; its defect is the separate bookkeeping commit boundary described above.
- Apart from the blocking failed-rebuild-then-midnight lifecycle, manual
  pagination, IntersectionObserver loading, stale `finally` ownership, loading
  ownership, font timing, Calendar retirement and fresh-process exit showed no
  regression. Ordinary mutation rebuild remains bounded independently of
  lifetime/previously loaded count, uses one root plus at most four cursors from
  one snapshot, and retains the 60-entry ordinary target.
- Complete added-line audit found no secret, token, credential, Magic Link,
  production environment value or `.env` file. Local Supabase synthetic values
  remained runtime-only and are not reproduced in this record.
- No Ticket 09, Trash/delete, AI Draft, Queue, RAG or Agent work began. Existing
  Note Garden drift remains exactly as reviewed. No duplicated-code or
  divergent-change finding was fixed; `EntryExperience` was not split. No
  unrelated-site cleanup or large refactor occurred.
- After validation, both tracked worktrees were still clean at their reviewed
  endpoints. This append is the only review-session file change. The required
  next action is the docs-only review-record commit and its exact-SHA Backend
  gate; no implementation or Ticket 09 work is authorized by this record.

### 2026-08-13 - Formal-review blocking findings implementation

#### Boundary and preflight

- This implementation session was limited to the two High blockers from the
  2026-08-13 formal fixed-range review: migration/bookkeeping atomicity and a
  failed committed Save rebuild followed by Taipei midnight. The closed
  2026-08-10 foreign-key/Create race finding remains closed as a false
  positive. Existing non-blocking duplicated-code, divergent-change and Note
  Garden findings were deliberately not changed.
- Diary began on `main` with local `HEAD`, `origin/main` and GitHub remote
  `main` all exactly
  `ce8cc5dfaa6216d7e044e7035a5a7de4bf8b0b0d`; Personal Website began on
  `main` with all three refs exactly
  `6fb5c4e5dd8283fd9438cd3eb6ca497da1f37beb`. Both tracked worktrees were
  clean. No stash, reset, checkout, user-file cleanup or PR was used.

#### Red to minimal Green evidence

- Diary Red used pinned Supabase CLI v2.109.1 against real PostgreSQL. A
  deterministic trigger rejected only the
  `20260804120000` `schema_migrations` insert after an existing owner Entry had
  been created at the previous schema. The CLI failed and the PostgreSQL
  rollback assertion returned `0`, proving product DDL/data had committed
  independently of bookkeeping. The product Red run was `1 failed in
  105.07s`, wall `106.19s`, exit `1`; an earlier harness-only run was corrected
  after confirming that this CLI version does not forward the injected
  exception text to stderr.
- Diary minimal Green removes the migration's top-level `BEGIN`/`COMMIT` and
  retains the explicit `LOCK TABLE public.entries IN SHARE ROW EXCLUSIVE MODE`
  inside one `DO` statement, as PostgreSQL otherwise rejects top-level `LOCK`
  outside a transaction block. Supabase CLI now owns one implicit transaction
  containing every migration statement and its bookkeeping insert. The new
  regression proved schema, grants, functions, backfill and bookkeeping all
  rolled back while the existing Entry, immutable Revision and processing row
  remained unchanged; after removing the injected failure, the same migration
  retried safely. Green was `1 passed in 69.64s`, wall `70.66s`, exit `0`.
- Website Red added two owner-visible Playwright cases beginning only after
  the Entry Time mutation committed and its Save rebuild failed. The successful
  midnight path removed deep reading Entry A while clearing recovery, and the
  failure path showed midnight did not enter the shared A/B rebuild. The
  product Red was `2 failed`, wall `20.50s`, exit `1`.
- Website minimal Green retains committed recovery ownership after the Save
  rebuild failure. Midnight and manual Refresh continue to call the same
  `rebuildHistoryWindow`; recovery is cleared only after that implementation
  finds independent reading A and changed active B. A missing A or B throws,
  fails closed and remains retryable. Explicit Calendar navigation separately
  retires the old-date recovery ref. The two new cases passed `2 passed in
  3.6s`, wall `14.92s`, exit `0`.

#### Preserved contracts and local validation

- Docker Desktop was confirmed as Linux engine `29.6.2`; the repository CLI
  remained pinned at v2.109.1. A clean ordered reset applied all 17 migrations
  and seed in wall `25.82s`, exit `0`.
- The new bookkeeping rollback/retry regression passed as stated above. The
  retained deterministic concurrent previous-version Create regression passed
  `1 passed in 70.12s`, wall `71.12s`, exit `0`, proving the explicit lock is
  held through backfill and trigger installation. The true upgrade-over-
  existing-data regression passed `1 passed in 70.10s`, wall `71.24s`, exit
  `0`. RLS, grants, PostgREST, FastAPI and previous-version contracts were not
  widened or rewritten.
- `python -m mypy src tests` found no issues in 21 source files, wall `3.71s`,
  exit `0`. The repository-safe ordered Ticket 03-08 set passed `65 passed, 1
  warning in 198.17s`, wall `199.65s`, exit `0`. The independent full suite
  passed `84 passed, 1 warning in 211.76s`, wall `212.85s`, exit `0`. The one
  warning was the existing Starlette/httpx deprecation. These runs exercised
  real Supabase, forced PostgreSQL RLS, PostgREST, FastAPI, Uvicorn and mobile
  Chromium seams.
- Website typecheck passed. The final focused deep-A/save/recovery/font/
  midnight/Calendar ownership set used four workers and zero retries and
  passed `14 passed in 9.1s`, wall `15.32s`, exit `0`. It preserved one fresh
  root plus at most four same-snapshot cursor requests, ordinary target 60, no
  old cursor, A/B exactly once, the existing viewport tolerance,
  `document.fonts.ready`, manual anchoring, pagination, IntersectionObserver,
  stale ownership and Calendar retirement.
- Three independent full Website processes each used exactly four workers and
  zero retries: run 1 `36 passed in 13.4s`, wall `22.83s`; run 2 `36 passed in
  14.4s`, wall `21.61s`; run 3 `36 passed in 14.8s`, wall `23.82s`. All exited
  `0`, had no retry or hang, and returned normally after only the existing
  post-summary Vite mock-proxy `ECONNREFUSED 127.0.0.1:8000` diagnostics. An
  earlier three-run validation consistently found the in-scope Calendar
  retirement regression at `35 passed, 1 failed`; the minimal explicit
  Calendar retirement fix was added before these three successful runs.
- Final `npm.cmd run build` completed Vite in `3.45s`, wall `12.33s`, exit `0`
  with only existing non-module-script warnings. The subsequent
  `npm.cmd run verify:build` passed in wall `0.47s`, exit `0`. All six named
  output directories created by this session were resolved under
  `E:\personal_website\test-results` and are absent after cleanup; no older
  output directory or user file was removed.

#### Pre-commit review, scope and publication

- The `implement` skill's pre-commit review ran Standards and Spec as separate
  read-only axes against the two exact starting SHAs. Standards reported zero
  findings and Spec reported zero findings. This was not a formal fixed-range
  review and no formal review record was appended.
- The implementation diff is limited to the migration and its real CLI system
  regression in Diary, plus `EntryExperience.tsx` and its two Playwright
  regressions in Personal Website. No `.env`, credential, production value,
  Ticket 09, Trash/delete, AI Draft, Queue, RAG or Agent change was added.
- Personal Website implementation commit
  `b6d61fdea942f5445bce59e4c6cc2baeb486ae93` contains only
  `EntryExperience.tsx` and `continuous-history.spec.ts` and was pushed to
  `main`. Exact-SHA [Website checks and Pages run
  31718206467](https://github.com/oscar940327/my-personal-website/actions/runs/31718206467)
  completed successfully; jobs
  [build 94508236223](https://github.com/oscar940327/my-personal-website/actions/runs/31718206467/job/94508236223)
  and
  [deploy 94508644927](https://github.com/oscar940327/my-personal-website/actions/runs/31718206467/job/94508644927)
  were both `completed/success`. Exact-SHA [pages build and deployment run
  31718205457](https://github.com/oscar940327/my-personal-website/actions/runs/31718205457)
  also completed successfully; jobs
  [build 94508237958](https://github.com/oscar940327/my-personal-website/actions/runs/31718205457/job/94508237958),
  [report-build-status 94508356302](https://github.com/oscar940327/my-personal-website/actions/runs/31718205457/job/94508356302)
  and
  [deploy 94508356401](https://github.com/oscar940327/my-personal-website/actions/runs/31718205457/job/94508356401)
  were all `completed/success`.
- Diary CI now pins that exact Website implementation SHA. The scoped Diary
  implementation commit and its exact-SHA Backend run/job evidence are reported
  in the implementation handoff after the remote gate completes. No PR will be
  created. The only permitted next step after that gate is a new formal
  fixed-range code-review session.

### 2026-08-14 - Fresh formal fixed-range code review requires changes

#### Session contract, starting gate and verdict

- This was a new formal fixed-range review session. The complete `code-review`
  skill was read first. Standards and Spec were reviewed by two isolated,
  read-only agents in parallel against both complete integrated ranges; the
  one-commit blocker-fix subranges were checked separately and did not replace
  the integrated review. All 25 changed files plus relevant source were
  inspected, not only tests or endpoint commits.
- Diary began on `main` with local `HEAD`, local `origin/main` and GitHub remote
  `main` all exactly
  `d179ce77a592d7d336ee43e70ac0f42030447b75`; its tracked worktree was clean.
  Personal Website began on `main` with all three refs exactly
  `b6d61fdea942f5445bce59e4c6cc2baeb486ae93`; its tracked worktree was clean.
- Overall verdict: **CHANGES-REQUIRED**.
  - Standards: **CHANGES-REQUIRED**, five findings: one High blocking hard
    violation, one Low non-blocking hard violation and three Low non-blocking
    Fowler judgments.
  - Spec: **CHANGES-REQUIRED**, two findings: one High blocking defect and one
    retained Low non-blocking scope finding.
  - The axes remain separately ordered below. They do not cancel or rerank one
    another. The shared High evidence is one underlying blocker, not two
    implementation tasks.

#### Fixed ranges and preflight

- Diary integrated range:
  `898a6056068ce282e36399d568ea6350bb413f29...d179ce77a592d7d336ee43e70ac0f42030447b75`.
  Both endpoints resolved, the merge-base was exactly the requested base, the
  range was non-empty with 22 commits, and complete-range `git diff --check`
  returned `0`. It contains 14 changed files, 7,150 insertions and 30
  deletions.
- Personal Website integrated range:
  `231ebe21ed09ec7d777f3c78ed6eb58aab396962...b6d61fdea942f5445bce59e4c6cc2baeb486ae93`.
  Both endpoints resolved, the merge-base was exactly the requested base, the
  range was non-empty with 11 commits, and complete-range `git diff --check`
  returned `0`. It contains 11 changed files, 3,319 insertions and 69
  deletions.
- Diary blocker-fix subrange
  `ce8cc5dfaa6216d7e044e7035a5a7de4bf8b0b0d...d179ce77a592d7d336ee43e70ac0f42030447b75`
  and Website blocker-fix subrange
  `6fb5c4e5dd8283fd9438cd3eb6ca497da1f37beb...b6d61fdea942f5445bce59e4c6cc2baeb486ae93`
  each resolved and contained one commit.

#### Standards review - CHANGES-REQUIRED

1. **High - blocking hard violation - migration/bookkeeping atomicity remains
   broken.** Diary
   `supabase/migrations/20260807120000_audit_and_transform_taipei_unsafe_entry_times.sql:1,105,137`
   still wraps its audit/backfill and `SHARE ROW EXCLUSIVE` lock in top-level
   `BEGIN`/`COMMIT`. Pinned Supabase CLI v2.109.1 queues parsed migration
   statements and then the `schema_migrations` insert; its pinned pgconn batch
   loses the implicit whole-batch transaction when transaction-control
   statements are present. Product DDL/data can therefore commit while the
   bookkeeping insert fails. The new regression at
   `tests/system/test_migration_upgrade.py:17,273-423` injects failure only for
   version `20260804120000`, so it cannot detect this second instance. This
   violates `docs/adr/0013-use-expand-contract-database-migrations.md:19`.
2. **Low - non-blocking hard workflow violation, preserved.** Personal Website
   `index.html:132` adds Note Garden within Ticket 08, contrary to
   `docs/agents/development-workflow.md:3,19` one-ticket scope. This is the
   known existing scope drift and was not changed.
3. **Low - Fowler Duplicated Code judgment, preserved.** Personal Website
   `src/diary/EntryExperience.tsx:976-982,1041-1048` repeats rebuilt-window
   installation and cleanup.
4. **Low - possible Fowler Divergent Change judgment, preserved.** Personal
   Website `src/diary/EntryExperience.tsx:160-275,461-752,893-1058` combines
   rebuild, pagination, ownership, midnight, mutation recovery, anchoring and
   dialogs.
5. **Low - Fowler Duplicated Code judgment, preserved.** Diary
   `tests/system/test_migration_upgrade.py:51-94` duplicates Docker/psql argv
   construction.

No additional documented-standard, RLS, grants, PostgREST, FastAPI,
previous-version, Ticket 03-08 or security violation was found.

#### Spec review - CHANGES-REQUIRED

1. **High - blocking - integrated migration/bookkeeping atomicity is still
   incomplete.** The `20260804120000` blocker fix is correct, but
   `20260807120000_audit_and_transform_taipei_unsafe_entry_times.sql:1,137`
   retains the same top-level transaction-control defect. Its DDL, immutable
   audit setup and data transformation can commit before its later
   `schema_migrations` insert. The new real-CLI regression covers only
   `20260804120000`. This violates `.scratch/diary/spec.md:363` and
   `docs/adr/0013-use-expand-contract-database-migrations.md:19` transactional
   migration-failure requirements.
2. **Low - retained known scope creep, unchanged.** Personal Website
   `index.html:132` adds the unrelated Note Garden link, contrary to
   `.scratch/diary/spec.md:193` existing-site preservation. No cleanup was
   authorized or performed.

No additional missing, partial, unasked-for or incorrectly implemented Ticket
08 behavior was found.

#### 2026-08-13 blocker and invariant dispositions

- **Migration statements plus bookkeeping: PARTIAL, still blocking.** The
  latest Diary subrange correctly removes top-level transaction control from
  `20260804120000`. Its explicit
  `LOCK TABLE public.entries IN SHARE ROW EXCLUSIVE MODE` is correctly wrapped
  in one `DO` statement and remains held to the CLI-owned implicit transaction
  end. The real v2.109.1 rollback/retry regression passes. The complete range
  nevertheless fails because changed migration `20260807120000` retains the
  same transaction/bookkeeping split and the regression does not exercise it.
- **2026-08-10 FK/Create race: CLOSED as a false positive.** No new evidence
  reopens it. The deterministic previous-version regression remains green and
  confirms the explicit lock excludes Create through backfill and trigger
  installation.
- **Failed Save rebuild crossing Taipei midnight: CLOSED.** Save, midnight and
  manual Refresh all call the shared `rebuildHistoryWindow`. Independent
  reading Entry A and changed Entry B are both mandatory; only a successful
  guard installs the rebuilt window and clears recovery. Missing A or B fails
  closed while retaining retryable recovery. Explicit Calendar navigation
  separately retires old-date recovery.
- Source and fresh Chromium validation retained one fresh root plus at most
  four same-snapshot cursor requests, ordinary target 60, no old cursor, A/B
  exactly once, viewport and `document.fonts.ready` anchoring, manual
  pagination, IntersectionObserver loading, stale-finally/loading ownership
  and Calendar retirement.
- Entry Time remains metadata only. Capture time, Original Content, immutable
  Revisions and AI processing obligations remain unchanged. Asia/Taipei
  grouping, Calendar counts, microsecond/UUID ordering and snapshot behavior
  remain correct. Forced RLS, grants, direct PATCH denial, PostgREST owner-token
  evaluation, FastAPI authorization and previous-version/Ticket 03-08
  compatibility showed no additional regression.

#### Exact endpoint GitHub Actions

- Diary exact endpoint
  `d179ce77a592d7d336ee43e70ac0f42030447b75`:
  [Backend checks run 31718529209](https://github.com/oscar940327/diary/actions/runs/31718529209)
  was attempt 1 `completed/success`; its only returned
  [test job 94509319178](https://github.com/oscar940327/diary/actions/runs/31718529209/job/94509319178)
  was also `completed/success` at that exact SHA.
- Personal Website exact endpoint
  `b6d61fdea942f5445bce59e4c6cc2baeb486ae93`:
  [Website checks and Pages run 31718206467](https://github.com/oscar940327/my-personal-website/actions/runs/31718206467)
  was attempt 1 `completed/success`; jobs
  [build 94508236223](https://github.com/oscar940327/my-personal-website/actions/runs/31718206467/job/94508236223)
  and
  [deploy 94508644927](https://github.com/oscar940327/my-personal-website/actions/runs/31718206467/job/94508644927)
  were `completed/success`.
- At the same Website SHA,
  [pages build and deployment run 31718205457](https://github.com/oscar940327/my-personal-website/actions/runs/31718205457)
  was attempt 1 `completed/success`; jobs
  [build 94508237958](https://github.com/oscar940327/my-personal-website/actions/runs/31718205457/job/94508237958),
  [report-build-status 94508356302](https://github.com/oscar940327/my-personal-website/actions/runs/31718205457/job/94508356302)
  and
  [deploy 94508356401](https://github.com/oscar940327/my-personal-website/actions/runs/31718205457/job/94508356401)
  were all `completed/success`.

#### Fresh local validation

##### Personal Website

- `npm.cmd run typecheck`: wall `1.9s`, exit `0`.
- Focused A/B, Save/recovery, font/layout, midnight, stale ownership and
  Calendar-retirement Chromium set: exactly four workers, zero retries,
  `14 passed in 13.2s`, command wall `27.2s`, exit `0`, no hang or
  post-summary process error.
- One independent complete Chromium run: exactly four workers, zero retries,
  `36 passed in 16.5s`, command wall `25.4s`, exit `0`, no retry or hang. It
  emitted only the known post-summary Vite mock-proxy
  `ECONNREFUSED 127.0.0.1:8000` diagnostic; the command returned normally.
- `npm.cmd run build`: Vite `3.13s`, command wall `8.8s`, exit `0`, with only
  existing non-module-script warnings. `npm.cmd run verify:build`: wall
  `1.3s`, exit `0`.
- The only two output directories created by this session were absolute-path
  verified beneath `E:\personal_website\test-results`, then removed. Both are
  absent. No pre-existing output directory or user file was removed.

##### Diary

- Pinned runtime `npx.cmd supabase --version` returned `2.109.1`, wall `2.1s`,
  exit `0`. `python -m mypy src tests` found no issue in 21 source files, wall
  `1.5s`, exit `0`.
- Focused real migration set covered `20260804120000` bookkeeping rollback and
  retry, previous-version concurrent Create exclusion, and true
  upgrade-over-existing-data transformation: `3 passed in 168.89s`, command
  wall `170.8s`, exit `0`, no retry or hang.
- Complete suite: `84 passed, 1 warning in 218.89s`, command wall `220.6s`,
  exit `0`, no retry or hang. The existing warning is the Starlette/httpx
  deprecation. The run exercised real Supabase Auth/PostgreSQL/PostgREST,
  forced RLS, FastAPI, Uvicorn and mobile Chromium.
- An additional no-file-change real-CLI probe injected failure only at the
  `20260807120000` bookkeeping insert. The first PowerShell harness attempt
  misclassified normal CLI stderr progress as an exception and was discarded
  as harness-only evidence: wall `25.2s`, exit `1`, no product assertion. The
  corrected probe completed in wall `63.0s`: injected migration exit `1`,
  `PARTIAL_COMMIT_PROBE=1` proved the bookkeeping row absent while product DDL
  existed, then failure removal produced retry exit `0` and
  `RETRY_BOOKKEEPING_PROBE=1`. Cleanup full reset and session-started stack stop
  both exited `0`; there was no hang.

#### Scope, modification and next-step audit

- Fixed-range filenames contain no `.env` or Ticket 09 file. Added source was
  reviewed for credentials; no production secret, key or environment value was
  found. Runtime-only local Supabase synthetic values are not reproduced here.
- Existing Note Garden scope drift remains exactly as reviewed. Existing
  duplicated-code and divergent-change findings were neither fixed nor
  refactored. No unrelated HOME, PROJECT, JOURNEY, MktAgent or VideoNote work
  was performed.
- No product, migration, test or CI code was modified by this review. No
  Personal Website file was modified. Ticket 09, Trash/delete, AI Draft,
  Queue, RAG and Agent work were not started. No PR was created.
- After validation and runtime cleanup, both tracked worktrees remained clean
  at the reviewed endpoints. This EOF append is the review session's only file
  change. It must be preserved as one Diary documentation-only commit and
  pushed, then that exact commit's Backend run and every returned job must
  reach `completed/success`.
- Because this review failed, the only permitted next work is another new
  Ticket 08 blocker implementation session for the `20260807120000`
  migration/bookkeeping atomicity defect. Ticket 09 remains blocked.

### 2026-08-14 - Remaining migration atomicity blocker fixed

#### Session boundary and starting gate

- This was a new Ticket 08 blocker implementation/TDD session limited to the
  one High finding confirmed by the 2026-08-14 formal review. It did not run a
  formal fixed-range review and does not claim that Ticket 08 passed review.
- Diary began on `main` with local `HEAD`, local `origin/main` and GitHub
  remote `main` all exactly
  `54ab40a3a838e8228a0271339434a95bd6079b91`; Personal Website began on
  `main` with all three refs exactly
  `b6d61fdea942f5445bce59e4c6cc2baeb486ae93`. Both tracked worktrees were
  clean. No stash, reset, checkout, PR or user-file cleanup was used.
- The public TDD seam was pinned Supabase CLI v2.109.1 applying the real
  ordered migrations to local PostgreSQL. Failure injection was a trigger on
  `supabase_migrations.schema_migrations` whose only rejecting branch matched
  version `20260807120000`.

#### Deterministic Red and root cause

- The new regression reset to preceding version `20260805120000`, created one
  owner Entry at `9999-12-31T16:00:00Z`, injected the version-specific
  bookkeeping failure and ran the real CLI upgrade. With the original `071`
  top-level `BEGIN`/`COMMIT`, Red was `1 failed in 116.56s`, command wall
  `117.84s`, exit `1`, with zero retry and no hang.
- The observed rollback state was exact: bookkeeping was absent, while product
  DDL, the immutable audit row, the Entry Time transformation and the current
  history-position transformation had all committed. This proved the review's
  partial-commit symptom rather than an adjacent migration failure.
- The confirmed root cause was the top-level `COMMIT` ending the migration
  transaction before Supabase CLI v2.109.1 inserted its migration bookkeeping
  row. The lower-ranked hypotheses that the CLI did not provide an implicit
  whole-batch transaction or that the version-specific trigger targeted a
  different migration were falsified by Green.

#### Minimal Green and preserved lock

- The only product change removes top-level `BEGIN` and `COMMIT` from
  `20260807120000_audit_and_transform_taipei_unsafe_entry_times.sql`. The
  existing `LOCK TABLE public.entries IN SHARE ROW EXCLUSIVE MODE` remains
  explicit and is wrapped in one `DO` statement, matching the unchanged `041`
  migration. PostgreSQL holds that table lock to the CLI-owned transaction end,
  which now occurs only after the `schema_migrations` insert succeeds or the
  complete batch rolls back.
- The same regression turned Green at `1 passed in 106.50s`, command wall
  `107.58s`, exit `0`, with zero retry and no hang. It proved bookkeeping,
  product DDL, audit data, Entry transformation and history transformation all
  rolled back together. After the failure trigger was removed, the migration
  retried successfully and each bookkeeping/effect assertion had exactly one
  row or one current transformed position.
- Audit schema and semantics, immutable trigger, RLS, grants, PostgREST,
  FastAPI and Entry transformation rules were not changed. Migration
  `20260804120000` has no diff. A read-only scan of every Ticket 08 migration
  found no remaining top-level `BEGIN`, `START TRANSACTION`, `COMMIT` or
  `ROLLBACK`; PL/pgSQL block-local `begin`/`end` statements are not transaction
  control.

#### Required local validation

- Pinned CLI version check returned `2.109.1`, exit `0`. The first clean-reset
  invocation correctly refused because the stack was stopped: wall `2.38s`,
  exit `1`, no migration assertion, retry or hang. This session then started
  the local stack and the clean ordered reset applied all 17 migrations plus
  seed in wall `65.61s`, exit `0`, with no retry or hang.
- Existing `041` rollback/retry validation first completed its product checks
  but received a local Auth `502` while its `finally` cleanup reprovisioned a
  user: `1 failed in 105.36s`, wall `106.47s`, exit `1`. A second attempt met
  the same `502` during fixture setup: `1 error in 34.83s`, wall `35.94s`, exit
  `1`. Container inspection showed healthy Auth but an unhealthy Kong upstream
  after repeated resets under the session's full-stack ownership. The session
  stopped that stack and returned lifecycle ownership to the repository pytest
  fixture; the required regression then passed `1 passed in 106.63s`, wall
  `107.73s`, exit `0`. These were two recorded infrastructure retries; no run
  hung, and no product assertion failed.
- The previous-version concurrent Create regression passed `1 passed in
  106.47s`, wall `107.58s`, exit `0`, with zero retry and no hang. The
  2026-08-10 FK/Create finding remains closed as a false positive; this session
  found no new evidence and did not reopen it.
- The upgrade-over-existing-data regression passed `1 passed in 109.21s`, wall
  `110.33s`, exit `0`, with zero retry and no hang. It retained the two unsafe
  Entry transformations, safe control, immutable audits, RLS, grants,
  PostgREST, FastAPI, history/calendar behavior and repeat-idempotency checks.
- `python -m mypy src tests` found no issues in 21 source files, wall `2.61s`,
  exit `0`. Complete `python -m pytest -q --tb=short` passed `85 passed, 1
  warning in 306.33s`, command wall `307.50s`, exit `0`, with zero pytest retry
  and no hang. The warning is the existing Starlette/httpx deprecation.

#### Scope, cleanup and handoff

- The implementation diff before this append contained only the `071`
  migration and its real-CLI system regression. No Personal Website file was
  modified. Existing Note Garden scope drift and duplicated-code/divergent-
  change findings were not handled. Ticket 09, Trash/delete, AI Draft, Queue,
  RAG and Agent work were not started.
- No named test-output directory was created. The pre-existing ignored
  `.pytest_cache` was used by pytest and left untouched because it was not
  established as session-created. The session-started Supabase stack was
  stopped; no `supabase_*_diary` container remained. No debug marker, `.env`,
  credential or production configuration was added.
- The scoped migration, regression and this append-only record are committed
  together and pushed to Diary `main`. Exact commit and Backend run/job links
  are recorded in the completion handoff after every job at that SHA reaches
  `completed/success`. The only permitted next step is another new Ticket 08
  formal fixed-range code-review session; Ticket 09 remains blocked.

### 2026-08-14 - Fresh formal fixed-range code review finds a cross-migration blocker

#### Session contract, starting gate and verdict

- This was a new review-only session under the repository `code-review`
  skill. Two isolated read-only agents reviewed Standards and Spec in
  parallel against both complete integrated ranges. The latest Diary
  blocker-fix subrange received additional inspection but did not replace the
  complete review. No product, migration, test or Website file was modified.
- Diary began on `main` with local `HEAD`, local `origin/main` and GitHub
  remote `main` all exactly
  `04d68d4836686b568100c0eb81fe96c421f89ecb`; Personal Website began on
  `main` with all three refs exactly
  `b6d61fdea942f5445bce59e4c6cc2baeb486ae93`. Both tracked worktrees were
  clean. Any mismatch would have stopped the session.
- Overall verdict: **REVIEW-FAILED / CHANGES-REQUIRED**.
  - Standards: **CHANGES-REQUIRED**, one High blocking hard violation.
  - Spec: **CHANGES-REQUIRED**, one High blocking defect.
  - Both axes independently identify the same underlying defect; it is one
    implementation task, but the axes remain separately reported and do not
    cancel or rerank one another.
- This review does **not** claim Ticket 08 PASS. Ticket 08 remains
  `ready-for-agent`, and Ticket 09 remains blocked.

#### Fixed ranges and preflight

- Diary integrated range:
  `898a6056068ce282e36399d568ea6350bb413f29...04d68d4836686b568100c0eb81fe96c421f89ecb`.
  Both endpoints resolved, the merge-base is the specified base, the diff is
  non-empty with 24 commits, and complete-range `git diff --check` returned
  `0`. It contains 14 changed files, 7,684 insertions and 30 deletions.
- Personal Website integrated range:
  `231ebe21ed09ec7d777f3c78ed6eb58aab396962...b6d61fdea942f5445bce59e4c6cc2baeb486ae93`.
  Both endpoints resolved, the merge-base is the specified base, the diff is
  non-empty with 11 commits, and complete-range `git diff --check` returned
  `0`. It contains 11 changed files, 3,319 insertions and 69 deletions.
- Diary blocker-fix subrange:
  `54ab40a3a838e8228a0271339434a95bd6079b91...04d68d4836686b568100c0eb81fe96c421f89ecb`.
  It resolves to one commit, is non-empty, and subrange `git diff --check`
  returned `0`. Its only changed files are this Ticket record, migration
  `20260807120000` and the real migration-upgrade regression.

#### Standards review - CHANGES-REQUIRED

1. **High - blocking hard violation - a previous-version Create can strand
   the upgrade between migrations `071` and `091`.** Migration
   `supabase/migrations/20260807120000_audit_and_transform_taipei_unsafe_entry_times.sql:103-137`
   correctly holds `SHARE ROW EXCLUSIVE` through its own CLI-owned transaction
   and `schema_migrations` insert. Supabase CLI v2.109.1, however, applies
   pending files with separate `ExecBatch` transactions. That transaction and
   lock end before
   `supabase/migrations/20260809120000_enforce_taipei_safe_entry_time_range.sql:1-6`
   requests the lock needed to add its tighter CHECK.

   A previous-version Create already queued behind `071` can therefore obtain
   `RowExclusiveLock` immediately after `071` commits, while migration `051`'s
   RPC still accepts `9999-12-31T16:00:00Z`. The Create commits before queued
   `091` validation; `091` then fails. Because `071` bookkeeping already
   committed, ordinary retry skips its audit/transformation and fails again on
   the stranded row. This violates ADR 0013's expand-contract,
   previous-version compatibility, migration-failure and safe-retry rules.

- No other included Standards finding was found. Per the explicit review
  boundary, the existing Note Garden scope drift and existing Duplicated Code
  and Divergent Change judgements were not handled or reported as new work.

#### Spec review - CHANGES-REQUIRED

1. **High - blocking - the `051` to `071` to `091` contract is not safe under
   a concurrent previous-version Create.** Ticket 08 requires migration-safe
   Entry Time transformation while the immediately previous application
   remains usable. The product spec requires transactional migration failure
   to stop release before promotion, and ADR 0013 requires safe
   expand-contract compatibility. The cross-file transaction boundary above
   leaves a write window that creates a persistent, non-retryable failed
   upgrade. Existing regressions cover data present before `071`, `071`
   bookkeeping failure, and the separate `041` concurrency question; none
   covers an unsafe Create queued at the `071` to `091` boundary.

- No other missing, partial, unasked-for or incorrectly implemented Ticket 08
  behavior was found within the requested boundary. Existing Note Garden,
  duplicated-code and divergent-change findings were explicitly excluded.

#### Atomicity and invariant dispositions

- **`071` statements plus bookkeeping: PASS within one migration.** The
  latest fix removes top-level `BEGIN`/`COMMIT`, retains the explicit lock in
  one `DO` statement, and lets PostgreSQL hold the lock through the CLI-owned
  transaction and bookkeeping insert. The version-specific real CLI
  regression proves product DDL, audit data, Entry transformation, current
  history transformation and bookkeeping roll back together, then retry
  produces exactly one bookkeeping row, audit row, transformed Entry and
  current position.
- **Cross-migration `071` to `091` safety: FAIL.** The `071` lock cannot protect
  the gap after its own committed bookkeeping and before the separately
  transacted `091` constraint. A fix needs to close that write window and add
  a real CLI regression with a preceding-version-valid but Taipei-unsafe
  concurrent Create.
- **`041` rollback/retry fix: unchanged and PASS.** The latest subrange has no
  diff for `20260804120000_change_entry_time_and_stabilize_history.sql`; its
  own explicit lock, atomic bookkeeping regression and safe retry remain
  green.
- **2026-08-10 FK/Create finding: remains closed as a false positive.** The
  deterministic `041` previous-version concurrent Create regression remains
  green. The new finding is a different `071` to `091` transaction-boundary
  race and does not reopen the old FK/backfill/trigger allegation.
- Audit schema and immutable evidence semantics, RLS, grants, direct PATCH
  denial, PostgREST owner-token behavior, FastAPI validation/authorization,
  Entry transformation rules, capture time, Original Content, immutable Entry
  Revisions and AI processing obligations show no additional drift.

#### Independent runtime proof of the blocking race

- A no-file-change local PostgreSQL/CLI probe reset to migration `051`, paused
  `071` after it held `SHARE ROW EXCLUSIVE`, and queued the actual
  previous-version `create_diary_entry` RPC with Entry Time
  `9999-12-31T16:00:00Z`.
- Releasing `071` produced Create exit `0` and first-upgrade exit `1`. The
  exact stranded state was `071` bookkeeping count one, `091` bookkeeping
  count zero, one unsafe active Entry and no audit row for it. Ordinary
  `migration up` retry again exited `1` because booked `071` did not rerun.
- Probe wall was `47.89s`, with zero harness retry and no hang. Its deliberate
  ordinary migration retry reproduced the same exit `1`; cleanup clean reset
  returned `0`. It created no repository or output file.

#### Exact endpoint GitHub Actions

- [Backend checks run 31728057908](https://github.com/oscar940327/diary/actions/runs/31728057908)
  is attempt 1 `completed/success` at exact reviewed Diary SHA
  `04d68d4836686b568100c0eb81fe96c421f89ecb`.
- Its complete returned job list contains only
  [test job 94541286541](https://github.com/oscar940327/diary/actions/runs/31728057908/job/94541286541),
  which is `completed/success`; every returned step is also
  `completed/success`.

#### Required local validation

- Pinned `npx.cmd supabase --version` returned `2.109.1`, wall `1.79s`, exit
  `0`. An initial sandbox-only attempt could not write the CLI telemetry temp
  file: wall `13.76s`, exit `1`, no migration assertion, retry or hang. The
  first status check after that found Docker stopped: wall `6.61s`, exit `1`,
  no product assertion or hang.
- The session-started stack completed clean ordered reset of all 17 migrations
  plus seed: wall `35.56s`, exit `0`, zero retry and no hang.
- `071` bookkeeping rollback/retry regression: `1 passed in 108.72s`; setup
  `39.92s`, call `68.76s`, command wall `111.91s`, exit `0`, zero retry and no
  hang.
- Unchanged `041` bookkeeping rollback/retry regression: `1 passed in
  106.62s`; setup `36.84s`, call `69.75s`, command wall `107.70s`, exit `0`,
  zero retry and no hang.
- Previous-version concurrent Create regression: `1 passed in 105.20s`;
  setup `37.89s`, call `67.27s`, teardown `0.01s`, command wall `106.53s`,
  exit `0`, zero retry and no hang.
- Upgrade-over-existing-data regression completed its product assertions but
  first received local Kong/Auth `502` during teardown user restoration:
  `1 failed in 103.40s`, wall `104.45s`, exit `1`. This was one recorded
  infrastructure retry, not a product assertion failure. After the unhealthy
  stack was stopped, the fixture-owned clean lifecycle passed `1 passed in
  108.68s`; setup `49.43s`, call `46.78s`, teardown `12.42s`, wall `109.70s`,
  exit `0`. Neither run hung.
- `python -m mypy src tests`: no issues in 21 source files, wall `2.34s`, exit
  `0`.
- Complete `python -m pytest -q --tb=short`: `85 passed, 1 warning in
  298.19s`, command wall `299.25s`, exit `0`, zero retry and no hang. The one
  warning is the existing Starlette/httpx deprecation. This run exercised the
  real Supabase Auth/PostgreSQL/PostgREST, forced RLS, FastAPI, Uvicorn and
  mobile Chromium paths.

#### Scope, cleanup and handoff

- No session-created named output directory required removal. Diary
  `.pytest_cache` and Personal Website `test-results` existed before this
  session and were deliberately left untouched. Diary `test-results` and both
  `playwright-report` paths remained absent.
- The session-owned Supabase stack was stopped; absolute container inspection
  returned zero `supabase_*_diary` containers. Both tracked worktrees were
  clean at their reviewed endpoints before this EOF append.
- This append-only Ticket record is the session's only file change. No PR was
  created. Ticket 09, Trash/delete, AI Draft, Queue, RAG and Agent work were
  not started. The existing Note Garden, duplicated-code and divergent-change
  findings were not handled.
- Only this documentation record may be committed and pushed. Its exact-SHA
  Backend run and every returned job must reach `completed/success` before
  handoff. Because both review axes have a blocking finding, the next allowed
  work is a separate Ticket 08 implementation/TDD session for the `071` to
  `091` migration boundary, followed by another fresh complete fixed-range
  review. Ticket 09 must not begin.

### 2026-08-14 - Cross-migration 071 to 091 blocker fixed

#### Session boundary, starting gate and TDD seam

- This was a new Ticket 08 blocker implementation/TDD session limited to the
  one High cross-migration finding in the latest formal review. It used the
  complete repository `implement` and `tdd` instructions. It did not invoke or
  begin a formal code review and does not claim that Ticket 08 passed review.
- Diary began on `main` with local `HEAD`, local `origin/main` and GitHub
  remote `main` all exactly
  `3bd0e320f07e948acca48ba3a621223aa9907cb1`; Personal Website began on
  `main` with all three refs exactly
  `b6d61fdea942f5445bce59e4c6cc2baeb486ae93`. Both tracked worktrees were
  clean. Any mismatch would have stopped the session.
- The confirmed public seam was Supabase CLI v2.109.1 applying the real
  ordered local migrations to PostgreSQL while a preceding-version
  `create_diary_entry` call was queued at migration `071`'s explicit table
  lock. No mock or migration-file reimplementation was used.

#### Deterministic Red and root cause

- The new regression reset to `20260805120000`, created one preceding unsafe
  Entry, paused the real `071` transformation after it held
  `SHARE ROW EXCLUSIVE`, and queued an actual preceding-version Create with
  `9999-12-31T17:00:00Z`. PostgreSQL's lock queue deterministically let that
  Create commit after `071` bookkeeping and before `091` obtained its lock.
- With the original `091`, Red was `1 failed in 117.69s`, command wall
  `119.11s`, exit `1`, zero retry and no hang. Durable state proved the exact
  reviewed defect: `071` bookkeeping and its preceding-row audit/transform
  were committed; `091` bookkeeping and CHECK were absent; the concurrent
  unsafe Entry was present without an audit; and ordinary `migration up`
  retry still failed because booked `071` did not rerun.
- The root cause was the Supabase CLI v2.109.1 transaction boundary between
  separately executed migration files. `071`'s correct CLI-owned transaction
  and lock ended after its bookkeeping insert, leaving a write window before
  the separately transacted original `091` CHECK.

#### Minimal Green and transaction evidence

- The only product change is in
  `20260809120000_enforce_taipei_safe_entry_time_range.sql`. Its first
  statement now explicitly locks `public.entries` in
  `SHARE ROW EXCLUSIVE` mode. In the same CLI-owned transaction, `091`
  extends the immutable audit's version constraint, records any gap Entry
  with migration version `20260809120000`, applies the unchanged exact
  24-hour subtraction, adds the Taipei-safe CHECK, replaces the two RPCs and
  completes CLI bookkeeping.
- No top-level `BEGIN`, `START TRANSACTION`, `COMMIT` or `ROLLBACK` was added.
  Migration `20260807120000` retains its existing explicit lock and atomicity
  without a diff. Migration `20260804120000` is also byte-for-byte unchanged.
- The regression injects failure only at the `091` bookkeeping insert. It
  proves the failed transaction rolls back the audit-version constraint,
  gap audit, gap transformation, current history-position transformation,
  Taipei-safe CHECK, RPC replacements and `091` bookkeeping together while
  leaving already committed `071` intact. After removing the injection,
  ordinary retry succeeds. A further `migration up` is a no-op, and exact
  cardinalities prove one `071` bookkeeping row, one `091` bookkeeping row,
  two source-specific audit rows, one concurrent Entry, one Revision, one AI
  processing obligation and one current transformed history position.
- The first Green product run had all five durable database assertions true
  but a CLI diagnostic-string assertion failed because v2.109.1 did not
  forward the PostgreSQL trigger message: `1 failed in 110.12s`, wall
  `111.20s`, exit `1`. A combined-output variation failed for the same
  harness-only reason: `1 failed in 112.11s`, wall `113.21s`, exit `1`.
  Neither run retried or hung. The implementation-coupled diagnostic-string
  assertion was removed while all durable behavior assertions were retained.
- The corrected behavior regression passed `1 passed in 112.57s`, wall
  `113.75s`, exit `0`. After direct audit-constraint rollback and Green-state
  assertions were added, its final run passed `1 passed in 89.90s`, wall
  `91.73s`, exit `0`. Both Green runs had zero retry and no hang.

#### Required validation

- An initial sandbox-only CLI attempt could not write its telemetry temp file:
  wall `6.9s`, exit `1`, with no migration assertion, retry or hang. An
  approved status check then returned pinned version `2.109.1` and correctly
  reported that the stack was stopped. The formal standalone version check
  returned exactly `2.109.1`, wall `1.46s`, exit `0`.
- The session-owned stack started in wall `24.29s`, exit `0`. Clean ordered
  reset applied all 17 migrations in order plus seed, wall `22.87s`, exit `0`,
  zero retry and no hang.
- The required existing real-CLI set passed `4 passed in 212.40s`, command
  wall `213.48s`, exit `0`, zero retry and no hang. Individual call durations
  were: `071` bookkeeping rollback/retry `47.40s`; unchanged `041`
  bookkeeping rollback/retry `46.42s`; original previous-version concurrent
  Create regression `46.10s`; upgrade-over-existing-data regression `45.47s`.
- Final `python -m mypy src tests` found no issues in 21 source files, wall
  `3.24s`, exit `0`. The final complete
  `python -m pytest -q --tb=short` passed `86 passed, 1 warning in 337.01s`,
  command wall `339.16s`, exit `0`, zero retry and no hang. The warning is the
  existing Starlette/httpx deprecation. An earlier complete run before the
  final catalog assertions also passed `86 passed, 1 warning in 303.31s`,
  wall `304.48s`, exit `0`.

#### Preserved contracts, cleanup and handoff

- Audit reason, exact transformation, immutable trigger, RLS, grants,
  PostgREST behavior, FastAPI validation/authorization, Entry metadata-only
  semantics, Original Content, immutable Revisions and AI obligations remain
  unchanged. The new audit row truthfully records `091` while preceding rows
  retain `071`. The 2026-08-10 `041` FK/Create finding remains closed as a
  false positive; the original concurrency regression stayed Green.
- Personal Website remained clean and unchanged at its required SHA. Existing
  Note Garden scope drift and duplicated-code/divergent-change findings were
  not handled. Ticket 09, Trash/delete, AI Draft, Queue, RAG and Agent work
  were not started. No PR was created.
- The session-owned Supabase stack stopped in wall `19.99s`, exit `0`, and no
  `supabase_*_diary` container remained. No named test output directory was
  created: absolute checks confirmed Diary `test-results` and
  `playwright-report` absent. The pre-existing ignored `.pytest_cache` was
  left untouched; no user or pre-existing output directory was removed.
- The scoped `091` migration, deterministic real-CLI regression and this
  append-only record are the only files permitted in the implementation
  commit. After push, that exact documentation/implementation commit's
  Backend run and every returned job must reach `completed/success` before
  handoff. This session is not a formal code review and cannot declare Ticket
  08 PASS. The only permitted next step is a new complete fixed-range
  code-review session; Ticket 09 remains blocked.

### 2026-08-14 - Fresh formal fixed-range review finds a same-Entry migration gap

#### Session contract, starting gate and overall verdict

- This was a new read-only formal review under the repository `code-review`
  skill. Standards and Spec ran as isolated review axes against both complete
  integrated ranges; the latest Diary blocker-fix subrange received separate
  inspection and did not replace the complete review. The primary reviewer
  independently inspected all 14 Diary and 11 Personal Website changed files,
  every Ticket 08 migration, the related source and the complete Ticket/spec
  history rather than relying on endpoint commits or passing tests.
- Diary began on `main` with local `HEAD`, local `origin/main` and GitHub
  remote `main` all exactly
  `fd46d8a96e43bfdde6330c17e1b1b18846af6c56`; Personal Website began on
  `main` with all three refs exactly
  `b6d61fdea942f5445bce59e4c6cc2baeb486ae93`. Both tracked worktrees were
  clean. The first sandboxed remote check could not reach GitHub (wall `0.8s`,
  exit `1`); the permitted network retry completed both exact remote checks
  successfully (outer wall `6.9s`, each command exit `0`, no hang).
- Diary integrated range:
  `898a6056068ce282e36399d568ea6350bb413f29...fd46d8a96e43bfdde6330c17e1b1b18846af6c56`.
  Both endpoints resolve, the range is non-empty with 26 commits and 14 changed
  files, and complete-range `git diff --check` returned `0`.
- Personal Website integrated range:
  `231ebe21ed09ec7d777f3c78ed6eb58aab396962...b6d61fdea942f5445bce59e4c6cc2baeb486ae93`.
  Both endpoints resolve, the range is non-empty with 11 commits and 11 changed
  files, and complete-range `git diff --check` returned `0`.
- Latest Diary blocker-fix subrange:
  `3bd0e320f07e948acca48ba3a621223aa9907cb1...fd46d8a96e43bfdde6330c17e1b1b18846af6c56`.
  It is non-empty with one commit and three changed files; subrange
  `git diff --check` returned `0`.
- Overall verdict: **REVIEW-FAILED / CHANGES-REQUIRED**. Diary Standards and
  Spec each contain the same High blocking defect. Personal Website passes
  both axes with zero included finding. The axes remain separately reported
  and do not cancel or rerank one another. Ticket 08 is not PASS.

#### Standards review

- **Diary: CHANGES-REQUIRED — one High blocking hard violation.**
- **Personal Website: PASS — zero included findings.**

1. **High — blocking hard violation — `091` cannot self-heal an already-
   audited Entry changed again during the `071→091` transaction gap.** The
   immediately previous Change RPC accepts timestamps through
   `9999-12-31T23:59:59.999999Z` and updates an existing Entry at
   `supabase/migrations/20260804130000_restrict_entry_time_to_python_utc_range.sql:48-74`.
   `071` permits only one audit row per Entry at
   `supabase/migrations/20260807120000_audit_and_transform_taipei_unsafe_entry_times.sql:1-8`
   and makes that evidence immutable at `:37-42,70-100`. After `071` audits
   and transforms Entry X from `16:00Z`, the previous RPC can therefore commit
   a different unsafe `17:00Z` value after `071` releases its lock and before
   separately transacted `091` owns its lock.

   `091` then discards the required second evidence pair through
   `ON CONFLICT (entry_id) DO NOTHING` at
   `supabase/migrations/20260809120000_enforce_taipei_safe_entry_time_range.sql:16-36`.
   Its update at `:38-44` skips X because current `17:00Z` no longer equals
   the retained `071` audit's `original_entry_at=16:00Z`; the Taipei-safe
   CHECK at `:46-51` fails. Ordinary retry reaches the identical state. This
   violates ADR 0013's immediately-previous-version compatibility,
   transactional migration-failure and safe-retry requirements at
   `docs/adr/0013-use-expand-contract-database-migrations.md:11,17-19,23-24`.

No other included Standards finding was found. Per the explicit session
boundary, known Note Garden, Duplicated Code and Divergent Change findings are
excluded rather than repeated or handled.

#### Spec review

- **Diary: CHANGES-REQUIRED — one High blocking finding.**
- **Personal Website: PASS — zero included findings.**

1. **High — blocking — the migration does not audit/transform every gap row
   and ordinary retry is not self-healing.** The trigger and evidence are the
   same as the Standards finding. It contradicts the Ticket 08 accepted
   migration contract that every unsafe original and exact transformed value
   is retained while both previous and current application contracts remain
   usable (`.scratch/diary/issues/08-change-entry-time-and-regroup.md:1273-1299`),
   the product's expand-contract and transactional-failure requirements
   (`.scratch/diary/spec.md:362-363`), and ADR 0013. The new Create-only
   regression at `tests/system/test_migration_upgrade.py:638-1016` uses a new
   `entry_id`, so it cannot exercise a second unsafe Change on an Entry whose
   immutable `071` audit already occupies that primary key.

No other missing, partial, incorrectly implemented or non-excluded scope
behavior was found in either complete range.

#### Latest blocker and invariant dispositions

- **New `071→091` concurrent Create path: PASS for the covered new-Entry
  case.** `091` starts with `SHARE ROW EXCLUSIVE` at lines `1-5`, and its
  audit/transform, CHECK, RPC replacements and bookkeeping share the pinned
  CLI-owned transaction. The regression proves injected `091` bookkeeping
  failure rolls every `091` effect back with committed `071` preserved;
  ordinary retry and no-op repeat apply effects/bookkeeping exactly once.
- **Cross-migration same-Entry Change path: FAIL.** Two no-file-change pinned
  CLI probes reproduced the source defect. The stronger probe loaded the
  actual previous-version `043` Change function and called it as the
  authenticated owner. The function returned the same Entry at
  `9999-12-31T17:00:00Z`; first `migration up` failed adding the CHECK and an
  ordinary retry failed identically. Durable state was unsafe Entry `17:00Z`,
  exactly one old `071` audit whose original is `16:00Z`, `091` bookkeeping
  count zero and Taipei CHECK count zero.
- **`071` per-file atomicity and explicit lock: PASS, unchanged.** Its blob is
  identical across the latest subrange
  (`60c170be799f39c9171e9548b4cdb82662fe9955`), and its lock/audit/transform
  remains at lines `103-137`.
- **`20260804120000`: PASS, byte-for-byte unchanged in the latest subrange.**
  Its blob is identical on both endpoints
  (`ab934f7fc4dc489944509ee3767a416f3b2a58d1`); its explicit lock and
  rollback/retry behavior did not regress.
- **2026-08-10 `041` FK/Create finding: remains closed as a false positive.**
  The original deterministic previous-version concurrent Create regression
  is green. The present blocker is new direct Change-path evidence at the
  separate `071→091` boundary and does not reopen that allegation.
- Audit reason/exact 24-hour transformation semantics, immutable trigger, RLS,
  grants, PostgREST owner-token behavior, FastAPI validation/authorization,
  metadata-only Entry Time semantics, capture time, Original Content,
  immutable Revisions, AI obligations, History/Calendar ordering and Ticket
  03–08 behavior show no additional finding in the inspected and exercised
  paths.

#### Required validation evidence

##### Diary

- `npx.cmd supabase --version`: the sandbox attempt hit the CLI telemetry-file
  ACL (`1.33s`, exit `1`); the allowed retry returned exactly `2.109.1`
  (wall `1.72s`, exit `0`, retry count one, no hang).
- Initial `npx.cmd supabase status` correctly found the stack stopped (wall
  `2.41s`, exit `1`); session-owned start passed (wall `38.40s`, exit `0`).
- Clean ordered `npx.cmd supabase db reset --local` applied all 17 migrations
  and seed in wall `34.46s`, exit `0`, zero retry and no hang.
- The five required real-CLI regressions ran together with `--durations=0`:
  `5 passed in 367.79s`, command wall `369.14s`, exit `0`, zero retry and no
  hang. Individual call durations were: new `071→091` concurrent Create
  `68.17s`; `071` bookkeeping rollback/retry `66.21s`; unchanged `041`
  rollback/retry `66.14s`; original previous-version concurrent Create
  `65.15s`; upgrade-over-existing-data `64.86s`.
- `python -m mypy src tests`: no issues in 21 source files, wall `2.04s`, exit
  `0`, zero retry and no hang.
- Complete `python -m pytest -q --tb=short`: `86 passed, 1 warning in
  426.82s`, command wall `428.00s`, exit `0`, zero retry and no hang. The one
  warning is the existing Starlette/httpx deprecation. The suite exercised
  real Supabase Auth/PostgreSQL/PostgREST, forced RLS, FastAPI, Uvicorn and
  mobile Chromium.
- First equivalent-state blocker probe: setup wall `0.14s`, exit `0`; first
  migration wall `2.38s`, expected exit `1`; ordinary retry wall `2.36s`,
  expected exit `1`; durable-state assertion wall `0.10s`, exit `0`; cleanup
  reset wall `31.98s`, exit `0`. Zero harness retry or hang occurred.
- Exact previous-RPC blocker probe: setup and authenticated Change wall
  `0.39s`, exit `0`; first migration wall `2.52s`, expected exit `1`; ordinary
  retry wall `2.32s`, expected exit `1`; durable-state assertion wall `0.11s`,
  exit `0`; cleanup reset wall `31.11s`, exit `0`. Zero harness retry or hang
  occurred.
- The session-owned stack stopped with `--no-backup` in wall `13.69s`, exit
  `0`; absolute container inspection returned zero `supabase_*_diary`
  containers.

##### Personal Website

- `npm.cmd run typecheck`: wall `0.95s`, exit `0`, zero retry and no hang.
- Complete Chromium E2E:
  `npm.cmd run test:e2e -- --workers=4 --retries=0 --output=test-results/ticket08-formal-fd46d8a`
  used exactly four workers and zero retries, ran all 36 tests, and passed
  `36 passed in 18.7s`; command wall `30.39s`, exit `0`, no hang. The known
  post-summary mock-proxy `ECONNREFUSED 127.0.0.1:8000` diagnostic did not
  affect assertions or exit.
- `npm.cmd run build`: Vite `3.02s`, command wall `8.42s`, exit `0`, zero
  retry/no hang, with only existing informational non-module-script warnings.
  `npm.cmd run verify:build`: wall `0.42s`, exit `0`, zero retry/no hang.
- The sole session-created browser output directory resolved exactly to
  `E:\personal_website\test-results\ticket08-formal-fd46d8a`; only that
  absolute path was removed and verified absent. No pre-existing output
  directory or user file was touched.

#### Scope, modification and next step

- Both repositories were clean after validation and cleanup. No product,
  migration, test, CI or Personal Website file was modified. No secret,
  `.env` file or production configuration was added. This EOF append is the
  review session's only change.
- No finding was fixed or refactored. No Personal Website change, PR, Ticket
  09, Trash/delete, AI Draft, Queue, RAG or Agent work was started. Existing
  Note Garden and excluded code-smell findings remain untouched.
- Only this documentation record may be committed and pushed. Its exact-SHA
  Backend run and every returned job must reach `completed/success` before
  handoff.
- Because both review axes contain a High blocker, the only permitted next
  work is a new Ticket 08 blocker implementation/TDD session for the
  same-Entry `071→091` previous-version Change gap, followed later by another
  fresh complete fixed-range review. Ticket 09 remains blocked.

### 2026-08-14 - Maintenance-window architecture decision changes the formal migration boundary

#### Decision and historical finding disposition

- ADR 0016 now requires every production release containing a database schema
  migration to enter a Diary-only maintenance window. The release stops
  accepting all new Diary API reads and writes, drains in-flight requests,
  quiesces write-capable background workloads, verifies a backup, applies and
  validates migrations, verifies and deploys the selected version, and exits
  maintenance only after protected smoke checks pass. Other personal-site
  pages remain available.
- Every prior Ticket 08 implementation note, failed review, finding, probe and
  validation record above is preserved. In particular, the latest High
  same-Entry `071` to `091` finding remains an accurate finding under its
  reviewed assumption that the preceding-version Change RPC could write
  between migration files. No product code, migration, or test has been
  changed in this decision session, and this record does not claim that the
  latest finding was fixed in code.
- The formal production contract no longer permits that assumption: request
  draining and writer quiescence must complete before migrations begin, and
  neither the old nor new backend may write during migration execution. The
  same-Entry migration gap is therefore excluded by the maintenance deployment
  contract rather than repaired by a concurrent-writer implementation.
- ADR 0013 remains in force. Expand-contract sequencing and compatibility with
  the immediately previous application version are still required across the
  stable pre-migration and post-migration schema states so rollback remains
  possible. That compatibility does not authorize parallel writes during the
  migration window. Zero-downtime database migration is not an MVP requirement.

#### Ticket status and next review

- Ticket 08 remains `ready-for-agent` and **REVIEW-FAILED /
  CHANGES-REQUIRED**. It is not Passed. Ticket 09 has not started and remains
  blocked.
- The latest same-Entry evidence is not deleted or relabeled as a false
  positive. A fresh reviewer must assess it against ADR 0016's explicit
  no-concurrent-writes production boundary while retaining it as evidence of
  why the maintenance contract is required.
- Before review, Ticket 08 must receive complete validation with migration
  execution evaluated only after admission is closed, in-flight requests are
  drained, and write-capable workloads are quiescent. Implementing the Azure
  maintenance mechanism belongs to the later deployment tickets; Ticket 08
  must establish and honor the no-concurrent-writes boundary. The existing
  Ticket 03-08 behavior and migration, FastAPI, database, browser, type, and
  complete regression suites remain required; the boundary change is not a
  waiver for any non-concurrency invariant.
- The next code review must be a new independent complete fixed-range review
  from the original Ticket 08 bases through the documentation-decision
  endpoint in Diary and the unchanged integrated Ticket 08 endpoint in
  Personal Website. Both Standards and Spec axes must inspect the complete
  ranges. Ticket 08 may be marked Passed only if that full validation is
  present and the fresh review reports no blocking finding under the formal
  boundary.
