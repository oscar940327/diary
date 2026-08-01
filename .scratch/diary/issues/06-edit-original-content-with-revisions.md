# 06 — Edit Original Content with immutable revisions

**What to build:** Let the owner correct or expand Original Content without overwriting history. Editing creates a new current Entry Revision, prior revisions remain inspectable, and a stale edit from another device cannot silently replace newer work.

**Blocked by:** 03 — Capture an Entry and show today's history; 04 — Browse continuous bidirectional history.

**Status:** ready-for-agent

- [x] Editing submits complete replacement Original Content together with the revision the client believed was current.
- [x] A successful edit creates a new immutable sequential Entry Revision and changes the Entry's current revision reference atomically.
- [x] The previous revision remains unchanged and available only to the authenticated owner.
- [x] History and Entry detail display the newest current revision by default.
- [x] Revision history exposes sequence, creation time, and complete content in a usable owner interface.
- [x] A stale expected revision receives a conflict response containing enough current state for the owner to retry deliberately.
- [x] Editing Original Content marks prior-revision derived processing stale and creates a durable obligation for the new current revision.
- [x] Empty replacement content is rejected without changing the current revision.
- [x] System tests cover sequential edits, stale concurrent edits from two clients, immutable prior text, and authorization.

## Comments

### 2026-08-01 - Implementation complete, awaiting review

- Fixed review bases:
  - Diary:
    `b47070d3ed3acb97909c9d59166ba8bed6415cfb`.
  - Personal Website:
    `ab99cf8a101e2d0a294a6b1be740ed18b0207e47`.
- Personal Website implementation SHA:
  `e41ee0ad9e6b1cd3cec2e05eb079cfdea8b942dd`.
- The Diary implementation endpoint is the commit containing this record.

#### TDD evidence

- Backend red:
  - Command:
    `python -m pytest -q tests/system/test_entry_revisions.py::test_sequential_edits_create_immutable_revision_history`.
  - The first assertion reached the real FastAPI/Uvicorn seam and received
    `404 Not Found` from the absent
    `PUT /entries/{entry_id}/original-content` endpoint.
- Backend green:
  - The same focused tracer passed after the ordered migration, caller-token
    PostgREST RPC, Entry detail, and revision-history contracts were added.
  - The completed Ticket 06 system file covers sequential replacements,
    current History/detail, immutable history, two-client stale conflict,
    blank rejection, stale/new derived obligations, non-owner denial, direct
    RLS visibility, and transactional RLS rollback.
- Chromium red:
  - Command:
    `python -m pytest -q tests/system/test_owner_browser_authentication.py::test_owner_completes_magic_link_on_mobile_and_reaches_diary`.
  - After a real Magic Link sign-in and capture, Chromium timed out waiting
    for the absent `Entry actions` UI.
- Chromium green:
  - The identical real Supabase/PostgREST/FastAPI/Uvicorn/Chromium journey
    passed after adding the complete-replacement editor and revision-history
    interface.
  - A focused browser contract test passed for a `409` stale edit: it retains
    the owner's replacement, shows the server's complete current content,
    and sends the current revision only after deliberate owner confirmation.

#### Implementation

- Ordered additive migration
  `20260801150000_edit_original_content_with_revisions.sql` adds an explicit
  `stale_at` marker to durable processing obligations and owner-authorized,
  security-invoker RPCs for current Entry detail, complete revision history,
  and atomic revision-aware editing.
- An edit locks the stable Entry, compares the expected current revision,
  marks the superseded revision's processing obligation stale, creates one
  sequential immutable Entry Revision and one new pending Draft/embedding
  obligation, and moves the current pointer in the same transaction.
- A stale precondition returns HTTP `409` with the full current Entry state.
  The UI never retries implicitly; it preserves the attempted replacement and
  requires the owner to choose the displayed current revision before retrying.
- Continuous History and Entry detail continue to join through
  `current_revision_id`; existing reverse chronology, snapshot cursors,
  microsecond/UUID ordering, bidirectional loading, and scroll-anchor code is
  unchanged.
- FastAPI `require_owner`, caller-token PostgREST access, singleton-owner RLS,
  column grants, and owner-scoped policies retain defense in depth. Previous
  revisions remain readable only to the owner and retain the immutable-update
  trigger.
- No AI Draft, Queue worker, RAG, revision restore, Entry Time edit, Trash, or
  later-ticket behavior was implemented.

#### Complete verification

- Diary:
  - `python -m mypy src tests`: passed, 19 source files.
  - `python -m pytest -q`: 58 passed with one existing Starlette/httpx
    deprecation warning.
  - `npm.cmd run supabase -- db reset`: passed; all nine ordered migrations
    applied from a clean local database.
  - `npm.cmd run supabase -- db lint --level warning`: passed with no schema
    findings.
  - `git diff --check`: passed.
- Personal Website:
  - `npm.cmd run typecheck`: passed.
  - `npm.cmd run test:e2e`: 19 Chromium tests passed.
  - The existing Calendar Taipei-midnight test initially exposed that its
    synthetic one-hour auth session expired during its explicit 24-hour fake
    clock advance. Its test-only session now lasts 48 hours; the unchanged
    Calendar assertions passed 20 repeats with 4 workers and the full suite.
  - `npm.cmd run build`: passed with the existing classic-script notices.
  - `npm.cmd run verify:build`: passed.
  - `git diff --check`: passed.

#### Environment and scope

- No new Supabase, GitHub, or Azure environment variable is required.
  Production must apply the new ordered migration through the existing
  backup and migration process.
- Credential-signature scans found no secret in tracked source. Browser code
  continues to use only the existing public Supabase configuration.
- Ticket 07 has not started. No push or code review was performed in this
  implementation session.
