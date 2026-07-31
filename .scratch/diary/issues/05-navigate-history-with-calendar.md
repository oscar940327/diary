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
