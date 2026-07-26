# Diary

Diary is an owner-only personal record and memory system. Ticket 01 establishes
the first tracer between the React page in the existing personal website and
this FastAPI backend.

## Run the API locally

Requirements:

- Python 3.12 or newer

From this repository:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
python -m uvicorn diary_api.app:app --app-dir src --reload
```

The public readiness endpoint is available at
`http://127.0.0.1:8000/health`.

## Run the frontend locally

The frontend is part of the sibling `personal_website` repository. In another
PowerShell window:

```powershell
cd "E:\personal_website"
npm.cmd install
npm.cmd run dev
```

Open `http://127.0.0.1:5173/my-personal-website/diary.html`.

Vite proxies the local `/diary-api` path to `http://127.0.0.1:8000`. The
production API URL is supplied later as a public build variable.

The browser configuration contains only the public API URL. Ticket 01 requires
no production credential.

## Verify

Install the backend test dependencies and Chromium once:

```powershell
python -m pip install -e ".[dev]"
python -m playwright install chromium
```

The browser acceptance test needs the Ticket 01 frontend checkout and its
locked Node dependencies. Set its path explicitly so the same command works
regardless of where the two repositories live:

```powershell
npm.cmd ci --prefix "E:\personal_website"
$env:DIARY_FRONTEND_REPOSITORY = "E:\personal_website"
python -m pytest tests\acceptance
```

That pytest command starts this repository's Uvicorn service on port `8000`
and the frontend repository's Vite service on port `4173`, opens a real
Chromium browser, navigates from HOME to DIARY, and waits for the unmocked
`/diary-api/health` request to pass through Vite to FastAPI `/health`. The test
stops both services when it finishes.

Run the complete backend suite:

```powershell
python -m pytest
python -m mypy src tests
```

Run the complete frontend suite from `personal_website`:

```powershell
npm.cmd run typecheck
npm.cmd run test:e2e
npm.cmd run build
npm.cmd run verify:build
```

Backend CI checks out the public frontend repository at the fixed Ticket 01
commit, installs both repositories' dependencies, installs Chromium, and runs
the complete backend suite. Keeping the cross-repository orchestration in the
backend workflow means CI does not need a token that can read the private
Diary repository from another repository.
