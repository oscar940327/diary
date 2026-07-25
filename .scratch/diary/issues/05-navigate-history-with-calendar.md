# 05 — Navigate history with a calendar

**What to build:** Add a calendar as an alternative way to locate Entries. Selecting a day positions the owner inside the same continuous history, rather than opening an isolated daily document.

**Blocked by:** 04 — Browse continuous bidirectional history.

**Status:** ready-for-agent

- [ ] The owner can switch between continuous history and calendar without losing the ability to capture a new Entry.
- [ ] A requested month shows presence or counts derived only from active, non-trashed Entries.
- [ ] Selecting a date opens continuous history with that date as the anchor.
- [ ] After a calendar jump, scrolling upward reaches newer dates and scrolling downward reaches older dates.
- [ ] Dates, month boundaries, today, and Entry counts use `Asia/Taipei` regardless of browser timezone.
- [ ] A date with no Entry still produces a stable nearby history position and an understandable empty state.
- [ ] Calendar retrieval does not return complete personal content unnecessarily.
- [ ] System tests cover month boundaries, empty dates, multiple Entries per date, and fixed-timezone behavior.
- [ ] Desktop and mobile browser tests verify the calendar-to-history journey.
