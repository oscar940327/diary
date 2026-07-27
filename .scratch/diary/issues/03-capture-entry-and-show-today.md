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
