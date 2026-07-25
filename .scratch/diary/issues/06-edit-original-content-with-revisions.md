# 06 — Edit Original Content with immutable revisions

**What to build:** Let the owner correct or expand Original Content without overwriting history. Editing creates a new current Entry Revision, prior revisions remain inspectable, and a stale edit from another device cannot silently replace newer work.

**Blocked by:** 03 — Capture an Entry and show today's history; 04 — Browse continuous bidirectional history.

**Status:** ready-for-agent

- [ ] Editing submits complete replacement Original Content together with the revision the client believed was current.
- [ ] A successful edit creates a new immutable sequential Entry Revision and changes the Entry's current revision reference atomically.
- [ ] The previous revision remains unchanged and available only to the authenticated owner.
- [ ] History and Entry detail display the newest current revision by default.
- [ ] Revision history exposes sequence, creation time, and complete content in a usable owner interface.
- [ ] A stale expected revision receives a conflict response containing enough current state for the owner to retry deliberately.
- [ ] Editing Original Content marks prior-revision derived processing stale and creates a durable obligation for the new current revision.
- [ ] Empty replacement content is rejected without changing the current revision.
- [ ] System tests cover sequential edits, stale concurrent edits from two clients, immutable prior text, and authorization.
