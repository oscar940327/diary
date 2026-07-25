# 07 — Restore a historical Entry Revision

**What to build:** Allow the owner to select an earlier Entry Revision and make its content current without rewriting history. Restoration copies that content into a new revision and schedules derived processing for the new current source.

**Blocked by:** 06 — Edit Original Content with immutable revisions.

**Status:** ready-for-agent

- [ ] The revision-history interface offers a distinct restore action with explicit confirmation.
- [ ] Restoring requires both the historical revision identity and the revision currently expected by the client.
- [ ] A successful restore creates a new sequential immutable revision whose Original Content equals the selected historical content.
- [ ] The selected historical revision and every intervening revision remain unchanged.
- [ ] The new revision becomes current in Entry detail and continuous history.
- [ ] Restoration creates only the new revision's processing obligation and excludes superseded revisions from active work.
- [ ] A stale restore request is rejected as a conflict rather than overwriting a newer edit.
- [ ] System and browser tests verify restore, audit history, stale conflict, and current-content display.
