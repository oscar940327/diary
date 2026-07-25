# 16 — Enforce Insight Agent evidence boundaries

**What to build:** Make Agent answers trustworthy when evidence is partial, ambiguous, or absent. Every turn re-retrieves personal records, separates supported facts from inference and general advice, and says clearly when Diary cannot support a personal claim.

**Blocked by:** 15 — Answer the first grounded Insight Agent question.

**Status:** ready-for-agent

- [ ] Every user turn performs retrieval again; previous Agent prose is never considered evidence about the owner.
- [ ] Previous messages may resolve conversational references, but only retrieved Original Content can support personal-record claims.
- [ ] Explicit time expressions narrow retrieval, while ambiguous temporal or metadata filters broaden rather than silently discard evidence.
- [ ] Record-grounded statements, cross-record inference, and general advice have distinct visible representations.
- [ ] Inference is labeled and cites the underlying records; general advice is labeled as not coming from Diary and carries no personal citation.
- [ ] A versioned sufficiency check runs before generation and validates the structured answer afterward.
- [ ] When evidence is insufficient, the response begins with an explicit insufficient-record statement.
- [ ] Optional general advice may follow insufficient evidence only in its separate non-record section.
- [ ] The Agent cannot browse the web, use external tools, send reminders, or call unrelated services.
- [ ] The complete Conversation remains visible even when only a bounded context is supplied to the model.
- [ ] Deterministic system cases cover grounded facts, multi-record inference, general advice, ambiguity, temporal filtering, follow-up turns, and abstention.
