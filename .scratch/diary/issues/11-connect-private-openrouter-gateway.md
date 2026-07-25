# 11 — Connect the private OpenRouter gateway

**What to build:** Replace the fake-only AI boundary with a production-capable OpenRouter gateway whose model, provider routing, privacy, validation, usage recording, and cost-key separation follow the accepted contract without weakening on failure.

**Blocked by:** 10 — Process AI Drafts asynchronously with a fake provider.

**Status:** ready-for-agent

- [ ] Draft, Agent, and embedding workloads accept exact configured model slugs and reject mutable aliases such as `latest`.
- [ ] Default workload models match the accepted Draft, Agent, and embedding selections.
- [ ] Every request denies provider data collection, requires zero-data-retention eligibility, and requires requested parameter support.
- [ ] Same-model privacy-eligible provider fallback is permitted; cross-model fallback is neither sent nor accepted.
- [ ] No eligible provider produces a visible failure and never causes privacy requirements to be relaxed.
- [ ] Draft structured output rejects invalid summary length, category values, tag shape, or unsupported invented fields.
- [ ] Persisted audit metadata includes exact model, returned provider, request/generation identifier, prompt/schema version, tokens, cost where available, and timestamps.
- [ ] Production and live evaluation use separate inference keys with no Management Key or automatic top-up capability in the application.
- [ ] Operational logs contain neither prompts, Original Content, model output, raw provider response bodies, nor credentials.
- [ ] Ordinary automated tests remain deterministic through the fake boundary; live calls require an explicit command.
