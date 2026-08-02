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
