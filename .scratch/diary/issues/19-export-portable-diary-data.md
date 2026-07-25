# 19 — Export portable Diary data

**What to build:** Give the owner a versioned, portable archive of non-rebuildable Diary history without leaking credentials or inflating the package with derived infrastructure state.

**Blocked by:** 09 — Manage Trash and permanent deletion; 12 — Correct and regenerate AI Drafts; 17 — Manage Conversations and citation lifecycle.

**Status:** ready-for-agent

- [ ] Only the authenticated owner can request and download an export.
- [ ] Export produces a versioned JSON manifest packaged as JSON/ZIP with generation time and fixed timezone.
- [ ] The archive includes stable Entries, all Entry Revisions, AI Draft generations, current AI Corrections, effective categories and tags, Conversations, messages, and citations.
- [ ] Identifiers and relations are sufficient to associate revisions, corrections, messages, and exact citation sources.
- [ ] Trashed Entries remain exportable until permanently deleted.
- [ ] Permanently deleted Entries and removed citation excerpts do not reappear in a later export.
- [ ] The archive excludes credentials, API keys, JWTs, Magic Links, Queue messages, operational logs, prompts, vectors, and rebuildable index state.
- [ ] Export generation does not write personal content to application logs.
- [ ] Real-HTTP tests parse the archive and verify completeness, relation integrity, Trash behavior, deletion behavior, and all exclusion rules.
