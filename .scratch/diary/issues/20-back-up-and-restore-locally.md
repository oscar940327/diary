# 20 — Back up and restore Diary locally

**What to build:** Establish a tested logical database recovery path before automating it in Azure. A backup can be restored into an independent database, non-rebuildable data remains correct, and derived retrieval/work state is reconstructed safely.

**Blocked by:** 14 — Add chunking, embeddings, and hybrid memory retrieval; 17 — Manage Conversations and citation lifecycle.

**Status:** ready-for-agent

- [ ] A logical backup captures non-rebuildable schema and data needed for Entries, revisions, corrections, Conversations, messages, citations, owner authorization, and migration version.
- [ ] Rebuildable vectors and transient Queue delivery state are omitted from the recovery dependency.
- [ ] Backup metadata identifies creation time, source environment, schema version, and verification state without embedding secrets.
- [ ] Restore defaults to an independent non-production database and refuses accidental production reset behavior.
- [ ] Restore validation checks representative revision history, effective Correction precedence, Conversation ordering, citation relations, and owner access.
- [ ] Active non-trashed current revisions are re-chunked and re-embedded after restore.
- [ ] Missing eligible AI obligations are reconstructed idempotently without scheduling superseded or trashed revisions.
- [ ] The restored system passes protected capture, history, search, and cited Agent smoke checks through public API behavior.
- [ ] Normal application rollback is documented and tested as separate from database restore.
- [ ] An automated recovery test demonstrates backup, isolated restore, rebuild, and verification without production credentials or real diary content.
