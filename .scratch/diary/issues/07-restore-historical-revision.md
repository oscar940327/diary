# 07 — Restore a historical Entry Revision

**What to build:** Allow the owner to select an earlier Entry Revision and make its content current without rewriting history. Restoration copies that content into a new revision and schedules derived processing for the new current source.

**Blocked by:** 06 — Edit Original Content with immutable revisions.

**Status:** ready-for-agent

- [x] The revision-history interface offers a distinct restore action with explicit confirmation.
- [x] Restoring requires both the historical revision identity and the revision currently expected by the client.
- [x] A successful restore creates a new sequential immutable revision whose Original Content equals the selected historical content.
- [x] The selected historical revision and every intervening revision remain unchanged.
- [x] The new revision becomes current in Entry detail and continuous history.
- [x] Restoration creates only the new revision's processing obligation and excludes superseded revisions from active work.
- [x] A stale restore request is rejected as a conflict rather than overwriting a newer edit.
- [x] System and browser tests verify restore, audit history, stale conflict, and current-content display.

## Comments

### 2026-08-03 - Ticket 07 implementation complete

#### Fixed review bases and preflight

- Diary review base:
  `eda071b58a04bf0fa7358b80e0a65e94f4068874`.
- Personal Website review base:
  `e41ee0ad9e6b1cd3cec2e05eb079cfdea8b942dd`.
- Ticket 06's fresh fixed-range review is recorded as `PASSED`, with no
  blocking Standards or Spec finding.
- Both repositories were clean on `main`, and their HEADs exactly matched the
  fixed review bases before Ticket 07 began.
- Latest required GitHub Actions were green at both bases:
  - Diary `Backend checks`, run
    [30713573732](https://github.com/oscar940327/diary/actions/runs/30713573732).
  - Personal Website `Website checks and Pages`, run
    [30709120399](https://github.com/oscar940327/my-personal-website/actions/runs/30709120399),
    and `pages build and deployment`, run
    [30709120073](https://github.com/oscar940327/my-personal-website/actions/runs/30709120073).

#### TDD evidence

- Backend red: the new real-system test reached Supabase, PostgREST and
  Uvicorn, then failed with HTTP `404 Not Found` because
  `/entries/{entry_id}/revision-restorations` did not exist.
- Backend green: the focused restore system set passed `5 passed`, and the
  complete Entry Revision regression set passed `13 passed`.
- Browser red: Chromium opened Revision History and timed out waiting for the
  missing `Restore Revision 1` action.
- Browser green: the focused restore journey passed after the independent
  action and explicit confirmation were implemented; the full frontend
  revision suite passed `3 passed`.

#### Implementation and boundaries

- Ordered migration `20260803120000_restore_historical_revision.sql` adds one
  caller-token, RLS-enforced atomic restore RPC owned by the existing no-login,
  no-bypass mutation role.
- The request contains the selected historical revision ID and the client's
  expected current revision ID. A successful restore copies the selected
  Original Content into the next sequential immutable revision, stales active
  superseded processing, creates exactly one new pending obligation, and moves
  the current pointer in the same PostgreSQL transaction.
- FastAPI keeps the owner authorization boundary and returns HTTP `409` with
  the current Entry for a stale restore. Direct authenticated mutation of
  `current_revision_id` remains denied.
- Revision History exposes Restore only for historical revisions. The first
  action opens a separate explicit confirmation; only confirmation sends the
  request. A stale response displays the newer current revision and does not
  retry automatically.
- Personal Website implementation commit:
  `231ebe21ed09ec7d777f3c78ed6eb58aab396962`. Diary CI is pinned to this exact
  frontend commit for its real browser system journey.
- No new Supabase, GitHub or Azure environment variable is required. No secret
  was added to frontend code or Git.
- Ticket 08, Entry Time mutation, Trash, AI Draft generation, Queue
  publication, RAG and Agent work were not started.
- This implementation session did not run code review. Ticket 07 requires a
  new fixed-range review session after both commits are pushed in order.

#### Full verification

- Diary: `python -m mypy src tests` passed; `python -m pytest` passed
  `66 passed` with one existing Starlette/httpx deprecation warning.
- Personal Website: `npm test` passed typecheck and all `21` Chromium tests;
  `npm run build` and `npm run verify:build` passed.

### 2026-08-03 - Fixed-range code review passed

#### Verdict and fixed ranges

- Review verdict: **PASSED**.
  - Standards: **PASS** with no blocking or documented-standard violation and
    four non-blocking maintainability judgements.
  - Spec: **PASS** with no finding.
- Diary fixed range:
  `eda071b58a04bf0fa7358b80e0a65e94f4068874...c42d0f5f54586c62494c77b99838bb11b372119d`.
- Personal Website fixed range:
  `e41ee0ad9e6b1cd3cec2e05eb079cfdea8b942dd...231ebe21ed09ec7d777f3c78ed6eb58aab396962`.
- Both review axes ran independently and in parallel against only these fixed
  three-dot ranges. Neither axis substituted current HEAD, a newly computed
  merge-base, or a working-tree diff.

#### Preflight and GitHub Actions

- Both worktrees were clean before and after review, and both HEADs exactly
  matched their implementation endpoints.
- Fresh `origin` refs confirmed all four endpoints exist and both
  implementation commits are present on `origin/main`.
- Both fixed ranges were non-empty, with one implementation commit in each.
- Both exact-range `git diff --check` commands passed.
- Exact-SHA GitHub Actions were green:
  - Diary `Backend checks`, run
    [30762305447](https://github.com/oscar940327/diary/actions/runs/30762305447),
    completed successfully for
    `c42d0f5f54586c62494c77b99838bb11b372119d`.
  - Personal Website `Website checks and Pages`, run
    [30762095151](https://github.com/oscar940327/my-personal-website/actions/runs/30762095151),
    and `pages build and deployment`, run
    [30762094606](https://github.com/oscar940327/my-personal-website/actions/runs/30762094606),
    completed successfully for
    `231ebe21ed09ec7d777f3c78ed6eb58aab396962`.

#### Standards findings

- **Medium; non-blocking judgement call; possible Divergent Change.** Personal
  Website `src/diary/EntryExperience.tsx:625-716,1085-1164` keeps Restore
  orchestration, conflict handling, confirmation and presentation in the
  existing large component. Extracting a focused revision-restore module is
  optional maintainability work and does not block Ticket 07.
- **Low; non-blocking judgement call; possible Duplicated Code.** Personal
  Website `src/diary/api.ts:115-149,286-319,344-377` repeats the Edit and
  Restore conflict envelopes, error carriers and HTTP `409` decoding. A shared
  conflict decoder or type is optional cleanup.
- **Low; non-blocking judgement call; possible Duplicated Code.** Diary
  `src/diary_api/app.py:505-542,545-582` and
  `src/diary_api/entries.py:184-215,217-248` repeat mutation-result parsing,
  exception mapping and stale-conflict response shapes between Edit and
  Restore. A narrow shared helper is optional cleanup.
- **Low; non-blocking judgement call; possible Duplicated Code.** Personal
  Website `tests/e2e/entry-revisions.spec.ts:153-193,297-337` repeats browser
  authentication and health/owner route scaffolding. A typed fixture could
  reduce future drift.
- No hard Standards violation or blocking finding was found. Tool-enforced
  formatting or type rules were not reported as review findings.

#### Spec findings and verification

- **No Spec findings.** Ticket 07 has no missing or partial requirement,
  incorrect implementation behaviour, or scope creep in either fixed range.
- Review confirmed the distinct historical-only Restore action and explicit
  confirmation, the two-identity request, sequential immutable copy, unchanged
  historical revisions, current Entry and History display, stale superseded
  processing, one new active obligation, atomic rollback, and HTTP `409` stale
  conflict without retry or overwrite.
- FastAPI continues to use the caller owner token. PostgreSQL forced RLS and
  the no-login, no-bypass mutation role remain an independent authorization
  boundary, while direct owner-token PATCH of the current pointer and
  processing staleness remains denied.
- The ordered migration only adds the Restore RPC and preserves compatibility
  with the immediately previous application revision.
- Focused local verification passed seven Restore, direct-mutation, RLS and
  atomicity system tests; the complete Entry Revision plus continuous-History
  set passed `18 passed`; the real owner/mobile browser set passed
  `14 passed`; the focused snapshot regression passed; the Website Entry
  Revision Playwright spec passed `3 passed`; and an ordered Supabase database
  reset applied every migration successfully.
- Credential, private-key and new-log-call scans of the exact diffs found no
  secret, personal content, token or logging exposure.
- No Entry Time mutation, Trash, AI Draft generation, Queue publication, RAG,
  Agent, or other Ticket 08-or-later work was started.

Ticket 07 passes the required review gate and is complete. Its non-blocking
maintainability judgements are not part of Ticket 08 and should be tracked
separately if the owner chooses to address them.
