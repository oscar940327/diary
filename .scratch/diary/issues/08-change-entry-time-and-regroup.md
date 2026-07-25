# 08 — Change Entry Time and regroup history

**What to build:** Let the owner move an Entry to the intended date and time while preserving the distinction between metadata and Original Content. The Entry moves across history and calendar groups without creating a content revision.

**Blocked by:** 04 — Browse continuous bidirectional history.

**Status:** ready-for-agent

- [ ] The owner can edit Entry Time through an explicit Entry action.
- [ ] A valid change updates Entry metadata without creating or changing an Entry Revision.
- [ ] Immutable capture time remains unchanged and is distinguishable from Entry Time.
- [ ] The Entry disappears from its former date group and appears in the correct new `Asia/Taipei` group.
- [ ] Calendar presence or counts update for both affected dates.
- [ ] History cursor ordering remains correct after moving an Entry across a date or across an equal timestamp.
- [ ] Invalid timestamps are rejected without partial changes.
- [ ] Changing Entry Time alone does not invalidate or regenerate AI interpretation of unchanged Original Content.
- [ ] System and browser tests cover same-day changes, cross-day moves, timezone boundaries, and unchanged revision count.
