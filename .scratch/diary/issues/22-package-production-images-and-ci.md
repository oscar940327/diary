# 22 — Package production images and CI

**What to build:** Package the backend workloads reproducibly and build them through CI so later Azure releases can deploy an exact tested commit rather than mutable local artifacts.

**Blocked by:** 10 — Process AI Drafts asynchronously with a fake provider.

**Status:** ready-for-agent

- [ ] FastAPI and asynchronous worker workloads have production-ready container entry points and health/readiness behavior appropriate to their roles.
- [ ] Images run without embedding production secrets and accept environment-specific configuration only at runtime.
- [ ] CI runs formatting, static checks, deterministic tests, and image builds before publishing.
- [ ] Ordinary CI uses local Supabase/Azurite and fake AI boundaries and requires no Azure, production Supabase, or OpenRouter credential.
- [ ] Successful builds publish private GHCR artifacts identified by immutable Git commit SHA.
- [ ] Deployment never requires or selects a mutable `latest` tag.
- [ ] API and worker artifacts can be associated with the same source commit for coordinated release.
- [ ] Build metadata allows a running workload to report its deployment SHA without exposing repository secrets.
- [ ] A local production-shaped smoke test proves the packaged API and worker can communicate with their configured database and Queue.
- [ ] Documentation explains image visibility, required package-read access, and safe local verification.
