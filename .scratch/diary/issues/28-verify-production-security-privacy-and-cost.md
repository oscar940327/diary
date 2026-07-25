# 28 — Verify production security, privacy, and cost controls

**What to build:** Run the production-shaped acceptance checks that prove Diary protects its owner and student budget. Authentication, privacy routing, log redaction, cost controls, AI recovery, and service smoke behavior must be demonstrated rather than inferred from configuration.

**Blocked by:** 18 — Pause and resume AI work on budget exhaustion; 21 — Evaluate live AI with synthetic Diary data; 24 — Deploy Azure Queue, worker, and Blob storage; 26 — Release blue-green and roll back safely; 27 — Verify GitHub Pages and mobile production journeys.

**Status:** ready-for-agent

- [ ] Production rejects unauthenticated, invalid, expired, and non-owner access while allowing the configured owner.
- [ ] CORS accepts only the exact published personal-site origin and protected API lookup does not disclose foreign resources.
- [ ] OpenRouter account and request settings confirm disabled private input/output logging, disabled model training use, denied data collection, ZDR eligibility, fixed models, and no cross-model fallback.
- [ ] Production and evaluation key limits are verified at USD 5 and USD 1 per month respectively, with automatic top-up disabled.
- [ ] An end-to-end budget-block-and-resume exercise proves no retry storm, continued capture/text search, newest-first backlog recovery, and automatic Agent return.
- [ ] Unique synthetic markers placed in Original Content, prompts, answers, credentials, authorization material, and raw provider errors are absent from queryable Azure logs.
- [ ] Logs retain only accepted structured operational fields, use `INFO` by default, retain 30 days, and respect the ingestion safety cap.
- [ ] Azure budget alerts exist at 50, 80, and 100 percent, the student spending limit remains enabled, and no automatic paid upgrade exists.
- [ ] Supabase quota review thresholds and Free-plan pause/resume behavior are verified and documented.
- [ ] Protected production canary checks cover database, Queue, worker, Blob, search, citation, deployment SHA, and readiness without inspecting real diary content.
- [ ] The live synthetic AI evaluation records zero critical errors for the release candidate.
