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

### 2026-08-02 - Blocking review fixes implemented, awaiting new review

- New Diary implementation SHA:
  `49667cb0569a93a0bd2d7fa2c5a4f0a59a327d3e`.
- Personal Website was not modified. Its implementation endpoint remains
  `e41ee0ad9e6b1cd3cec2e05eb079cfdea8b942dd`.

#### Preflight

- Both worktrees were clean on `main` before implementation.
- After fresh fetches, Diary `HEAD` and `origin/main` were both
  `524d15311bda3ad624a7b5eea499c2942fe62071`.
- After a fresh fetch, Personal Website `HEAD` and `origin/main` were both
  `e41ee0ad9e6b1cd3cec2e05eb079cfdea8b942dd`.
- GitHub Actions were green at both exact starting endpoints:
  - Diary `Backend checks`, run
    [30710883223](https://github.com/oscar940327/diary/actions/runs/30710883223),
    completed successfully for `524d15311bda3ad624a7b5eea499c2942fe62071`.
  - Personal Website `Website checks and Pages`, run
    [30709120399](https://github.com/oscar940327/my-personal-website/actions/runs/30709120399),
    and `pages build and deployment`, run
    [30709120073](https://github.com/oscar940327/my-personal-website/actions/runs/30709120073),
    completed successfully for
    `e41ee0ad9e6b1cd3cec2e05eb079cfdea8b942dd`.

#### TDD RED evidence

- Atomic current-pointer boundary:
  - Command:
    `python -m pytest -q tests/system/test_entry_revisions.py::test_owner_cannot_patch_current_revision_pointer_directly`.
  - The real owner-token PostgREST PATCH returned `204 No Content` instead of
    the required `403`, proving that the owner could point an Entry back to a
    historical revision outside the edit RPC.
- Processing-staleness boundary:
  - Command:
    `python -m pytest -q tests/system/test_entry_revisions.py::test_owner_cannot_patch_processing_staleness_directly`.
  - The real owner-token PostgREST PATCH returned `204 No Content` instead of
    `403`, proving that the owner could clear a superseded revision's
    `stale_at` independently.
- RLS rollback after introducing the narrow mutation principal:
  - Command:
    `python -m pytest -q tests/system/test_entry_revisions.py::test_fastapi_edit_uses_owner_token_for_postgres_rls`.
  - The first run returned `200` instead of `503` because the injected
    restrictive policy still targeted `authenticated` rather than the new
    function owner. This showed that the test had to deny the actual
    `diary_edit_mutator` RLS principal.
- Immutable History membership:
  - Command:
    `python -m pytest -q tests/system/test_continuous_history.py::test_history_snapshot_keeps_an_unvisited_entry_edited_between_pages`.
  - After the initial middle page, another client edited an unvisited Entry.
    Completing both cursor directions returned eight of the nine expected
    test Entries; the edited Entry was omitted because v3 tested the current
    mutable `entries.xmin` against the original snapshot.
- The first sandboxed pointer-test attempt stopped in Supabase CLI setup with
  the known Windows Bun `EPERM` user-file error. The identical authorized run
  reached the `204` product assertion above; only that run is RED evidence.

#### TDD GREEN evidence

- The two direct owner PATCH focused commands each passed after caller UPDATE
  grants were removed and the edit RPC received its narrow mutation role.
- The focused RLS command passed after its restrictive policy targeted
  `diary_edit_mutator`. The original Entry detail and single-revision history
  proved that staling the old obligation, inserting the new revision and
  pending obligation, and moving the current pointer all rolled back.
- The non-owner authorization test passed with FastAPI `401`, direct edit RPC
  RLS denial, and `403` for both raw PATCH paths.
- `python -m pytest -q tests/system/test_entry_revisions.py`: 8 passed,
  covering sequential immutable revisions, current detail and History,
  stale-edit conflict, processing obligations, blank rejection, owner and
  non-owner boundaries, and transactional RLS rollback.
- The concurrent-edit History focused command passed after application
  transition to v4. The original snapshot membership appeared exactly once,
  both directions reached their ends, full microsecond ordering preceded the
  UUID tie-break, and both the current and a fresh traversal displayed the
  edited current revision.
- The equal-time, overlapping-capture, and concurrent-edit History snapshot
  commands passed together: 3 passed.

#### Implementation

- Ordered migration
  `20260802120000_restrict_atomic_edit_mutations.sql` adds the no-login,
  non-superuser, `NOINHERIT`, `NOBYPASSRLS` `diary_edit_mutator` role. It has
  only the table and column privileges required by the existing atomic edit
  function.
- The edit function keeps the same PostgREST contract but now executes as the
  narrow role with `row_security = on`. An equivalent request-UID helper
  reads the caller JWT claims without using a backend or service-role token;
  owner-scoped policies apply that identity to the mutation role.
- `authenticated` no longer has direct UPDATE permission for
  `entries.current_revision_id`, `ai_processing.stale_at`, or their edit-only
  `updated_at` columns. FastAPI still calls PostgREST with the verified owner
  token, while PostgreSQL RLS independently authorizes every affected row.
- Ordered migration
  `20260802130000_stabilize_history_membership.sql` additively stores each
  Entry's immutable capture transaction identity in
  `entries.history_membership_xid`; a trigger rejects later changes.
- The migration leaves v1, v2, and v3 History RPCs available and adds
  contract-compatible `list_diary_history_v4`. V4 uses
  `history_membership_xid` with `pg_visible_in_snapshot()` instead of the
  mutable current tuple's `xmin`.
- FastAPI's store now calls v4. Cursor encoding, HTTP response shapes,
  microsecond/UUID ordering, bidirectional loading, and the Personal Website
  API contract are unchanged. The immediately previous application revision
  remains compatible with the expanded schema and its existing v3 RPC.

#### Complete verification

- Diary:
  - `python -m mypy src tests`: passed, 19 source files.
  - `python -m pytest -q`: passed, 61 tests, with the existing
    Starlette/httpx deprecation warning.
  - `npm.cmd run supabase -- db reset`: passed; all 11 ordered migrations
    applied from a clean local database.
  - `npm.cmd run supabase -- db lint --level warning`: passed with no schema
    findings.
  - `git diff --check`: passed.
- Personal Website, unchanged at
  `e41ee0ad9e6b1cd3cec2e05eb079cfdea8b942dd`:
  - `npm.cmd run typecheck`: passed.
  - `npm.cmd run test:e2e`: 19 Chromium tests passed using four workers.
  - `npm.cmd run build`: passed with only the existing classic-script notices.
  - `npm.cmd run verify:build`: passed.
  - `git diff --check`: passed, and the worktree remained clean.
- The pushed Diary implementation SHA passed GitHub Actions:
  - `Backend checks`, run
    [30712354034](https://github.com/oscar940327/diary/actions/runs/30712354034),
    completed successfully for
    `49667cb0569a93a0bd2d7fa2c5a4f0a59a327d3e`.
- Final mutation-boundary inspection confirmed that authenticated callers
  have neither direct column UPDATE privilege, the function owner is
  `diary_edit_mutator`, and that role cannot log in or bypass RLS.

#### Scope and next fixed ranges

- No AI Draft generation, worker, Queue publication, RAG, revision restore,
  Entry Time edit, Trash, or non-blocking review cleanup was implemented.
- Ticket 07 has not started.
- This implementation session did not run code review. Ticket 06 still needs
  a fresh fixed-range review before Ticket 07 may begin.
- Next fixed review ranges:
  - Diary:
    `b47070d3ed3acb97909c9d59166ba8bed6415cfb...49667cb0569a93a0bd2d7fa2c5a4f0a59a327d3e`.
  - Personal Website:
    `ab99cf8a101e2d0a294a6b1be740ed18b0207e47...e41ee0ad9e6b1cd3cec2e05eb079cfdea8b942dd`.

### 2026-08-02 - New fixed-range code review passed

- Review verdict: **PASSED**.
  - Standards: **PASS** with no blocking or hard violation and four
    non-blocking judgement findings.
  - Spec: **PASS** with no finding.
  - Both axes are free of blocking findings, so Ticket 06 is complete and
    passes the required fresh-session code-review gate.
- Fixed review ranges:
  - Diary:
    `b47070d3ed3acb97909c9d59166ba8bed6415cfb...49667cb0569a93a0bd2d7fa2c5a4f0a59a327d3e`.
  - Personal Website:
    `ab99cf8a101e2d0a294a6b1be740ed18b0207e47...e41ee0ad9e6b1cd3cec2e05eb079cfdea8b942dd`.

#### Preflight

- Diary and Personal Website were both clean on `main` before review.
- Fresh `origin` refs confirmed every fixed-range endpoint is present on
  `origin/main`. Diary `origin/main` and documentation HEAD were
  `76829b08e5e51e484e21199674956beec925d1b6`; Personal Website `HEAD` and
  `origin/main` were the fixed endpoint
  `e41ee0ad9e6b1cd3cec2e05eb079cfdea8b942dd`.
- Both exact three-dot diffs were non-empty, and both exact-range
  `git diff --check` commands passed. The review did not substitute current
  HEAD, a newly computed merge-base, or a working-tree diff for either fixed
  range.
- GitHub Actions were green at every required exact SHA:
  - Diary implementation `Backend checks`, run
    [30712354034](https://github.com/oscar940327/diary/actions/runs/30712354034),
    completed successfully for
    `49667cb0569a93a0bd2d7fa2c5a4f0a59a327d3e`.
  - Diary documentation `Backend checks`, run
    [30712579494](https://github.com/oscar940327/diary/actions/runs/30712579494),
    completed successfully for
    `76829b08e5e51e484e21199674956beec925d1b6`.
  - Personal Website `Website checks and Pages`, run
    [30709120399](https://github.com/oscar940327/my-personal-website/actions/runs/30709120399),
    and `pages build and deployment`, run
    [30709120073](https://github.com/oscar940327/my-personal-website/actions/runs/30709120073),
    completed successfully for
    `e41ee0ad9e6b1cd3cec2e05eb079cfdea8b942dd`.

#### Standards findings

- **Medium; non-blocking judgement call; possible Divergent Change.**
  Personal Website `src/diary/EntryExperience.tsx:254-266,532-649,895-1034`
  adds revision-editor state, conflict handling, revision fetching, and two
  dialogs to the existing History, Calendar, and capture component. At 1,111
  lines, the component weakens ADR 0005's preference for testable, focused
  modules. This is maintainability cleanup and does not block Ticket 06.
- **Low; non-blocking judgement call; Duplicated Code.** Personal Website
  `src/diary/EntryExperience.tsx:604-614,651-661` repeats the
  `Ctrl/Cmd+Enter` submit handler in the edit and capture forms. Existing E2E
  coverage verifies both paths; extracting a shared handler is optional
  cleanup.
- **Low; non-blocking judgement call; Duplicated Code.** Diary
  `src/diary_api/app.py:60-65,86-91` repeats the nonblank Original Content
  validator for capture and replacement request models. Both HTTP 422
  contracts are covered; a shared validator or value type is optional
  cleanup.
- **Low; non-blocking judgement call; Duplicated Code.** Personal Website
  `tests/e2e/entry-revisions.spec.ts:5-55` repeats the unsigned-token,
  localStorage session, and health/owner route scaffold used by other E2E
  specs. A typed fixture could reduce future test setup drift.
- No documented repository, workflow, ADR, migration, security, or testing
  standard was violated. Tool-enforced formatting or type rules were not
  reported as review findings.

#### Spec findings

- **No Spec findings.** Ticket 06 has no missing or partial requirement,
  scope creep, or implementation behavior that appears incorrect in either
  fixed range.

#### Blocking-fix revalidation

- The atomic edit boundary is repaired:
  - Diary
    `supabase/migrations/20260802120000_restrict_atomic_edit_mutations.sql:1-40,42-149,151-310`
    creates a `NOLOGIN`, `NOSUPERUSER`, `NOINHERIT`, `NOBYPASSRLS` mutation
    role, applies owner-scoped RLS to it, runs the edit function with
    `row_security = on`, and revokes authenticated direct UPDATE of
    `entries.current_revision_id`, `ai_processing.stale_at`, and both related
    `updated_at` columns.
  - `src/diary_api/entries.py:192-202,340-358` still sends the verified caller
    bearer token with the publishable key. No service-role token or RLS bypass
    replaces caller authorization.
  - The same migration at `:185-292` locks the owner Entry, stales the old
    obligation, creates the next immutable sequential revision, creates its
    pending Draft and embedding obligation, and moves the current pointer in
    one PostgreSQL transaction.
  - `tests/system/test_entry_revisions.py:260-338,373-492` proves owner and
    non-owner raw PATCH denial, non-owner RPC denial, caller-token RLS, and
    complete transaction rollback when a restrictive RLS policy denies the
    pointer update.
- History snapshot membership is repaired:
  - Diary
    `supabase/migrations/20260802130000_stabilize_history_membership.sql:1-27`
    adds and protects an immutable capture transaction identity. V4 at
    `:33-295` applies `pg_visible_in_snapshot()` to that identity instead of
    mutable `entries.xmin`.
  - `tests/system/test_continuous_history.py:471-610` edits an unvisited Entry
    after the initial page, exhausts older and newer cursors independently,
    and proves the initial membership appears exactly once with no omission or
    duplicate. It also proves full-microsecond Entry Time ordering before the
    UUID tie-break and verifies that both the current traversal and a fresh
    traversal display the edited current revision.
  - The migration is ordered and additive, leaves History v1-v3 available,
    and adds v4. `src/diary_api/entries.py:238-268` transitions the current
    application to v4, while the immediately previous application remains
    compatible with the retained v3 RPC and expanded `entries` schema.

#### Review verification and scope

- The two code-review axes ran in parallel and independently against only the
  fixed ranges above.
- Focused local verification passed five real-system regressions covering both
  direct owner PATCH denials, non-owner API/RLS denial, caller-token RLS
  rollback, and concurrent-edit History exact-once traversal. The first
  sandboxed attempt stopped in Supabase CLI/Bun setup with the known Windows
  user-file `EPERM`; the identical authorized rerun passed all five tests.
- Original Ticket 06 behavior remains present: complete replacement plus
  expected revision, immutable sequential history, newest-current detail and
  History, newest-first owner revision history, deliberate HTTP 409 conflict
  recovery, blank rejection, and durable stale/new processing obligations.
- No AI generation, worker, Queue publication, RAG, revision restore, Entry
  Time edit, Trash, or other Ticket 07 behavior was implemented. No secret was
  added or exposed by either fixed range.
- Personal Website was not modified by the blocking-fix session. Its endpoint
  remains `e41ee0ad9e6b1cd3cec2e05eb079cfdea8b942dd`, and the API contract is
  unchanged.
- Ticket 07 has not started. It may begin only in a separate implementation
  session after this review-documentation commit is pushed and its exact-SHA
  GitHub Actions run succeeds.
