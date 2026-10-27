## Agent skills

### Issue tracker

Issues are tracked as Markdown files under `.scratch/<feature>/`. See `docs/agents/issue-tracker.md`.

### Triage labels

Triage uses the default five-state vocabulary. See `docs/agents/triage-labels.md`.

### Domain docs

This is a single-context repository. See `docs/agents/domain.md`.

### Discussion notes

Before ending each Diary planning conversation, add a short, dated summary to `DISCUSSION.md`, even if no decision was made. Write in plain language, not as a transcript or implementation guide. Clearly separate confirmed decisions from ideas still being discussed. Detailed behavior belongs in the spec and tickets; high-impact architecture decisions belong in ADRs.

### Development workflow

Follow the staged Skill workflow in `docs/agents/development-workflow.md`. Implement one ticket at a time, use TDD within that ticket, and run code review in a new session before moving to the next ticket.
