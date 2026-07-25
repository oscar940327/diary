# 09 — Manage Trash and permanent deletion

**What to build:** Give the owner a recoverable deletion path and a separate deliberate destruction path. Trashed Entries leave normal Diary use immediately, can be restored, and remain indefinitely until the owner confirms permanent deletion.

**Blocked by:** 05 — Navigate history with a calendar; 07 — Restore a historical Entry Revision; 08 — Change Entry Time and regroup history.

**Status:** ready-for-agent

- [ ] Moving an Entry to Trash is distinct from permanent deletion and removes it from history and calendar results.
- [ ] Trash has an owner-only listing that shows enough Entry information to decide whether to restore or destroy it.
- [ ] Restoring clears Trash state and returns the Entry to its correct date group without losing revision history.
- [ ] No automatic age-based Trash purge exists.
- [ ] Permanent deletion requires a separate explicit confirmation value and cannot be triggered by the ordinary delete action.
- [ ] Permanent deletion removes the stable Entry, every Entry Revision, processing records, and any currently existing derived/index records belonging to it.
- [ ] Resource lookup and destructive operations do not reveal another identity's records.
- [ ] Later search, AI, and Agent tickets must treat Trash exclusion and permanent deletion as invariant acceptance behavior.
- [ ] System and browser tests cover trash, normal-view exclusion, restore, confirmation failure, and permanent cascade deletion.
