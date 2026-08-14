# 27 — Verify GitHub Pages and mobile production journeys

**What to build:** Connect the completed Diary frontend to the production API through the existing GitHub Pages site and verify the critical owner journeys at desktop and mobile sizes without regressing existing pages.

**Blocked by:** 05 — Navigate history with a calendar; 08 — Change Entry Time and regroup history; 09 — Manage Trash and permanent deletion; 12 — Correct and regenerate AI Drafts; 17 — Manage Conversations and citation lifecycle; 18 — Pause and resume AI work on budget exhaustion; 26 — Release blue-green and roll back safely.

**Status:** ready-for-agent

- [ ] The published personal website contains `DIARY` below `JOURNEY` and above `MktAgent` in all shared navigation copies.
- [ ] The Diary application loads directly at the GitHub Pages origin and calls the configured Azure HTTPS API.
- [ ] Authentication redirects return to Diary and production CORS accepts the published origin.
- [ ] Existing HOME, PROJECT, JOURNEY, MktAgent, VideoNote, assets, and animations remain functional and are not migrated to React.
- [ ] During a schema-changing Diary release, desktop and mobile Diary surfaces present a clear temporary-maintenance state while HOME, PROJECT, JOURNEY, MktAgent, VideoNote, and other non-Diary pages remain usable.
- [ ] Desktop and narrow mobile browser runs complete login, capture, history, calendar jump, Original Content edit, Entry Time change, Trash, and restore.
- [ ] Browser runs also complete AI Correction, direct search, Agent question, Conversation reopen, and citation navigation.
- [ ] A budget-blocked browser case shows continued capture, direct text search, recovery status, and temporary Agent unavailability.
- [ ] Complete Original Content remains readable, critical controls remain reachable, and citation/source presentation is usable at mobile width.
- [ ] Opening capture preserves the underlying history position and bidirectional loading preserves the visible anchor.
- [ ] The browser suite uses synthetic content and does not expose real diary text in CI artifacts or logs.
