# 18 — Pause and resume AI work on budget exhaustion

**What to build:** Protect journaling and spending when the OpenRouter production key reaches a credit or key limit. AI work pauses without retry storms, text search remains useful, and the owner can explicitly resume a clean current-revision backlog after restoring budget.

**Blocked by:** 11 — Connect the private OpenRouter gateway; 13 — Search Original Content directly; 14 — Add chunking, embeddings, and hybrid memory retrieval; 15 — Answer the first grounded Insight Agent question.

**Status:** ready-for-agent

- [ ] Credit, payment-required, or key-limit responses become `blocked_budget` without consuming the ordinary retry allowance.
- [ ] The first budget failure opens one shared pause atomically and prevents workers from issuing further OpenRouter calls.
- [ ] New Entries and Original Content edits remain fully saveable while the pause is open.
- [ ] Affected Entries clearly show that AI is waiting for budget recovery.
- [ ] Settings reports pause state and eligible waiting, processing, failed, and completed counts without exposing credentials.
- [ ] The owner must explicitly request budget check and resume; the application cannot buy credit, top up, raise limits, or use a Management Key.
- [ ] Recovery schedules only missing obligations for current, non-trashed revisions, newest first, and eventually covers every eligible item.
- [ ] Another budget response reopens the pause immediately without looping.
- [ ] Direct text search remains available and clearly avoids claiming complete semantic behavior while embeddings are missing.
- [ ] Insight Agent requests are unavailable with a clear reason until the active embedding backlog is zero, then return automatically.
- [ ] Real-HTTP tests cover pause, continued capture, no retry storm, backlog counts/order, Trash and superseded exclusion, repeat budget failure, and automatic Agent restoration.
