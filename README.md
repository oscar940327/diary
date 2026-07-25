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

Backend:

```powershell
python -m pytest
python -m mypy src tests
```

Frontend, from `personal_website`:

```powershell
npm.cmd run typecheck
npm.cmd run test:e2e
npm.cmd run build
npm.cmd run verify:build
```
