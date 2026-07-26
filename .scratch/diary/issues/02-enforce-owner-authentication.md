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

### 2026-07-27 - Code review verdict: failed

- Fixed implementation ranges reviewed:
  - Diary:
    `e64a6c53206767bac79c3765681acb439bb915bc...517e73200d7154179d311c5fa79a2ef12b209c54`.
  - Personal Website:
    `e8e6bbe3831d91c2aca73c7f9fdf790f1dc6ccbf...c6592f326a03fe4ec3a25e005cd71df6d1b5d219`.
- Standards verdict: passed with zero hard findings. One non-blocking
  Duplicated Code judgement remains in the acceptance/system service
  orchestration helpers.
- Spec verdict: failed with one blocking finding. `SupabaseJwtVerifier`
  converts every generic `PyJWKClientError` into an invalid token and therefore
  a `401`. With the installed PyJWT, a JWKS response that is not a JSON object
  or contains no usable signing key also raises `PyJWKClientError`; those
  invalid-set failures must return the sanitized authentication-service `503`
  required by this ticket. The existing test covers an unreachable JWKS
  endpoint but not these invalid-JWKS responses.
- The other latest review findings are resolved: the database-enforced
  singleton owner registry is the sole owner source, registry failures fail
  closed, RLS remains independent, and the frontend preserves valid sessions
  during protected-access outages while rejecting stale results.
- Full local verification on the implementation SHAs passed:
  - `python -m mypy src tests`: 14 files passed.
  - `python -m pytest -vv`: all 18 tests passed.
  - `npm.cmd run supabase -- db lint --level warning`: no schema errors.
  - Personal Website typecheck, all 7 Playwright tests, production build, and
    preserved-site build verification passed.
- GitHub Actions were green on both implementation SHAs: Diary Backend checks
  run `30217972628`, Website checks and Pages run `30217977607`, and Pages
  deployment run `30217977145` all concluded successfully.
- CI caveat: Diary CI still checks out Personal Website
  `dc5a9d9227c244b22aac78883021f1bd30a7775b`, not the final Website
  implementation SHA. The complete local cross-repository suite did use
  `c6592f326a03fe4ec3a25e005cd71df6d1b5d219`.
- Ticket 02 is not formally review-passed. Ticket 03 remains unimplemented and
  must not start until the blocking JWKS classification finding is fixed and a
  fresh review passes.

### 2026-07-27 - JWKS classification finding implementation

- TDD red evidence: a real HTTP JWKS endpoint returning a JSON array produced
  the uniform `401`; the new protected-API test expected the sanitized
  authentication-service `503`.
- `SupabaseJwtVerifier` now validates the signing-key set separately from
  matching the token `kid`. An unreachable, non-object, malformed, empty, or
  unusable JWKS fails closed with the sanitized `503`; a valid JWKS that does
  not contain the requested `kid` receives the uniform `401`.
- Public HTTP classification tests cover malformed, expired, missing-claim,
  and invalid-signature tokens with the same `401` body and challenge header.
  The pre-existing real-system malformed and expired token coverage remains
  active.
- The first fresh spec review found that structurally malformed key entries
  such as `{"keys":[null]}` could escape PyJWT as `AttributeError`. A second
  red-green cycle covered that shape. The next review found malformed RSA
  field types escaping as `TypeError`; a third red-green cycle now covers empty
  response bodies, invalid encoding, non-object keys, and malformed key fields.
  The verifier classifies the finite external decode/key-shape exception set as
  the same sanitized `503` without catching broad `Exception`.
- Diary CI now pins Personal Website commit
  `c6592f326a03fe4ec3a25e005cd71df6d1b5d219`, replacing the intermediate
  `dc5a9d9227c244b22aac78883021f1bd30a7775b` pin.
- Local verification:
  - `python -m mypy src tests`: 14 source files passed.
  - Focused auth suite: all 15 tests passed.
  - Full Diary suite: 25 tests passed; the two production-CORS cases could not
    start because an unrelated user-owned
    `python -m uvicorn main:app --reload --port 8001` process already occupied
    their fixed local test port. The process was inspected but not stopped.
  - Supabase warning-level database lint reported no schema errors.
  - Pinned Personal Website typecheck, all 7 Playwright tests, production
    build, and preserved-site build verification passed.
- A fresh review and clean-runner GitHub Actions verification remain required.
  Ticket 03 remains unimplemented.
