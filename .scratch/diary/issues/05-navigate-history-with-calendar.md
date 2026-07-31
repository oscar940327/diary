# 05 — Navigate history with a calendar

**What to build:** Add a calendar as an alternative way to locate Entries. Selecting a day positions the owner inside the same continuous history, rather than opening an isolated daily document.

**Blocked by:** 04 — Browse continuous bidirectional history.

**Status:** ready-for-agent

- [x] The owner can switch between continuous history and calendar without losing the ability to capture a new Entry.
- [x] A requested month shows presence or counts derived only from active, non-trashed Entries.
- [x] Selecting a date opens continuous history with that date as the anchor.
- [x] After a calendar jump, scrolling upward reaches newer dates and scrolling downward reaches older dates.
- [x] Dates, month boundaries, today, and Entry counts use `Asia/Taipei` regardless of browser timezone.
- [x] A date with no Entry still produces a stable nearby history position and an understandable empty state.
- [x] Calendar retrieval does not return complete personal content unnecessarily.
- [x] System tests cover month boundaries, empty dates, multiple Entries per date, and fixed-timezone behavior.
- [x] Desktop and mobile browser tests verify the calendar-to-history journey.

## Comments

### 2026-08-01 - Implementation complete, awaiting review

- Fixed review bases:
  - Diary:
    `eab9aecc9bc30ebd53a4f0822cecb7ed30d80835`
  - Personal Website:
    `22326dea27c35fb69852b3a5c5b1cf731d9546aa`
- Implementation SHAs:
  - Diary:
    `644de5a6e45843368aea6bf845c9bacf2f4ae712`
  - Personal Website:
    `8fd2fa6835b16fcf66095862dcbc30d182d920dd`
- Preflight confirmed Ticket 04's new fixed-range review passed, both
  worktrees were clean, and the latest GitHub Actions for both repository
  HEADs completed successfully.
- TDD red evidence:
  - The first real-HTTP Calendar tracer received `404 Not Found` because
    `GET /entries/calendar` did not exist.
  - The first valid Chromium Calendar-to-History tracer loaded History, then
    timed out waiting for the absent `Calendar` navigation control.
- TDD green result:
  - An ordered caller-authorized Supabase RPC and protected FastAPI endpoint
    return only active Entry dates and counts for one `Asia/Taipei` month.
    The query reads Entry lifecycle and time metadata without joining Entry
    Revisions or returning Original Content.
  - The responsive Calendar uses `Asia/Taipei` for the displayed month and
    Today. Selecting any date returns to the existing continuous History with
    that date as its anchor, including a stable empty date group and nearby
    Entries. Existing older/newer cursors, snapshot semantics, microsecond
    ordering, scroll anchors, and global New Entry behavior remain intact.
- Complete Diary verification:
  - `python -m mypy src tests`: passed, 18 source files.
  - `python -m pytest -q`: 49 passed with one existing Starlette/httpx
    deprecation warning.
  - `npm.cmd run supabase -- db reset`: passed; all ordered migrations applied
    from a clean local database.
  - `npm.cmd run supabase -- db lint --level warning`: passed with no schema
    findings.
- Complete Personal Website verification:
  - `npm.cmd run typecheck`: passed.
  - `npm.cmd run test:e2e`: 15 Chromium tests passed, including desktop and
    mobile Calendar journeys in a non-Taipei browser timezone.
  - `npm.cmd run build`: passed.
  - `npm.cmd run verify:build`: passed.
- FastAPI owner authorization and PostgreSQL RLS continue as defense in depth;
  the system suite covers both the non-owner API denial and direct PostgREST
  visibility. Active/non-trashed counts, Taipei month boundaries, multiple
  Entries per date, empty anchors, and both history directions use the real
  Supabase, PostgREST, FastAPI HTTP, and Uvicorn seam.
- No new Supabase, GitHub, or Azure environment variable is required.
  Production must apply the new ordered migration through the existing
  migration process.
- Ticket 06, Entry editing, revision restore, AI Draft, RAG, and Agent behavior
  were not started.
- This is an implementation record, not a review verdict. Ticket 05 requires
  a fresh fixed-range code-review session before Ticket 06 may begin.

### 2026-08-01 - Fixed-range code review — FAILED

Reviewed the complete three-dot ranges, including the Diary documentation
commit rather than only the implementation commits:

- Diary:
  `eab9aecc9bc30ebd53a4f0822cecb7ed30d80835...8bc1f22008333a4e063e10eb93e4b7655347de5a`
  (`644de5a6e45843368aea6bf845c9bacf2f4ae712` implementation).
- Personal Website:
  `22326dea27c35fb69852b3a5c5b1cf731d9546aa...8fd2fa6835b16fcf66095862dcbc30d182d920dd`.

#### Preflight and CI

- Both endpoints resolved, each repository HEAD exactly matched its endpoint,
  and both worktrees were clean before review.
- Both three-dot diffs were non-empty and both `git diff --check` invocations
  passed.
- GitHub Actions at the exact endpoints were green:
  - Diary `Backend checks`, run `30660939932`: success.
  - Personal Website `Website checks and Pages`, run `30660448884`: success.
  - Personal Website `pages build and deployment`, run `30660446687`:
    success.

#### Standards — PASS

No blocking documented-standard violation was found. Authorization remains
layered through FastAPI `require_owner` and the caller-token, security-invoker
RPC/RLS path. The migration is ordered, additive, versioned, and compatible
with the expand-contract policy. Strict credential-signature scans found no
secret in either tracked repository or the built frontend; changed test tokens
are synthetic.

Non-blocking findings:

- **Low — non-blocking — Duplicated Code (judgement call):**
  `E:\personal_website\src\diary\CalendarView.tsx:15` duplicates the
  `Asia/Taipei` date-part projection in
  `E:\personal_website\src\diary\EntryExperience.tsx:31`. A shared owner-clock
  utility would prevent timezone behavior from drifting.
- **Low — non-blocking — Primitive Obsession (judgement call):**
  `E:\personal_website\src\diary\CalendarView.tsx:29`, `:36`, `:44`, and
  `:52` pass and parse unconstrained month/date strings. Small validated
  `CalendarMonth` and `OwnerDate` values would make invalid states harder to
  represent.
- **Low — non-blocking — Duplicated Code (judgement call):**
  `E:\personal_website\tests\e2e\calendar-navigation.spec.ts:40` and `:232`
  repeat owner-session plus health/auth route setup. A shared fixture would
  reduce authentication-test drift.

Standards result: **PASS** — 0 blocking and 3 non-blocking findings.

#### Spec — FAIL

- **High — blocking:** An empty selected date earlier than the first active
  Entry becomes a dead end. The initial history query returns no rows, and
  `src/diary_api/entries.py:164` converts that to both cursors being absent.
  `E:\personal_website\src\diary\EntryExperience.tsx:516` permits the jump and
  `:623` renders a synthetic empty group claiming nearby History continues,
  but no newer control exists. This violates the Ticket 05 empty-date and
  newer-after-jump criteria and spec User Stories 19, 23, and 24. The system
  test at `tests/system/test_calendar_navigation.py:173` only covers an empty
  anchor with an older row available to seed cursors.
- **High — blocking:** A calendar jump does not invalidate an in-flight
  adjacent-history request. `E:\personal_website\src\diary\EntryExperience.tsx:387`
  creates a request-local controller without aborting or version-checking it;
  `:516` starts the new anchor request without invalidating the old adjacent
  request. If the old request resolves last, `:406`-`:412` can merge Entries
  from the old snapshot and overwrite a new-anchor cursor. This regresses the
  Ticket 04 snapshot, ordering, cursor, and scroll-anchor guarantees and
  violates the Ticket 05 continuous-history behavior. The browser tests use
  serialized responses and do not exercise the race.
- **Medium — non-blocking:** Calendar Today can become stale across Taipei
  midnight. `E:\personal_website\src\diary\CalendarView.tsx:72` computes Today
  only on render, while the effect at `:84` refreshes only for access-token or
  month changes. A Calendar left open from a historical anchor can keep
  yesterday marked indefinitely, contrary to the fixed `Asia/Taipei` Today
  requirement.

| Ticket 05 acceptance criterion | Result | Review evidence |
| --- | --- | --- |
| Switch History/Calendar and retain New Entry | PASS | `EntryExperience.tsx:548`-`:570`, `:667` |
| Active, non-trashed monthly presence/counts | PASS | calendar migration lines 16-27 |
| Selected date anchors the same continuous History | FAIL | zero-row anchor is a dead end |
| Newer and older navigation after a jump | FAIL | zero-row edge and stale-request race |
| Taipei dates, month boundaries, Today, and counts | FAIL | server/month/count pass; Today can become stale |
| Stable nearby position and understandable empty state | FAIL | pre-history date has no reachable nearby Entry |
| Calendar omits complete personal content | PASS | metadata-only `entries` query; no revision join |
| Required system boundary coverage | FAIL | no zero-row, request-race, or Calendar-midnight case |
| Desktop and mobile calendar-to-history journey | PASS | both Playwright journeys pass |

FastAPI owner authorization, PostgreSQL RLS defense in depth, ordered
expand-compatible migration behavior, secret boundaries, and Ticket 05's scope
boundary all pass inspection. Ticket 06, editing, revision restore, AI Draft,
RAG, and Agent behavior were not started.

Spec result: **FAIL** — 2 blocking and 1 non-blocking findings.

#### Local verification

- Diary `python -m mypy src tests`: passed, 18 source files.
- Diary `python -m pytest -q`: 49 passed; one existing Starlette/httpx
  deprecation warning.
- Diary `npm.cmd run supabase -- db reset`: passed; all ordered migrations,
  including `20260801120000_list_calendar_month.sql`, applied from a clean
  database.
- Diary `npm.cmd run supabase -- db lint --level warning`: passed with no
  schema findings.
- Personal Website `npm.cmd run typecheck`: passed.
- Personal Website `npm.cmd run test:e2e`: 15 Chromium tests passed.
- Personal Website `npm.cmd run build`: passed; Vite emitted its existing
  non-module classic-script warnings.
- Personal Website `npm.cmd run verify:build`: passed.
- Preliminary sandboxed Supabase/pytest attempts could not write the Supabase
  CLI user-level telemetry state. They were environment-only failures; the
  authoritative reruns with the required host permission are the passing
  results above.

Overall verdict: **FAILED**. Standards passed, but Spec has blocking findings;
Ticket 06 must not start until they are fixed and Ticket 05 passes a new
fixed-range review.

### 2026-08-01 - Review findings fixed, awaiting new fixed-range review

- Review bases retained for the next fixed-range review:
  - Diary:
    `0b1aae946978b3f21c30c48123fe516a13fcf212`
  - Personal Website:
    `8fd2fa6835b16fcf66095862dcbc30d182d920dd`
- New implementation SHAs:
  - Diary:
    `bad9832ad2795e3037734d7330c51c31b190851b`
  - Personal Website:
    `4bebbb5301260a4f1fa1a4ea594d2904e5243c13`

#### TDD evidence

- Empty anchor before the first active Entry:
  - Red command:
    `python -m pytest -q tests/system/test_calendar_navigation.py::test_empty_calendar_date_before_first_entry_can_reach_newer_history`
  - Red failure: the selected empty anchor returned
    `newer_cursor == None`.
  - Green: the same real-HTTP test passed and followed the returned cursor to
    the first newer Entry while retaining the selected anchor and no older
    cursor.
- Calendar jump versus an in-flight adjacent request:
  - Red command:
    `npm.cmd run test:e2e -- --grep "calendar jump isolates"`
  - Red failure: Playwright received one visible
    `Stale Entry from the old snapshot.` after the new anchor had rendered.
  - Green: the focused Chromium test passed after adding request abort plus
    generation validation and clearing all old-anchor adjacent and scroll
    state.
- Calendar Today across an `Asia/Taipei` midnight:
  - Red command:
    `npm.cmd run test:e2e -- --grep "Calendar updates Taipei Today"`
  - Red failure: `May 2026` did not appear after the fake clock crossed the
    Taipei April/May boundary.
  - Green: the focused fake-clock test passed; Calendar follows the current
    Taipei month across midnight but preserves a month the owner deliberately
    browsed, and Today advances again when that month is reopened.
- Completely empty active History:
  - Red command:
    `npm.cmd run test:e2e -- --grep "no active History exists"`
  - Red failure: the true no-active-Entry explanation was absent.
  - Green: the focused browser test passed with no nearby-history claim and no
    adjacent controls.
- New RPC RLS sentinel:
  - Red command:
    `python -m pytest -q tests/system/test_calendar_navigation.py::test_calendar_excludes_trashed_entries_and_preserves_owner_defenses`
  - Red failure: a non-owner direct RPC call received one all-null metadata
    sentinel instead of an empty result.
  - Green: the focused real-PostgREST test passed after restricting sentinel
    output through the singleton owner registry and its RLS policy.

#### Review finding resolutions

- Added ordered migration
  `20260801130000_locate_empty_history_anchors.sql` with additive
  `list_diary_history_v3`. It returns bounded page data plus cursor metadata
  even for an owner zero-row initial page. The synthetic newer boundary uses
  the same transaction snapshot, PostgreSQL microsecond precision, and UUID
  tuple ordering as ordinary pages. Existing `list_diary_history` and
  `list_diary_history_v2` remain unchanged for expand-contract rollback
  compatibility.
- Empty dates now behave as one continuous History position: before-first has
  only a newer path, between-Entries has both paths, after-last starts with
  older History, and a database with no active Entry returns neither path.
  Responses remain page-limited and do not download lifetime History.
- Calendar jumps abort the active adjacent request, increment the History
  generation, and clear `pendingHistoryAnchor`, `adjacentLoad`,
  `adjacentError`, `userScrolledHistory`, old Entries, and both old cursors.
  Late transport completion is ignored when its generation is stale.
- `ownerClock.ts` is now the shared Taipei clock/date utility used by Calendar
  and Entry capture/History. Calendar schedules a Taipei-midnight Today
  refresh and only auto-follows the next month when the owner has not browsed
  elsewhere.

#### Complete verification

- Diary:
  - `python -m mypy src tests`: passed, 18 source files.
  - `python -m pytest -q`: 52 passed with one existing Starlette/httpx
    deprecation warning.
  - `npm.cmd run supabase -- db reset`: passed; all eight ordered migrations
    applied from a clean local database.
  - `npm.cmd run supabase -- db lint --level warning`: passed with no schema
    findings.
  - `git diff --check`: passed.
- Personal Website:
  - `npm.cmd run typecheck`: passed.
  - `npm.cmd run test:e2e`: 18 Chromium tests passed.
  - `npm.cmd run build`: passed with the existing classic-script warnings.
  - `npm.cmd run verify:build`: passed.
  - `git diff --check`: passed.
- Credential-signature scans found no private-key, Supabase secret-key,
  OpenRouter key, GitHub token, or JWT literal in either tracked repository or
  the built Personal Website output. Browser assets retain only public
  configuration boundaries.

#### Acceptance and scope recheck

- History/Calendar switching and global New Entry remain available on desktop
  and mobile.
- Calendar month counts remain active/non-trashed, metadata-only, Taipei-bound,
  and do not join Entry Revisions or return Original Content.
- Calendar selection remains an anchor into reverse-chronological continuous
  History, with newer above, older below, bounded adjacent loading, stable
  snapshot cursors, microsecond precision, UUID tie-break, and scroll-anchor
  preservation.
- FastAPI `require_owner`, caller-token RPC access, singleton-owner RLS, and
  security-invoker execution remain defense in depth. The new direct non-owner
  RPC regression returns no rows.
- The migration is ordered, versioned, additive, and leaves both prior History
  RPCs callable by the previous application revision.
- Ticket 06, editing, revision restore, AI Draft, RAG, and Agent behavior were
  not started. No push or code review was performed in this session.

### 2026-08-01 - Taipei-midnight browser regression made deterministic

#### Review finding and scope

- The blocking finding was nondeterminism in Personal Website
  `tests/e2e/calendar-navigation.spec.ts`, not a demonstrated Calendar
  production defect. The test installed a running fake clock at
  `2026-04-30T23:59:59+08:00`; authentication, routing, page load, and Calendar
  navigation could consume the last second before the initial April checks.
- The fix is test-only. It pauses the installed clock at the same April 30
  instant before session and page setup. Time then changes only through the
  test's explicit `runFor(2_000)` and `fastForward(24 hours)` calls.
- No timeout, retry, serial mode, worker reduction, skipped assertion, or
  production Calendar change was introduced. Ticket 06, editing, revision
  restore, AI Draft, RAG, and Agent work were not started.

#### TDD red and green evidence

- Red command against unchanged Personal Website HEAD
  `4bebbb5301260a4f1fa1a4ea594d2904e5243c13`:
  `npm.cmd run test:e2e -- --grep "Calendar updates Taipei Today" --repeat-each=20 --workers=4`.
- Red result: 12 passed and 8 failed. Every failure timed out on the initial
  `April 2026` assertion, proving real setup time could advance the fake clock
  into May before the pre-midnight state was observed.
- Green command after the clock pause used the identical repeated/concurrent
  invocation. Result: 20 passed in 12.8 seconds.
- The retained assertions prove April 2026 and April 30 Today before the
  explicit advance; May 2026, May 1 Today, and a `2026-05` Calendar load after
  crossing midnight; no month takeover while the owner browses April across
  the next midnight; and May 2 Today after returning to May.

#### Verification

- Personal Website:
  - Focused midnight regression, 20 repeats with 4 workers: 20 passed.
  - `npm.cmd run typecheck`: passed.
  - `npm.cmd run test:e2e`: 18 Chromium tests passed.
  - `npm.cmd run build`: passed with the existing classic-script warnings.
  - `npm.cmd run verify:build`: passed.
  - `git diff --check`: passed.
- Diary:
  - `python -m mypy src tests`: passed, 18 source files.
  - `python -m pytest -q`: authoritative host-permitted rerun passed 52 tests
    with the existing Starlette/httpx warning. The first sandboxed attempt had
    20 passes and 32 Supabase setup errors from one user-state `EPERM`; it was
    an environment-only failure.
  - `npm.cmd run supabase -- db reset`: passed after starting the stopped local
    stack; all eight ordered migrations applied from a clean database. The
    first attempt only reported that Supabase was not running.
  - `npm.cmd run supabase -- db lint --level warning`: passed with no findings.
  - `git diff --check`: passed.

#### Fixed-range review handoff

- Review bases:
  - Diary: `891636e3c680a0bb7f032e64a0f779210302ff44`.
  - Personal Website: `4bebbb5301260a4f1fa1a4ea594d2904e5243c13`.
- New implementation/pin endpoints:
  - Diary CI pin: `59e3ae6282c5e6fc4e0abaa65f8a6bc7b28a7194`.
  - Personal Website test fix:
    `ab99cf8a101e2d0a294a6b1be740ed18b0207e47`.
- The complete Diary review endpoint is the documentation commit containing
  this record; its immutable SHA is the final local Diary HEAD reported in the
  session handoff. The Personal Website review endpoint is
  `ab99cf8a101e2d0a294a6b1be740ed18b0207e47`.
- Neither repository was pushed. Ticket 06 remains unstarted.
