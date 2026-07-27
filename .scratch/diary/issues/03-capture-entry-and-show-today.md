# 03 — Capture an Entry and show today's history

**What to build:** Let the authenticated owner capture free-form Original Content and immediately see the saved Entry in today's date group. Each submission creates an independent durable Entry and first Entry Revision before any AI activity can affect the result.

**Blocked by:** 02 — Enforce owner-only authentication.

**Status:** ready-for-agent

- [x] Each successful submit creates one stable Entry and one immutable first Entry Revision containing the complete Original Content.
- [x] Multiple submissions on the same day remain separate Entries.
- [x] Empty and whitespace-only submissions are rejected without creating partial records.
- [x] Desktop capture supports `Ctrl/Cmd + Enter`, and the same composer is usable at a mobile viewport.
- [x] Entry Time defaults to now in `Asia/Taipei` but can be intentionally supplied for a late or backdated Entry.
- [x] Merely browsing a past date never changes the default Entry Time of a new capture.
- [x] Repeating the same create idempotency key returns the original Entry instead of creating a duplicate.
- [x] Original Content and its durable processing obligation are committed before the API reports success or attempts external AI work.
- [x] Today's group displays the complete Original Content, Entry Time, immutable capture time, and current processing state.
- [x] Saving preserves the underlying browsing position and offers a direct action to view the new Entry.
- [x] Real-HTTP system tests cover multiple same-day Entries, backdating, blank rejection, UTC persistence, Taipei grouping, and idempotency.

## Comments

### 2026-07-27 - Implementation

- TDD API red: the first real owner request to `POST /entries` returned `404`.
  The database, atomic creation RPC, protected FastAPI endpoints, and date
  response were then implemented until the real Supabase/PostgREST/FastAPI
  test passed.
- TDD idempotency red: a repeated key initially returned `503` because an RPC
  output-column name made the duplicate lookup ambiguous. Qualifying the
  stored-table aliases made the retry return the original Entry with no extra
  Entry Revision or processing obligation.
- TDD browser red: the authenticated page initially had no Today history or
  composer. The owner can now capture from desktop or mobile, use
  `Ctrl/Cmd + Enter`, preserve the reading position, and directly view the
  saved Entry.
- TDD backdating red: an intentionally backdated Entry initially replaced the
  Today group. It now remains outside Today while the save confirmation can
  open a complete Saved Entry preview.
- TDD immutability red: a backend-role update could initially overwrite an
  Entry Revision. A database trigger now rejects every revision update, and
  the system test proves the complete Original Content remains unchanged.
- Capture atomically creates the stable Entry, immutable first Entry Revision,
  and durable `pending` Draft/embedding obligation. It does not publish work,
  call an LLM, create an AI Draft, or implement RAG.
- FastAPI owner authorization and PostgreSQL RLS remain independent controls.
  Owner and non-owner behavior is exercised through real Supabase Auth,
  PostgREST, HTTP, Uvicorn, and Chromium paths.
- Verification passed:
  - `python -m mypy src tests`: 16 source files passed.
  - `python -m pytest -q`: all 40 tests passed.
  - `npm.cmd run supabase -- db lint --level warning`: no schema errors.
  - Personal Website typecheck, all 9 Playwright tests, production build, and
    preserved-site build verification passed.
- Ticket 03 is implemented but is not review-passed. A fresh `$code-review`
  session must review the fixed base through the implementation commits.
  Ticket 04 has not started.

### 2026-07-28 - Code Review (Blocked)

- Fixed review ranges:
  - Diary:
    `8f3ff031379b477a058351b141acda7b9d0bf9fa...a64c43615dbc3c549a58557e1a972286d5629660`
  - Personal Website:
    `c6592f326a03fe4ec3a25e005cd71df6d1b5d219...3d808f8f5380e6a7d19965be46c336ce69e1b53d`
- Verdict: **Blocked**. Standards found one blocking violation and Spec
  found two blocking defects.
- Standards blocking finding: the FastAPI Entry data path does not preserve
  the required RLS defense in depth. `src/diary_api/entries.py:109-117` sends
  the backend Supabase secret as both `apikey` and Bearer authorization, while
  the Entry RPCs are granted only to `service_role` by
  `supabase/migrations/20260727133000_create_entries_and_revisions.sql:361-381`.
  PostgreSQL therefore sees a role that bypasses caller RLS, and
  `p_owner_id` is supplied by the same FastAPI path. The direct PostgREST RLS
  tests prove that browser callers are isolated, but they do not make RLS an
  independent control over FastAPI mutations if API authorization is
  misconfigured. This conflicts with the defense-in-depth decision in
  `CONTEXT.md` and ADR 0015.
- Spec blocking finding: saving a same-day Entry can lose the underlying
  visual reading anchor. Personal Website
  `src/diary/EntryExperience.tsx:151-159` prepends the new Entry above the
  existing list and then restores the old absolute `window.scrollY`. The
  inserted card changes the document offset of the content being read, so the
  same numeric scroll position no longer identifies the same content.
  `tests/e2e/diary-tracer.spec.ts:548-551` checks only that the numeric
  `scrollY` is unchanged and cannot detect this content shift.
- Spec blocking finding: Today becomes stale when an authenticated page stays
  open across midnight in `Asia/Taipei`.
  `src/diary/EntryExperience.tsx:93-114` loads the date group only when the
  access token changes. After midnight the heading still represents
  yesterday, and `src/diary/EntryExperience.tsx:151` compares the newly saved
  Entry against that stale date, so the new current-day Entry is not inserted
  into Today. This violates the requirement to immediately show a saved Entry
  in today's date group under the fixed owner timezone.
- The remaining Ticket 03 behavior reviewed cleanly: atomic Entry, first
  Entry Revision, and durable processing-obligation creation; complete
  Original Content; revision update immutability; idempotency; UTC
  persistence; Taipei grouping; blank rejection; desktop and mobile capture;
  backdating; and the direct saved-Entry action.
- Full verification completed:
  - `python -m mypy src tests`: passed, 16 source files.
  - `python -m pytest -q`: passed, 40 tests; one dependency deprecation
    warning.
  - `npm.cmd run supabase -- db lint --level warning`: passed with no schema
    errors.
  - Personal Website `npm.cmd run typecheck`: passed.
  - Personal Website `npm.cmd run test:e2e`: passed, 9 Chromium tests.
  - Personal Website `npm.cmd run build`: passed.
  - Personal Website `npm.cmd run verify:build`: passed.
  - `git diff --check` passed for both fixed ranges.
- No committed credential value was found. No Ticket 04 behavior, Queue
  publication or worker, AI Draft, RAG, or LLM implementation was found; the
  database change creates only the Ticket 03 durable processing obligation.
- Ticket 03 cannot be treated as complete until the blocking findings are
  resolved and a new fixed-range code review passes. Ticket 04 has not
  started.

### 2026-07-28 - Blocking Findings Resolved

- Final implementation SHAs:
  - Diary:
    `76cf123813a88ab56ea1f2ec52f8e7ea9ae35d1a`
  - Personal Website:
    `ceba0d921076e18a9545446d8a3cfda49e545452`
- TDD FastAPI/RLS red: the first caller-token tracer expected PostgreSQL to
  reject an owner-subject token without Entry privileges, but FastAPI returned
  `201` because the Entry RPC still used the backend secret as Bearer
  authorization. The final real-HTTP test was strengthened to use the actual
  authenticated owner token while a temporary restrictive Entry `INSERT` RLS
  policy denies the mutation; this proves the request passes the FastAPI owner
  gate and is independently stopped by PostgreSQL RLS.
- TDD FastAPI/RLS green: Entry RPCs now use the publishable `apikey` and the
  verified caller access token as Bearer authorization. RPC owner identity
  comes from `auth.uid()` and no longer accepts `p_owner_id`. The backend
  secret remains limited to singleton owner-registry reads. Focused RLS and
  fail-closed real-HTTP tests passed, including non-owner, malformed token,
  and missing-registry cases.
- TDD scroll-anchor red: after a same-day prepend, the Entry being read moved
  from approximately `209px` to `440px` relative to the viewport even though
  the old absolute `scrollY` assertion passed.
- TDD scroll-anchor green: capture now records a visible Entry element and its
  viewport-relative offset, then compensates for the prepend height after
  render. The Playwright test asserts the same Entry keeps that offset.
  `View new Entry` still actively scrolls to the saved Entry.
- TDD midnight red: with the controlled browser clock moved from
  `2026-07-27 23:59` to `2026-07-28 00:00` in Asia/Taipei, the authenticated
  page never requested the new Today group and continued to show
  `2026-07-27`.
- TDD midnight green: the authenticated experience schedules the next
  Asia/Taipei midnight independently of token changes, reloads the new Today
  group, captures with the new date, prepends the new Entry immediately, and
  clears both its timer and in-flight request on unmount. The controlled-clock
  Playwright scenario passed without real waiting.
- Final verification passed:
  - `python -m mypy src tests`: 16 source files passed.
  - `python -m pytest -q`: all 42 tests passed; one existing dependency
    deprecation warning.
  - `npm.cmd run supabase -- db lint --level warning`: no schema errors.
  - Personal Website `npm.cmd run typecheck`: passed.
  - Personal Website `npm.cmd run test:e2e`: all 10 Chromium tests passed.
  - Personal Website `npm.cmd run build`: passed.
  - Personal Website `npm.cmd run verify:build`: passed.
- Final fixed-range review:
  - Diary:
    `a64c43615dbc3c549a58557e1a972286d5629660...76cf123813a88ab56ea1f2ec52f8e7ea9ae35d1a`
  - Personal Website:
    `3d808f8f5380e6a7d19965be46c336ce69e1b53d...ceba0d921076e18a9545446d8a3cfda49e545452`
  - Spec: no findings.
  - Standards: no hard violations; one non-blocking judgment call noted that
    the midnight Playwright setup repeats adjacent authenticated test setup.
    It was left unchanged to avoid unrelated refactoring.
- No Ticket 04 behavior, Queue publisher or worker, AI Draft, RAG, or LLM work
  was added. No credential value or real diary content was committed.
  Ticket 04 has not started.

### 2026-07-28 - Final Verification Review (Passed)

- Fixed review range:
  - Personal Website:
    `ceba0d921076e18a9545446d8a3cfda49e545452...914407d090b54e2037810238e34c02cc9709df2c`
- Implementation SHA:
  - Personal Website:
    `914407d090b54e2037810238e34c02cc9709df2c`
- Verdict: **Passed**.
  - Standards: 0 findings.
  - Spec: 0 findings.
- The range changes only the midnight cleanup verification from
  `page.clock.runFor("24:00:00")` to
  `page.clock.fastForward("24:00:00")`. Playwright fires each due timer at
  most once during `fastForward`, so the check remains able to detect an
  uncleared Diary midnight timer without exhaustively running unrelated
  recurring timers.
- Verification passed:
  - Personal Website `npm.cmd run typecheck`: passed.
  - Focused midnight Playwright case with `--repeat-each=3`: 3 passed.
  - Personal Website `npm.cmd run test:e2e`: all 10 Chromium tests passed.
  - Personal Website `npm.cmd run build`: passed.
  - Personal Website `npm.cmd run verify:build`: passed.
  - `git diff --check` passed for the fixed range.
- The cleanup assertion remains intact: after sign-out and unmount, advancing
  through the next Taipei midnight produces no additional Today request.
- No production code, credential value, Ticket 04 behavior, Queue publisher
  or worker, AI Draft, RAG, or LLM work was added.
- Ticket 03 is review-passed and can be treated as complete. Ticket 04 has
  not started.
