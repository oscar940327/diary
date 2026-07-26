# 01 — Establish the Diary tracer

**What to build:** Create the smallest end-to-end Diary path: the existing personal website exposes a `DIARY` destination, the Diary application loads directly inside that site, and it can confirm that the FastAPI backend is reachable. This establishes the production-shaped frontend/backend seam that later tickets extend.

**Blocked by:** None — can start immediately.

**Status:** ready-for-agent

- [x] The Sidebar label is `DIARY` immediately below `JOURNEY` and above `MktAgent` in desktop and responsive navigation.
- [x] Selecting `DIARY` opens a first-class page rather than an iframe or a separately hosted frontend.
- [x] Only the Diary page body uses React, TypeScript, and Vite; existing pages retain their current implementation and behavior.
- [x] The Diary page calls a FastAPI health/readiness contract and renders an understandable ready or unavailable state.
- [x] The GitHub Pages build preserves all existing site pages and assets and uses the repository deployment base correctly.
- [x] Local startup and verification instructions cover both repositories without requiring a production credential.
- [x] A browser-level test verifies navigation to Diary and the backend health result.
- [x] The initial automated checks run in CI and contain no application secret.

## Comments

### 2026-07-26 — Code review

Implementation commits:

- Diary backend: `afe7f64c340862b113c82c8c79a9b807ce7a6f47`
- Personal Website frontend: `e8e6bbe3831d91c2aca73c7f9fdf790f1dc6ccbf`

Review verdict: **Blocked.** The automated suites pass, but one serious Ticket 01
Spec finding remains unresolved.

#### Standards

- **Low — test-depth recommendation, not a hard standards violation.**
  `personal_website/tests/e2e/diary-tracer.spec.ts` intercepts every `/health`
  request, while the backend contract is tested separately in
  `diary/tests/test_health.py`. This cannot catch proxy rewrite, URL/path, or
  cross-repository integration errors.
- No documented-standard violations or reportable baseline code smells were
  found. Production CORS is intentionally excluded from this review because it
  belongs to Ticket 02; implementing it here would violate the one-ticket scope
  rule.

#### Spec

- **High — Ticket 01 browser acceptance is only partially implemented.** Ticket
  01 requires the smallest end-to-end path to confirm that FastAPI is reachable
  and a browser-level test of the backend health result. All three Playwright
  cases in `personal_website/tests/e2e/diary-tracer.spec.ts` use
  `page.route(...).fulfill(...)`, so the browser never calls the real FastAPI
  service. The CI suite would remain green if the API URL, Vite proxy rewrite,
  actual `/health` path, or frontend/backend contract were broken. The backend
  `TestClient` test does not cover that seam. Add one browser acceptance test
  that starts and calls the real FastAPI service.
- The remaining Ticket 01 scope passes review: desktop/mobile navigation order,
  first-class React page without an iframe, ready/unavailable UI, GitHub Pages
  base and legacy-asset preservation, two-repository local instructions, CI,
  and absence of application secrets. No material scope creep was found.

#### Verification

- Backend `python -m pytest`: **1 passed**; one non-blocking Starlette/httpx
  deprecation warning.
- Backend `python -m mypy src tests`: **passed**, no issues in 3 source files.
- Frontend `npm.cmd run test`: **passed** (`typecheck` plus **3 Playwright tests**).
- Frontend `npm.cmd run build`: **passed**.
- Frontend `npm.cmd run verify:build`: **passed**.
- Independent preservation check: all **50/50** pre-existing site pages/assets
  from the frontend base commit are present in `dist`.
- `git diff --check` passed for both comparison ranges; both repository HEADs
  match the implementation SHAs above.

Ticket 01 should not pass code review until the real frontend-to-FastAPI browser
acceptance test is added and the full verification suite is rerun.

### 2026-07-26 - Code re-review

Implementation commits:

- Diary backend and cross-repository acceptance:
  `8addbd4a2389fe4df353a773f9eb120e7a2efbfb`
- Personal Website frontend:
  `e8e6bbe3831d91c2aca73c7f9fdf790f1dc6ccbf`

Review verdict: **Passed.** Standards and Spec both pass with zero findings.
The previous blocking finding is resolved.

#### Browser acceptance evidence

- `tests/acceptance/test_diary_tracer.py` does not use `page.route`,
  `route.fulfill`, or any other `/health` mock.
- Its session fixture starts the real FastAPI application through Uvicorn and
  starts the pinned Personal Website checkout through its real Vite executable.
- The fixture removes `VITE_DIARY_API_URL`, so React requests the local default
  `/diary-api/health` path.
- Chromium navigates from HOME to DIARY and observes the response at
  `/diary-api/health`; Vite proxies and rewrites that request to FastAPI
  `/health`.
- The test asserts HTTP 200, the exact FastAPI JSON response, the final Diary
  URL, and the rendered ready state.
- Backend CI pins the Personal Website implementation SHA above and runs the
  complete pytest suite containing this acceptance test.

#### Verification

- Backend `python -m pytest -vv`: **2 passed**, including the real Chromium
  cross-repository acceptance; one non-blocking Starlette/httpx deprecation
  warning.
- Backend `python -m mypy src tests`: **passed**, no issues in 5 source files.
- Frontend `npm.cmd run test`: **passed** (`typecheck` plus **3 Playwright
  tests**).
- Frontend `npm.cmd run build`: **passed**.
- Frontend `npm.cmd run verify:build`: **passed**.
- `git diff --check` passed for both review ranges, and both repository HEADs
  match the implementation SHAs above.

No Ticket 02 authentication, authorization, CORS, persistence, Entry, or queue
behavior was implemented. Ticket 02 was not started.
