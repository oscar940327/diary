# 13 — Search Original Content directly

**What to build:** Provide a direct lookup tool that finds Entries without generating an answer. Exact and fuzzy text search remains useful independently of AI availability, supports deliberate filters, and reconnects every result to continuous history.

**Blocked by:** 04 — Browse continuous bidirectional history; 09 — Manage Trash and permanent deletion; 12 — Correct and regenerate AI Drafts.

**Status:** ready-for-agent

- [ ] Direct search is a distinct surface and never invokes an answer-generation model.
- [ ] The text branch searches current Original Content using PostgreSQL trigram matching.
- [ ] Exact project, company, technology, and person names are discoverable in Chinese, English, and mixed-language records.
- [ ] Explicit date, controlled-category, and tag filters can be combined with the query.
- [ ] Category and tag filtering uses effective metadata, preferring AI Correction over AI Draft.
- [ ] Results identify the Entry and Entry Time and show a useful matching excerpt without replacing canonical content.
- [ ] Selecting a result opens the current Entry in continuous date-grouped history.
- [ ] Only current revisions of active, non-trashed Entries can appear.
- [ ] Search remains complete for its text branch when embeddings or OpenRouter are unavailable.
- [ ] Real-HTTP and browser tests cover literal names, mixed language, filters, correction precedence, navigation, trash, and superseded revisions.
