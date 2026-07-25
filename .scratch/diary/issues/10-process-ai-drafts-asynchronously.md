# 10 — Process AI Drafts asynchronously with a fake provider

**What to build:** Complete the asynchronous AI Draft path without live-model cost. Saving a current Entry Revision publishes opaque Queue work, an event-style worker consumes it through a deterministic fake AI boundary, and the owner sees reliable processing states and retry controls.

**Blocked by:** 03 — Capture an Entry and show today's history; 09 — Manage Trash and permanent deletion.

**Status:** ready-for-agent

- [ ] Local system tests run FastAPI, Supabase PostgreSQL, Azurite Queue, the real worker, and a deterministic fake AI provider.
- [ ] Queue messages contain opaque work identifiers and never Original Content or prompts.
- [ ] Entry creation or revision change durably records required work before Queue publication; unsent committed work can be reconciled.
- [ ] The worker treats delivery as at-least-once and duplicate delivery cannot create duplicate Drafts or terminal outputs.
- [ ] Visible states cover `pending`, `processing`, `ready`, `failed`, and their valid atomic transitions.
- [ ] The deterministic Draft contains a one-to-three-sentence summary, controlled categories, and normalized free-form tags below Original Content.
- [ ] One ordinary transient failure retries automatically; the next ordinary failure becomes `failed` and exposes manual retry.
- [ ] A worker restart or expired processing lease can resume unfinished work safely.
- [ ] Trashed and superseded revisions are never processed as active work.
- [ ] Browser and real-HTTP tests poll through public behavior and verify success, duplicate delivery, automatic retry, manual retry, and failure visibility.
