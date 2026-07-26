# 02 — Enforce owner-only authentication

**What to build:** Make Diary usable only by its pre-created owner even though the frontend and API are publicly reachable. The owner can complete passwordless sign-in on desktop or mobile, while every protected backend and database path rejects unauthenticated or different identities.

**Blocked by:** 01 — Establish the Diary tracer.

**Status:** ready-for-agent

- [x] The Diary page supports Supabase Magic Link or OTP sign-in, sign-out, session restoration, expiry, and understandable authentication errors.
- [x] Public sign-up is disabled and only the configured pre-created owner identity is accepted.
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
