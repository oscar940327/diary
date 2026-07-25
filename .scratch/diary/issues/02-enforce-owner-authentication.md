# 02 — Enforce owner-only authentication

**What to build:** Make Diary usable only by its pre-created owner even though the frontend and API are publicly reachable. The owner can complete passwordless sign-in on desktop or mobile, while every protected backend and database path rejects unauthenticated or different identities.

**Blocked by:** 01 — Establish the Diary tracer.

**Status:** ready-for-agent

- [ ] The Diary page supports Supabase Magic Link or OTP sign-in, sign-out, session restoration, expiry, and understandable authentication errors.
- [ ] Public sign-up is disabled and only the configured pre-created owner identity is accepted.
- [ ] Every protected FastAPI request verifies token signature, issuer, audience, expiry, and owner identity.
- [ ] A valid Supabase token belonging to a different identity receives the same protected denial behavior as other unauthorized access.
- [ ] Row Level Security independently prevents a non-owner from reading or mutating personal tables.
- [ ] Production CORS accepts only the exact personal-site origin; local development origins are configured separately.
- [ ] The public frontend contains only publishable configuration and no database, OpenRouter, Azure, or container-registry secret.
- [ ] System tests cover missing, malformed, expired, non-owner, and valid-owner credentials through real HTTP.
- [ ] A mobile-sized browser test completes the owner authentication path and reaches the protected Diary shell.
