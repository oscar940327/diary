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

### 2026-08-02 - Fixed-range code review failed

- Review verdict: **FAILED**.
  - Standards: **FAIL** with one blocking finding and four non-blocking
    findings.
  - Spec: **FAIL** with two blocking findings and no non-blocking finding.
  - Ticket 06 cannot pass the review gate until the blocking findings are
    fixed and a new fixed-range review succeeds.
- Fixed review ranges:
  - Diary:
    `b47070d3ed3acb97909c9d59166ba8bed6415cfb...20b7d65181c38ac82b9cc1d4270c88cae4d9e3f1`.
  - Personal Website:
    `ab99cf8a101e2d0a294a6b1be740ed18b0207e47...e41ee0ad9e6b1cd3cec2e05eb079cfdea8b942dd`.

#### Preflight

- All four commit endpoints resolved as commits.
- Diary and Personal Website HEAD exactly matched their implementation
  endpoints.
- Both worktrees were clean before review.
- Both implementation commits were present on `origin/main`.
- Both three-dot diffs were non-empty: nine changed Diary files and five
  changed Personal Website files.
- Both exact-range `git diff --check` commands passed.
- GitHub Actions were green at the exact implementation endpoints:
  - Diary `Backend checks`, run
    [30709196703](https://github.com/oscar940327/diary/actions/runs/30709196703):
    completed successfully for
    `20b7d65181c38ac82b9cc1d4270c88cae4d9e3f1`.
  - Personal Website `Website checks and Pages`, run
    [30709120399](https://github.com/oscar940327/my-personal-website/actions/runs/30709120399):
    completed successfully for
    `e41ee0ad9e6b1cd3cec2e05eb079cfdea8b942dd`.
  - Personal Website `pages build and deployment`, run
    [30709120073](https://github.com/oscar940327/my-personal-website/actions/runs/30709120073):
    completed successfully for the same endpoint.

#### Standards - blocking finding

- **High severity; blocking.** Diary
  `supabase/migrations/20260801150000_edit_original_content_with_revisions.sql:8-59`
  grants `authenticated` callers direct column-level UPDATE access to
  `entries.current_revision_id` and `ai_processing.stale_at`; the new RLS
  policies verify ownership but do not constrain the mutation to the atomic
  edit RPC. An owner bearer token can use PostgREST to clear Revision 1's
  `stale_at` and point the Entry back to Revision 1 in separate transactions.
  The existing same-Entry foreign key accepts that state: no sequential
  Revision 3 or matching processing obligation is created, and Revision 2's
  obligation remains active. This breaks the revision/current-processing
  invariants documented in `CONTEXT.md:71,76-79`, ADR 0001:15,21, and Ticket
  06 criteria 10 and 15. A verifiable fix must deny direct caller PATCH of
  both columns while retaining caller identity and RLS inside a narrowly
  privileged edit path, or enforce equivalent deferred database invariants.
  Add an owner-token direct PostgREST regression proving both PATCH attempts
  fail while the FastAPI edit still succeeds atomically.

#### Standards - non-blocking findings

- **Medium severity; non-blocking judgement call; possible Divergent
  Change.** Personal Website `src/diary/EntryExperience.tsx:254` and
  `:532-649,895-1030` add revision editor, conflict, history-fetch, and two
  dialog responsibilities to the existing pagination, scroll, and capture
  component. The file is now 1,111 lines, weakening ADR 0005:19's goal of
  testable, focused modules. A verifiable cleanup is to extract the
  revision-aware editor and revision-history dialog/hooks, then rerun
  typecheck and E2E.
- **Low severity; non-blocking judgement call; Duplicated Code.** Personal
  Website `src/diary/EntryExperience.tsx:604-614` duplicates the
  `Ctrl/Cmd+Enter` submit handler at `:651-661`. A shared handler can remove
  the duplicate while the existing shortcut tests verify behavior.
- **Low severity; non-blocking judgement call; Duplicated Code.** Diary
  `src/diary_api/app.py:60-68,86-94` duplicates the nonblank Original Content
  validator in the capture and replacement request models. A shared
  validator or value type can preserve the two HTTP 422 contracts.
- **Low severity; non-blocking judgement call; Duplicated Code.** Personal
  Website `tests/e2e/entry-revisions.spec.ts:5-55` repeats the unsigned token,
  localStorage session, and health/owner route scaffold already used by other
  specs. A typed Playwright fixture/helper can reduce fixture drift while the
  same E2E suite proves behavior is unchanged.

#### Spec - blocking findings

- **High severity; blocking.** Diary
  `supabase/migrations/20260801150000_edit_original_content_with_revisions.sql:251-255`
  updates the stable `entries` row on every successful edit, replacing that
  tuple's `xmin`. The active History RPC filters only the current tuple using
  `pg_visible_in_snapshot(entries.xmin, v_snapshot)` at
  `supabase/migrations/20260801130000_locate_empty_history_anchors.sql:93-96`.
  If another client edits a snapshot-visible Entry before the current client
  reaches it, the following cursor request sees only a post-snapshot tuple and
  omits the Entry from that traversal. This violates Ticket 04 criterion 15,
  the Spec's bidirectional cursor contract at lines 200 and 241, and the
  requested no-regression check for continuous History snapshots. A
  verifiable fix must base membership on an immutable creation transaction
  identity rather than mutable `entries.xmin`, publish the repair through a
  backward-compatible ordered history RPC migration, and add a real
  PostgreSQL test that edits an unvisited Entry between initial and older and
  newer cursor requests and proves exact-once traversal.
- **High severity; blocking.** Diary
  `supabase/migrations/20260801150000_edit_original_content_with_revisions.sql:8-59`
  also fails the Spec axis because raw owner-token PATCH can bypass the Spec
  line 245 atomic edit contract, move the current pointer to historical
  content without a new revision, and independently alter stale processing.
  That is a broken restore-like path ahead of Ticket 07, whose criteria at
  `.scratch/diary/issues/07-restore-historical-revision.md:9-16` require a
  confirmed restore to copy historical content into a new sequential
  revision. The verifiable correction is the restricted mutation boundary
  and direct-PATCH denial coverage described in the Standards blocker.

#### Spec - non-blocking findings

- None.

#### Acceptance and scope confirmation

- Confirmed otherwise: edit requests carry complete replacement Original
  Content and expected current revision; the RPC locks the Entry and creates
  an immutable sequential revision, stales the old processing obligation,
  creates the new durable pending Draft and embedding obligation, and moves
  the pointer in one transaction.
- Previous revisions retain the immutable-update trigger and owner-only read
  policy. Entry detail, History, and Revision History select the current
  revision by default; revision history is newest-first and exposes sequence,
  `Asia/Taipei`-formatted creation time, and complete content.
- Stale edits return HTTP 409 with the complete current Entry representation.
  The UI preserves the attempted replacement and only changes the expected
  revision after the owner selects `Keep editing against Revision ...`; it
  does not retry automatically.
- Whitespace-only replacement is rejected before the store call, and the SQL
  function also rejects it before acquiring or changing an Entry row.
- FastAPI `require_owner`, caller-token PostgREST RPCs, the singleton owner
  registry, and forced owner-scoped RLS remain independent authorization
  layers, subject to the direct-mutation blocker above.
- Authentication, capture idempotency, Calendar navigation, microsecond/UUID
  ordering, bidirectional loading, and frontend scroll anchoring remained
  green. The snapshot-membership blocker above is the sole continuous-History
  regression found.
- The Calendar synthetic session change only extends that test session from
  one hour to 48 hours so its explicit 24-hour fake-clock advance does not
  expire authentication. Calendar assertions, timeouts, retry configuration,
  and worker count were unchanged; the full 19-test run used four workers.
- A high-confidence scan of both repositories and the built Website output
  found no Supabase secret, JWT, GitHub token, private key, database credential,
  or other candidate secret. Both repositories track only `.env.example` as
  environment-like files, and browser configuration remains limited to public
  values.
- No AI Draft generation, Queue worker, RAG, revision-restore UI/API, Entry
  Time edit, Trash, or other Ticket 07 behavior was intentionally implemented.
  The processing rows created here are only Ticket 06's required durable
  obligations.

#### Complete verification results

- Diary:
  - `python -m mypy src tests`: passed, 19 source files.
  - `python -m pytest -q`: passed, 58 tests, with one existing
    Starlette/httpx deprecation warning.
  - The first sandboxed pytest attempt produced 38 setup errors because
    Supabase CLI/Bun could not open its user file (`EPERM`); the identical
    authorized rerun above passed. This was an environment setup failure, not
    a product assertion failure.
  - `npm.cmd run supabase -- db reset`: passed; all nine ordered migrations
    applied from a clean local database.
  - `npm.cmd run supabase -- db lint --level warning`: passed with no schema
    findings.
  - Exact-range `git diff --check`: passed.
- Personal Website:
  - `npm.cmd run typecheck`: passed.
  - `npm.cmd run test:e2e`: passed, 19 Chromium tests using four workers.
  - `npm.cmd run build`: passed; Vite emitted only the existing classic-script
    notices while producing the complete site.
  - `npm.cmd run verify:build`: passed.
  - Exact-range `git diff --check`: passed.

This review did not change implementation code, did not update `CONTEXT.md`
because the review failed, did not begin Ticket 07, and did not push either
repository. The only authorized change from this session is this Diary
review-documentation record.
