# 25 — Automate daily backups in Azure

**What to build:** Turn the proven local recovery path into a scheduled Azure operation. Diary creates one daily logical backup in private Blob storage, retains thirty recovery points, and demonstrates restoration into an independent database.

**Blocked by:** 20 — Back up and restore Diary locally; 24 — Deploy Azure Queue, worker, and Blob storage.

**Status:** ready-for-agent

- [ ] A scheduled Container Apps Job creates one logical PostgreSQL backup per day using least-privilege secrets.
- [ ] Backup artifacts are written only to a private Blob container.
- [ ] Backup name or metadata exposes creation time, source environment, schema version, and verification state without including credentials or personal excerpts.
- [ ] Lifecycle management retains the latest 30 daily backups and removes older blobs automatically.
- [ ] Backup execution and failure are visible through sanitized operational metadata and owner-oriented diagnostics.
- [ ] The restore procedure targets an independent database by default and refuses ambiguous production replacement.
- [ ] A selected Azure backup restores Entry revisions, Correction precedence, Conversations, citations, owner authorization, and schema version correctly.
- [ ] The exercise rebuilds embeddings and eligible AI work and proves protected history, search, and Agent behavior afterward.
- [ ] The completed restore test records the backup identity, destination, verification results, duration, and any known limitation without storing secrets.
- [ ] Storage consumption and retention behavior are included in cost review guidance.
