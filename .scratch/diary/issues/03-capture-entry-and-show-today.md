# 03 — Capture an Entry and show today's history

**What to build:** Let the authenticated owner capture free-form Original Content and immediately see the saved Entry in today's date group. Each submission creates an independent durable Entry and first Entry Revision before any AI activity can affect the result.

**Blocked by:** 02 — Enforce owner-only authentication.

**Status:** ready-for-agent

- [ ] Each successful submit creates one stable Entry and one immutable first Entry Revision containing the complete Original Content.
- [ ] Multiple submissions on the same day remain separate Entries.
- [ ] Empty and whitespace-only submissions are rejected without creating partial records.
- [ ] Desktop capture supports `Ctrl/Cmd + Enter`, and the same composer is usable at a mobile viewport.
- [ ] Entry Time defaults to now in `Asia/Taipei` but can be intentionally supplied for a late or backdated Entry.
- [ ] Merely browsing a past date never changes the default Entry Time of a new capture.
- [ ] Repeating the same create idempotency key returns the original Entry instead of creating a duplicate.
- [ ] Original Content and its durable processing obligation are committed before the API reports success or attempts external AI work.
- [ ] Today's group displays the complete Original Content, Entry Time, immutable capture time, and current processing state.
- [ ] Saving preserves the underlying browsing position and offers a direct action to view the new Entry.
- [ ] Real-HTTP system tests cover multiple same-day Entries, backdating, blank rejection, UTC persistence, Taipei grouping, and idempotency.
