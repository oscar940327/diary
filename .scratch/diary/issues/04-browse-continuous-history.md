# 04 — Browse continuous bidirectional history

**What to build:** Turn the initial today view into the primary continuous Diary history. The owner can read complete Entries grouped by date, load older or newer groups incrementally, and retain visual position while moving through a long history.

**Blocked by:** 03 — Capture an Entry and show today's history.

**Status:** ready-for-agent

- [x] History opens at today and orders newer Entry Times above older Entry Times.
- [x] Entries are grouped by `Asia/Taipei` calendar date and display complete current Original Content.
- [x] Loading downward retrieves older groups without downloading the complete lifetime history.
- [x] Starting from a past anchor and loading upward retrieves newer groups through a separate cursor.
- [x] Cursor ordering remains stable when Entries share the same Entry Time by including stable Entry identity.
- [x] Prepending or appending groups preserves the reader's visual scroll anchor without a disruptive jump.
- [x] History cursors do not duplicate or omit Entries when data changes between requests.
- [x] The composer remains accessible without replacing the current history position.
- [x] Real-HTTP tests cover both cursor directions, equal timestamps, and Taipei date boundaries.
- [x] Browser tests verify complete content, incremental loading, and scroll anchoring.

## Comments

### 2026-07-28 - Implementation complete, awaiting review

- Fixed implementation bases:
  - Diary:
    `62215e1fa1d96331fa4c6d982311dd32ee05e71c`
  - Personal Website:
    `914407d090b54e2037810238e34c02cc9709df2c`
- Personal Website implementation:
  `578785059949681a03897b49d8f88920f0db1e5e`
- TDD red evidence:
  - The first real-HTTP tracer failed with `404` because
    `GET /entries/history` did not exist.
  - The first browser tracer could not find the History experience because
    the UI exposed only the Ticket 03 Today view.
  - A boundary-scroll tracer showed that older content was not loaded until
    user-scroll intent was connected to the boundary observer.
  - A Today-anchor tracer showed that an empty Today group disappeared when
    the first returned Entry belonged to yesterday.
- TDD green result:
  - A caller-authorized Supabase RPC and FastAPI endpoint now provide bounded,
    bidirectional snapshot/keyset pages ordered by `(entry_at, id)`.
  - The frontend merges and groups pages without downloading all history,
    restores the same visible Entry after prepend or append, keeps New Entry
    globally available, and retains an empty Today anchor when appropriate.
- Complete Diary verification:
  - `python -m mypy src tests`: passed (17 source files).
  - `python -m pytest -q`: 45 passed, with one existing dependency
    deprecation warning.
  - `npm.cmd run supabase -- db lint --level warning`: passed with no schema
    findings.
- Complete Personal Website verification:
  - `npm.cmd run typecheck`: passed.
  - `npm.cmd run test:e2e`: 12 Chromium tests passed.
  - `npm.cmd run build`: passed.
  - `npm.cmd run verify:build`: passed.
- Existing owner authentication, RLS, capture idempotency, and revision
  immutability remain covered by the complete suites. The real Supabase,
  PostgREST, FastAPI HTTP, Uvicorn, and Chromium system path remains intact.
- No new environment variable is required. Production must apply the new
  ordered Supabase migration through the existing migration process.
- This is an implementation record, not a review verdict. Ticket 04 still
  requires a fresh fixed-range code-review session and green GitHub Actions.
- Ticket 05, Calendar, editing, AI Draft, RAG, and Agent behavior were not
  implemented.

### 2026-07-28 - Fixed-range code review failed

- Review verdict: **FAILED**.
  - Standards: **PASS** with no hard or blocking violation and two
    non-blocking judgement findings.
  - Spec: **FAIL** with two blocking findings.
- Fixed review ranges:
  - Diary:
    `62215e1fa1d96331fa4c6d982311dd32ee05e71c...82643322472ef392290c21e0028428cce5db37fa`
  - Personal Website:
    `914407d090b54e2037810238e34c02cc9709df2c...578785059949681a03897b49d8f88920f0db1e5e`
- Reviewed implementation SHAs:
  - Diary: `82643322472ef392290c21e0028428cce5db37fa`
  - Personal Website: `578785059949681a03897b49d8f88920f0db1e5e`

#### Spec finding

- **Blocking - frontend loses sub-millisecond Entry Time ordering.**
  Personal Website `src/diary/EntryExperience.tsx` lines 91-96 sorts
  `entry_at` with `Date.parse()`. JavaScript `Date` keeps only millisecond
  precision, while PostgreSQL `timestamptz` and the FastAPI response preserve
  microseconds. Two Entries at, for example, `.000100Z` and `.000900Z` are
  therefore treated as having the same Entry Time and are incorrectly ordered
  by UUID. A larger UUID on the older Entry places it above the newer Entry.
  This violates the acceptance criteria that newer Entry Times appear above
  older Entry Times and that stable Entry identity is only the tie-breaker when
  Entry Times are actually equal. A direct Node reproduction produced equal
  `Date.parse()` values for those timestamps and sorted the older, larger-UUID
  Entry first. The current equal-timestamp browser coverage does not exercise
  distinct microseconds within one millisecond.
- **Blocking - the timestamp watermark is not a stable PostgreSQL snapshot.**
  `20260728123000_list_continuous_history.sql` records
  `clock_timestamp()` and later selects `entries.created_at <= v_snapshot_at`.
  The capture RPC independently records `created_at` with
  `clock_timestamp()`. Under PostgreSQL READ COMMITTED semantics, a capture
  transaction can record `created_at = T0` but remain uncommitted while the
  first history statement takes its visibility snapshot and watermark at
  `T1 > T0`. The first page cannot see that Entry. If capture commits before
  the next cursor request, the new statement can see it and the timestamp
  predicate admits it because `T0 <= T1`. Depending on which side of the
  keyset boundary its `(entry_at, id)` occupies, the Entry either appears
  midway through the supposed snapshot or is permanently omitted from that
  traversal. The existing test covers a capture that starts and commits after
  the first page; it does not cover an overlapping transaction. This violates
  the acceptance criterion that request-to-request data changes must not
  duplicate or omit Entries.

#### Standards findings

- Non-blocking judgement call, **Speculative Generality**:
  Personal Website `src/diary/api.ts` lines 152-170 retains the exported
  `loadTodayEntries` wrapper after the UI moved to the history endpoint and no
  call site remains. The backend `/entries/today` compatibility contract is
  still required for Ticket 03; only the unused frontend wrapper is in
  question.
- Non-blocking judgement call, **Duplicated Code**:
  Personal Website `tests/e2e/continuous-history.spec.ts` repeats the synthetic
  Supabase session plus health and owner-route setup across its two tests.
  A test helper could reduce future auth-fixture drift.
- No documented-standard breach was found. FastAPI still requires the owner,
  the history RPC uses the caller JWT with `security invoker`, `auth.uid()`,
  RLS, and `authenticated`-only execution, and the CI workflow pins the exact
  reviewed frontend SHA.

#### Acceptance and scope verification

- Confirmed working and covered: separate incremental older/newer cursors;
  backend `(entry_at, id)` keyset ordering for exactly equal timestamps;
  exclusion of a sequential capture that starts after the first request; fixed
  `Asia/Taipei` grouping and boundaries; complete current Original Content;
  prepend/append visual-anchor restoration; composer/capture
  reading-position restoration; FastAPI plus PostgreSQL RLS defense in depth;
  and the real Supabase, PostgREST, FastAPI HTTP, Uvicorn, and Chromium seam.
- Ticket 03 authentication, capture, idempotency, Today compatibility,
  backdated capture, RLS, and immutable revision behavior remained green in
  the complete suites.
- Ticket 05, Calendar, editing, AI Draft generation, RAG, and Agent behavior
  were not implemented.
- No candidate committed secret was found in either reviewed tree. The only
  tracked environment files are `.env.example`; frontend configuration remains
  limited to public API, Supabase URL, and publishable-key values.
- Ticket 04 cannot satisfy all acceptance criteria until both blocking defects
  are fixed and covered by regression tests.

#### Verification results

- Both endpoints resolved, each three-dot diff was non-empty, and both
  `git diff --check` commands passed.
- Diary:
  - `python -m mypy src tests`: passed, 17 source files.
  - `python -m pytest -q`: 45 passed with one existing dependency deprecation
    warning.
  - `npm.cmd run supabase -- db lint --level warning`: passed with no schema
    findings.
- Personal Website:
  - `npm.cmd run typecheck`: passed.
  - `npm.cmd run test:e2e`: 12 Chromium tests passed.
  - `npm.cmd run build`: passed.
  - `npm.cmd run verify:build`: passed.
- The initial sandbox-limited Supabase CLI invocations were inconclusive only
  because the CLI could not write its user telemetry file; the authorized
  reruns above completed successfully.
- GitHub Actions were green for both reviewed implementation SHAs:
  - Diary `Backend checks`, run
    [30375290710](https://github.com/oscar940327/diary/actions/runs/30375290710):
    completed successfully.
  - Personal Website `Website checks and Pages`, run
    [30375292891](https://github.com/oscar940327/my-personal-website/actions/runs/30375292891):
    completed successfully.
  - Personal Website `pages build and deployment`, run
    [30375291796](https://github.com/oscar940327/my-personal-website/actions/runs/30375291796):
    completed successfully.

The review record now needs a documentation-only commit. It must not mark the
ticket passed or begin Ticket 05. The blocking findings require implementation
fixes and a new fixed-range review before Ticket 05 is ready.

### 2026-07-29 - Blocking review fixes implemented, awaiting new review

- New implementation SHAs:
  - Diary:
    `fa774739a482254c1f7d1b0d9b655dd2de358776`
  - Personal Website:
    `22326dea27c35fb69852b3a5c5b1cf731d9546aa`
- TDD red evidence:
  - The new Chromium regression used Entry Times
    `2026-07-29T04:00:00.000100Z` and
    `2026-07-29T04:00:00.000900Z` with the older Entry assigned the larger
    `ffffffff-...` UUID. It failed because `Date.parse()` collapsed both
    values to one millisecond and displayed the older Entry first.
  - The new real-PostgreSQL regression held an owner capture RPC transaction
    open after creating its Entry, requested the first history page through
    Uvicorn, FastAPI, and PostgREST, committed the capture, and then followed
    the older cursor. It failed because the newly committed Entry appeared in
    the older page even though it was not visible to the first statement.
- TDD green result:
  - Personal Website now compares timezone-aware ISO Entry Times as integer
    microseconds. Stable Entry identity is consulted only when the complete
    instants are equal.
  - The new additive `list_diary_history_v2` RPC captures
    `pg_current_snapshot()` on the initial statement and carries its
    transaction-visibility token through opaque HTTP cursors. Later pages use
    `pg_visible_in_snapshot()` instead of a `clock_timestamp()` /
    `created_at` watermark. The previous RPC remains available for
    expand-contract compatibility.
  - The overlap regression verifies separate incremental older and newer
    cursors, the complete original visible Entry set, and no duplicate,
    omitted, or mid-snapshot Entry.
- Complete Diary verification:
  - `python -m mypy src tests`: passed, 17 source files.
  - `python -m pytest -q`: 46 passed with one existing dependency
    deprecation warning.
  - `npm.cmd run supabase -- db reset`: passed; every ordered migration,
    including the v2 snapshot RPC, applied from a clean local database.
  - `npm.cmd run supabase -- db lint --level warning`: passed with no schema
    findings.
- Complete Personal Website verification:
  - `npm.cmd run typecheck`: passed.
  - `npm.cmd run test:e2e`: 13 Chromium tests passed.
  - `npm.cmd run build`: passed.
  - `npm.cmd run verify:build`: passed.
- Ticket 03 owner authentication, capture, idempotency, Today compatibility,
  backdated capture, RLS, and immutable revision coverage remained green.
  Asia/Taipei grouping, complete Original Content, visual scroll anchors,
  composer reading position, owner-only FastAPI authorization, and PostgreSQL
  RLS defense in depth also remained green.
- The real Supabase, PostgREST, FastAPI HTTP, Uvicorn, and Chromium seams are
  retained. Diary CI now pins the new Personal Website implementation SHA.
- Secret checks found no credential-like values in either implementation
  diff. Both repositories track only `.env.example`; frontend configuration
  remains limited to the public API URL, Supabase URL, and publishable key.
- Ticket 05, Calendar, editing, AI Draft generation, RAG, and Agent behavior
  were not implemented. The two non-blocking review cleanup findings were not
  changed.
- Complete fixed ranges for the required new code-review session:
  - Diary:
    `62215e1fa1d96331fa4c6d982311dd32ee05e71c...fa774739a482254c1f7d1b0d9b655dd2de358776`
  - Personal Website:
    `914407d090b54e2037810238e34c02cc9709df2c...22326dea27c35fb69852b3a5c5b1cf731d9546aa`
- GitHub Actions were green for the pushed fixes:
  - Diary `Backend checks`, run
    [30381806444](https://github.com/oscar940327/diary/actions/runs/30381806444):
    completed successfully.
  - Personal Website `Website checks and Pages`, run
    [30381667326](https://github.com/oscar940327/my-personal-website/actions/runs/30381667326):
    completed successfully.
  - Personal Website `pages build and deployment`, run
    [30381665752](https://github.com/oscar940327/my-personal-website/actions/runs/30381665752):
    completed successfully.
- This is an implementation and verification record, not a Passed verdict.
  Ticket 04 still requires a fresh fixed-range code-review session.

### 2026-07-29 - New fixed-range code review passed

- Review verdict: **PASSED**.
  - Standards: **PASS** with no blocking finding, one non-blocking
    documented-standard finding, and two non-blocking judgement findings.
  - Spec: **PASS** with no finding.
  - Both review axes are free of blocking findings, so Ticket 04 passes the
    required new-session code review.
- Fixed review ranges:
  - Diary:
    `62215e1fa1d96331fa4c6d982311dd32ee05e71c...fa774739a482254c1f7d1b0d9b655dd2de358776`
  - Personal Website:
    `914407d090b54e2037810238e34c02cc9709df2c...22326dea27c35fb69852b3a5c5b1cf731d9546aa`
- Both endpoints resolved, both three-dot diffs were non-empty, and both
  `git diff --check` commands passed. The Diary review ran from later
  documentation-only HEAD `c52c043fa95fb0526325d4586c6f0acfe6f43483`;
  every production and test path was identical to fixed endpoint
  `fa774739a482254c1f7d1b0d9b655dd2de358776`. Personal Website HEAD was the
  fixed endpoint.

#### Standards findings

- **Low, non-blocking - documented-standard breach:** Diary
  `CONTEXT.md:343-347` still says CI pins Personal Website `5787850...` and
  awaits the first review, while `.github/workflows/ci.yml:22-27` pins the
  repaired `22326de...` endpoint and Ticket Comments record the prior failed
  review. This leaves required domain documentation stale relative to
  `docs/agents/development-workflow.md:11` and
  `docs/agents/domain.md:3,18`. The review records the discrepancy but does
  not edit that file in this review session.
- **Low, non-blocking judgement - Speculative Generality:** Personal Website
  `src/diary/api.ts:152-170` retains the exported `loadTodayEntries` wrapper
  after the UI moved to history and no endpoint-tree consumer remains. The
  backend `/entries/today` compatibility contract itself remains required for
  Ticket 03.
- **Low, non-blocking judgement - Duplicated Code:** Personal Website
  `tests/e2e/continuous-history.spec.ts:37-73,266-302,381-417` repeats the
  synthetic Supabase session and health/owner route setup. A shared test
  helper could reduce future fixture drift.
- No other documented-standard violation or baseline smell warranted a
  finding. Ordered v1/v2 migration duplication is required by the
  expand-contract decision in ADR 0013 and was not reported as a smell.

#### Spec findings and blocking-fix revalidation

- **No Spec findings.** Ticket 04 has no missing or partial requirement,
  unrequested feature, or implementation behavior that appears incorrect in
  the fixed ranges.
- The prior timestamp blocker is resolved:
  - Personal Website `src/diary/EntryExperience.tsx:91-140` parses
    timezone-aware ISO Entry Times to integer microseconds, compares the full
    instant first, and consults stable Entry identity only for a true equal
    instant.
  - `tests/e2e/continuous-history.spec.ts:377-454` uses
    `.000100Z` for the older `ffffffff-...` UUID and `.000900Z` for the newer
    `00000000-...` UUID. Millisecond truncation plus a premature UUID
    tie-break would fail this Chromium regression.
- The prior snapshot blocker is resolved:
  - `supabase/migrations/20260729120000_use_transaction_snapshot_for_history.sql:42-67,69-93`
    captures `pg_current_snapshot()` for the first statement and filters
    later requests with `pg_visible_in_snapshot()`.
  - `src/diary_api/app.py:321-342` carries the same transaction-visibility
    token in both opaque cursors.
  - `tests/system/test_continuous_history.py:341-447` holds an owner capture
    transaction uncommitted, requests the first history page through real
    Uvicorn, FastAPI, PostgREST, and PostgreSQL, commits the capture, then
    independently follows older and newer cursors. It proves exact equality
    with the original visible Entry set, no duplicates, no omissions, and no
    mid-snapshot capture; a fresh traversal then proves the committed Entry is
    visible.
- Additional acceptance coverage was confirmed:
  - independent bounded older/newer pagination and equal-Entry-Time identity:
    `tests/system/test_continuous_history.py:180-338`;
  - complete Original Content, `Asia/Taipei` midnight boundaries, FastAPI
    non-owner denial, and direct PostgREST/RLS denial:
    `tests/system/test_continuous_history.py:452-540`;
  - complete content, separate cursor requests, and prepend/append visual
    scroll anchoring:
    `tests/e2e/continuous-history.spec.ts:33-260`;
  - user-scroll-triggered incremental loading:
    `tests/e2e/continuous-history.spec.ts:262-375`;
  - composer reading-position restoration and Ticket 03 capture behavior:
    `tests/e2e/diary-tracer.spec.ts:427-579`;
  - real Supabase Auth/PostgreSQL/PostgREST, FastAPI HTTP/Uvicorn, Vite, and
    mobile Chromium behavior remained covered by the complete Diary suite.
- Ticket 03 owner authentication, capture, idempotency, Today compatibility,
  backdated capture, RLS, immutable revision, and mobile Magic Link behavior
  remained green.
- Ticket 05, Calendar, editing, AI Draft generation, RAG, and Agent behavior
  were not implemented.
- Fixed-endpoint secret scans found only tracked `.env.example` files,
  documentation references, synthetic test tokens, and intentional public
  publishable-key configuration. No candidate committed credential or
  frontend secret was found, and the built-site verification passed.

#### Complete verification results

- Diary:
  - `python -m mypy src tests`: passed, 17 source files.
  - `python -m pytest -q`: passed, 46 tests, with one existing
    Starlette/httpx deprecation warning.
  - `npm.cmd run supabase -- db lint --level warning`: passed with no schema
    errors or findings.
  - The first sandboxed pytest and lint attempts could not write the Supabase
    CLI user telemetry file. The first authorized lint retry then found the
    local stack stopped by pytest. After explicitly starting the local
    Supabase/Docker stack, the authorized full pytest and lint reruns above
    completed successfully; these were environment-only setup failures, not
    product-test failures.
- Personal Website:
  - `npm.cmd run typecheck`: passed.
  - `npm.cmd run test:e2e`: passed, 13 Chromium tests.
  - `npm.cmd run build`: passed. Vite emitted its existing notices for legacy
    non-module static scripts while producing the complete site.
  - `npm.cmd run verify:build`: passed and verified the GitHub Pages output.

Ticket 04 may proceed past the code-review gate. This review did not modify
production code and did not begin Ticket 05.
