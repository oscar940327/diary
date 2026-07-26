# 02 — Enforce owner-only authentication

**What to build:** Make Diary usable only by its pre-created owner even though the frontend and API are publicly reachable. The owner can complete passwordless sign-in on desktop or mobile, while every protected backend and database path rejects unauthenticated or different identities.

**Blocked by:** 01 — Establish the Diary tracer.

**Status:** ready-for-agent

- [x] The Diary page supports Supabase Magic Link or OTP sign-in, sign-out, session restoration, expiry, and understandable authentication errors.
- [x] Public sign-up is disabled and only the pre-created identity in the database-enforced singleton owner registry is accepted.
- [x] Every protected FastAPI request verifies token signature, issuer, audience, expiry, and owner identity.
- [x] A valid Supabase token belonging to a different identity receives the same protected denial behavior as other unauthorized access.
- [x] Row Level Security independently prevents a non-owner from reading or mutating personal tables.
- [x] Production CORS accepts only the exact personal-site origin; local development origins are configured separately.
- [x] The public frontend contains only publishable configuration and no database, OpenRouter, Azure, or container-registry secret.
- [x] System tests cover missing, malformed, expired, non-owner, and valid-owner credentials through real HTTP.
- [x] A mobile-sized browser test completes the owner authentication path and reaches the protected Diary shell.

## Comments

### 2026-07-26 - Implementation

- Personal Website implementation commit:
  `dc5a9d9227c244b22aac78883021f1bd30a7775b`.
- Backend verification: mypy passed for 13 source files; pytest passed
  15 tests, including real local Supabase Auth, JWT, RLS, CORS, FastAPI, Vite,
  and mobile Chromium paths; Supabase database lint reported no schema errors.
- Frontend verification: typecheck passed, 5 Playwright tests passed,
  production build passed, and the preserved-site build verification passed.
- No production credential was used or committed.
- Ticket 02 awaits the required separate-session code review. Ticket 03 has
  not started.

### 2026-07-27 - Blocking review fix

- Reproduced the review failure with the complete real system suite:
  13 tests passed and 2 setup errors because a second owner Magic Link request
  received GoTrue `429 over_email_send_rate_limit`.
- The test fixture now retries only that exact rate-limit response for at most
  three seconds, polling every 100 milliseconds. Every other response still
  fails immediately, and the one-second Supabase email safety interval remains
  enabled.
- The real mobile browser still requests `/auth/v1/otp`, opens the Mailpit
  Magic Link, restores its session after reload, and signs out. The protected
  API and RLS checks still use real Supabase tokens over HTTP.
- After the fix, mypy passed, all 15 Diary tests passed, Supabase warning-level
  database lint reported no schema errors, and all Personal Website
  typecheck, 5 Playwright tests, production build, and build verification
  passed.
- Personal Website remained at
  `dc5a9d9227c244b22aac78883021f1bd30a7775b`. Ticket 03 remains unimplemented.
  Ticket 02 still requires a new separate-session code review.

### 2026-07-27 - Unresolved review findings implementation

- TDD red evidence:
  - A parseable token whose JWKS endpoint was unreachable received `401`
    instead of the expected `503`.
  - Removing `DIARY_OWNER_ID` made a valid owner request fail, and the original
    schema accepted a second owner row with `201`.
  - The frontend rendered a protected-access `503` as signed out, offered no
    recovery action, and a deliberately late stale `401` could replace a newer
    authenticated browser state.
- JWT validation now maps only invalid, expired, unsupported, or claim-invalid
  tokens to the uniform `401`. JWKS connection and invalid-set failures return
  a sanitized `503`; unexpected verifier exceptions are no longer hidden as
  authentication failures.
- `public.diary_owners` is now a database-enforced singleton and the sole owner
  source of truth. FastAPI reads it with backend-only
  `SUPABASE_SECRET_KEY`; `DIARY_OWNER_ID` was removed. RLS still evaluates the
  caller JWT independently. Missing or unreadable owner configuration fails
  closed with `503`.
- The Diary page preserves a valid Supabase session when protected access is
  temporarily unavailable, exposes a retry action, and ignores aborted or
  stale results after a newer session or verification attempt. A real `401`
  for the current session still clears that expired or unauthorized session.
- TDD green and full verification:
  - `python -m mypy src tests`: 14 files passed.
  - `python -m pytest -vv`: all 18 tests passed through real local Supabase
    Auth/Postgres/PostgREST, Uvicorn, HTTP, Vite, Mailpit, and mobile Chromium.
  - `npm.cmd run supabase -- db lint --level warning`: no schema errors.
  - Personal Website typecheck passed; all 7 Playwright tests passed;
    production build and preserved-site build verification passed.
- The exact Magic Link rate-limit retry remains limited to
  `429 over_email_send_rate_limit` for at most three seconds. OTP, Mailpit,
  mobile login, session restoration, sign-out, JWT, RLS, and CORS coverage all
  remain active and passing.
- Duplicate acceptance/system service orchestration was left unchanged because
  it is non-blocking and extracting it would broaden this review fix.
- Ticket 03 remains unimplemented. Ticket 02 is not marked review-passed and
  still requires a fresh `$code-review` session.
