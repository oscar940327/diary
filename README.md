# Diary

Diary is an owner-only personal record and memory system. The frontend remains
part of the existing personal website while this repository owns the FastAPI
API, Supabase schema, and cross-repository system tests.

## Local requirements

- Python 3.12 or newer
- Node.js 24 or newer
- Docker Desktop
- The sibling `personal_website` repository

Install the locked backend and local-infrastructure dependencies:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
npm.cmd ci
```

Start Supabase and apply the local migrations:

```powershell
npm.cmd run supabase -- start
npm.cmd run supabase -- db reset
npm.cmd run supabase -- status -o env
```

The status command prints local-only development values. Keep the secret or
service-role key and JWT signing values out of the frontend, screenshots,
logs, and Git.

For interactive local use, open Supabase Studio at
`http://127.0.0.1:54323`, create the one owner under Authentication, and copy
that user's UUID. In the Studio SQL editor, register the same UUID:

```sql
insert into public.diary_owners (user_id)
values ('replace-with-owner-uuid');
```

Set the API process environment:

```powershell
$env:DIARY_ENVIRONMENT = "local"
$env:SUPABASE_URL = "http://127.0.0.1:54321"
$env:SUPABASE_SECRET_KEY = "replace-with-local-secret-or-service-role-key"
python -m uvicorn diary_api.app:app --app-dir src --reload
```

The API readiness endpoint is `http://127.0.0.1:8000/health`. Protected
requests use `Authorization: Bearer <access-token>` and are accepted only when
Supabase's published signing key verifies the token and its issuer, audience,
and expiry, and the token subject matches the single row in
`public.diary_owners`. The database prevents a second owner row. FastAPI reads
that registry with the backend-only secret while PostgreSQL RLS independently
checks the caller's Supabase identity.

In the sibling frontend repository, copy `.env.example` to `.env.local`, use
the local `API_URL` and `PUBLISHABLE_KEY` printed by Supabase, then run:

```powershell
cd "E:\personal_website"
npm.cmd ci
npm.cmd run dev
```

Open `http://127.0.0.1:5173/my-personal-website/diary.html`. Local Magic Link
emails appear in Mailpit at `http://127.0.0.1:54324`.

## Production configuration

Before production use:

1. Apply `supabase/migrations` to the hosted Supabase project.
2. Disable public user sign-up, create the permanent owner administratively,
   and insert that user's UUID into `public.diary_owners`. The insert fails if
   an owner row already exists.
3. Configure the exact GitHub Pages URL as the Supabase Site URL and allowed
   Magic Link redirect.
4. Create a backend-only Supabase secret key in the hosted project, store it
   in Azure Key Vault, and expose it to the API as
   `SUPABASE_SECRET_KEY`.
5. Give the backend the remaining variables below.
6. Give the frontend only the public variables documented in its README.

Required backend variables:

- `DIARY_ENVIRONMENT=production`
- `DIARY_PRODUCTION_ORIGIN=https://oscar940327.github.io`
- `SUPABASE_URL`
- `SUPABASE_SECRET_KEY` (backend-only Key Vault reference)

Optional backend overrides:

- `SUPABASE_JWT_ISSUER` (defaults to `<SUPABASE_URL>/auth/v1`)
- `SUPABASE_JWT_AUDIENCE` (defaults to `authenticated`)

`DIARY_LOCAL_ORIGINS` is only for local/test environments. Production CORS
accepts exactly `DIARY_PRODUCTION_ORIGIN`.

The backend does not receive a JWT signing secret: it verifies access tokens
through Supabase's published JWKS. It does require a Supabase secret key to
read the singleton owner registry independently of caller RLS. The frontend
requires only the Supabase URL and publishable key. Never expose a secret or
service-role key, JWT private key or secret, database password, OpenRouter key,
Azure secret, or registry credential to the browser or Git.

## Verification

The complete backend suite starts a real local Supabase Auth/Postgres/PostgREST
stack, provisions synthetic users, exercises real JWT and RLS behavior through
HTTP, starts the sibling Vite/FastAPI applications, and completes the Magic
Link journey in mobile-sized Chromium:

```powershell
$env:DIARY_FRONTEND_REPOSITORY = "E:\personal_website"
python -m mypy src tests
python -m pytest
```

The system fixture resets only the local Supabase database. It never uses or
changes a hosted project.

Run the complete frontend verification from `personal_website`:

```powershell
npm.cmd run typecheck
npm.cmd run test:e2e
npm.cmd run build
npm.cmd run verify:build
```

Backend CI checks out the frontend at a fixed reviewed commit so the real
cross-repository browser contract cannot drift silently.
