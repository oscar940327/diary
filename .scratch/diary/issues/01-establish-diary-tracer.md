# 01 — Establish the Diary tracer

**What to build:** Create the smallest end-to-end Diary path: the existing personal website exposes a `DIARY` destination, the Diary application loads directly inside that site, and it can confirm that the FastAPI backend is reachable. This establishes the production-shaped frontend/backend seam that later tickets extend.

**Blocked by:** None — can start immediately.

**Status:** ready-for-agent

- [ ] The Sidebar label is `DIARY` immediately below `JOURNEY` and above `MktAgent` in desktop and responsive navigation.
- [ ] Selecting `DIARY` opens a first-class page rather than an iframe or a separately hosted frontend.
- [ ] Only the Diary page body uses React, TypeScript, and Vite; existing pages retain their current implementation and behavior.
- [ ] The Diary page calls a FastAPI health/readiness contract and renders an understandable ready or unavailable state.
- [ ] The GitHub Pages build preserves all existing site pages and assets and uses the repository deployment base correctly.
- [ ] Local startup and verification instructions cover both repositories without requiring a production credential.
- [ ] A browser-level test verifies navigation to Diary and the backend health result.
- [ ] The initial automated checks run in CI and contain no application secret.
