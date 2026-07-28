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
