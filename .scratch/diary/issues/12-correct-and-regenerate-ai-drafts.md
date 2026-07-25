# 12 — Correct and regenerate AI Drafts

**What to build:** Let the owner correct the AI's structured interpretation while preserving all three layers: immutable Original Content, generated AI Draft, and owner-authored AI Correction. Regeneration stays auditable and never silently defeats the owner's correction.

**Blocked by:** 10 — Process AI Drafts asynchronously with a fake provider; 11 — Connect the private OpenRouter gateway.

**Status:** ready-for-agent

- [ ] The AI section is secondary to Original Content, compact, collapsible, and displays current processing state.
- [ ] The owner can edit summary, controlled categories, and tags without changing Original Content.
- [ ] An AI Correction is stored separately for the exact Entry Revision and becomes effective metadata immediately.
- [ ] Unknown categories are rejected and tags are trimmed, deduplicated case-insensitively, and empty values removed.
- [ ] Regenerating creates a new auditable Draft generation and leaves an existing Correction effective.
- [ ] Discarding a Correction in favor of a regenerated Draft requires a distinct explicit confirmation.
- [ ] Editing Original Content excludes the old revision's Draft and Correction from current display and metadata use.
- [ ] A newly current revision receives new processing without copying a prior revision's Correction.
- [ ] System tests verify effective-metadata precedence, invalid values, regeneration, explicit discard, and revision isolation.
- [ ] Browser tests verify correction and regeneration flows on desktop and mobile.
