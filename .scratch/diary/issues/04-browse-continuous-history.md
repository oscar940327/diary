# 04 — Browse continuous bidirectional history

**What to build:** Turn the initial today view into the primary continuous Diary history. The owner can read complete Entries grouped by date, load older or newer groups incrementally, and retain visual position while moving through a long history.

**Blocked by:** 03 — Capture an Entry and show today's history.

**Status:** ready-for-agent

- [ ] History opens at today and orders newer Entry Times above older Entry Times.
- [ ] Entries are grouped by `Asia/Taipei` calendar date and display complete current Original Content.
- [ ] Loading downward retrieves older groups without downloading the complete lifetime history.
- [ ] Starting from a past anchor and loading upward retrieves newer groups through a separate cursor.
- [ ] Cursor ordering remains stable when Entries share the same Entry Time by including stable Entry identity.
- [ ] Prepending or appending groups preserves the reader's visual scroll anchor without a disruptive jump.
- [ ] History cursors do not duplicate or omit Entries when data changes between requests.
- [ ] The composer remains accessible without replacing the current history position.
- [ ] Real-HTTP tests cover both cursor directions, equal timestamps, and Taipei date boundaries.
- [ ] Browser tests verify complete content, incremental loading, and scroll anchoring.
