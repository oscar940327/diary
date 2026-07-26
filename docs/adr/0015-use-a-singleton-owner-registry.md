# Use a Singleton Owner Registry

## Context

Diary is permanently owned by one person. Ticket 02 originally represented that identity twice: FastAPI compared JWT subjects with `DIARY_OWNER_ID`, while PostgreSQL RLS relied on `public.diary_owners`. The environment variable and table could drift, allowing the API and database authorization layers to disagree. The two authorization layers must remain independent defenses without creating two owner sources of truth.

## Options

1. Keep `DIARY_OWNER_ID` authoritative and generate or validate the database row during deployment.
2. Keep both values and fail application startup when they differ.
3. Make a database-enforced singleton `public.diary_owners` row authoritative, let FastAPI read it with a backend-only Supabase secret, and let RLS independently evaluate the caller against the same row.

## Decision

`public.diary_owners` is the authoritative permanent owner registry. A database singleton constraint permits at most one row, and production provisioning must create that row before protected use. FastAPI verifies the Supabase JWT, reads the owner row through PostgREST using `SUPABASE_SECRET_KEY`, and compares the verified subject with it. `DIARY_OWNER_ID` is removed.

RLS remains enabled and forced. Browser and authenticated PostgREST requests use the caller's JWT, so RLS independently exposes the owner row only when `auth.uid()` matches it. The backend secret is stored through the Azure Key Vault arrangement in ADR 0010 and is never sent to the frontend.

If the registry is absent, malformed, unreachable, or cannot be read, protected FastAPI authorization fails closed with a service-unavailable response. A valid non-owner, invalid token, or expired token continues to receive the same unauthorized response.

## Consequences

- FastAPI and RLS cannot silently drift between an environment owner UUID and a database owner UUID.
- The database prevents provisioning a second Diary owner.
- FastAPI authorization and PostgreSQL RLS remain separate enforcement paths over one identity source.
- Protected API requests add a small PostgREST lookup; the owner UUID is not cached indefinitely, so administrative corruption or removal is detected rather than hidden.
- The backend now requires a Supabase secret key and its Key Vault bootstrap and rotation procedure; the public frontend still receives only the publishable key.
- Deleting the owner Auth user cascades to the registry row and makes protected API access unavailable until the owner configuration is deliberately repaired.
