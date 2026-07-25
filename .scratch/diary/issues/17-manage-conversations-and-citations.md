# 17 — Manage Conversations and citation lifecycle

**What to build:** Make prior Agent work revisitable and auditable over time. The owner can browse, continue, and delete Conversations, while citations preserve the exact historical evidence used and degrade safely when an Entry is permanently deleted.

**Blocked by:** 07 — Restore a historical Entry Revision; 09 — Manage Trash and permanent deletion; 16 — Enforce Insight Agent evidence boundaries.

**Status:** ready-for-agent

- [ ] The owner can list, open, and continue persistent Conversations with their complete visible message history.
- [ ] Deleting a Conversation removes its messages and citations but does not modify any Entry.
- [ ] Opening a citation displays the complete exact Entry Revision used by that Agent message.
- [ ] A cited historical revision remains unchanged when the Entry later receives a newer revision.
- [ ] Citation detail indicates when a newer current revision exists and offers navigation to the current Entry in continuous history.
- [ ] Navigation preserves access to the cited historical snapshot.
- [ ] Multiple chunks from one Entry Revision remain one visible source with stable numbering per Agent message.
- [ ] Permanently deleting an Entry removes the citation excerpt and live target and leaves an intelligible source-unavailable marker.
- [ ] A permanently deleted source cannot be reconstructed from citation storage or exposed by normal API responses.
- [ ] Browser and real-HTTP tests cover continuing and deleting a Conversation, revision drift, citation navigation, and unavailable sources.
