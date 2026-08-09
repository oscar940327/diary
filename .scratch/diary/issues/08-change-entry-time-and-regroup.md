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
