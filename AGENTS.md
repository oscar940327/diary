## Agent skills

### Active version

`main` is the Diary v2 rebuild: a Discord command bot using TypeScript, Hono, Cloudflare Workers, and D1. Start with `DISCUSSION.md` and ADR 0018. The `v1` branch preserves the previous implementation; `.scratch/diary/`, ADRs 0001-0017, and the existing Python/Supabase code describe that legacy version. The active planning directory is `.scratch/diary-v2/`; do not continue legacy Ticket 09 as v2 work.

### Issue tracker

Issues are tracked as Markdown files under `.scratch/<feature>/`. See `docs/agents/issue-tracker.md`.

### Triage labels

Triage uses the default five-state vocabulary. See `docs/agents/triage-labels.md`.

### Domain docs

This is a single-context repository. See `docs/agents/domain.md`.

### Discussion notes

`DISCUSSION.md` is a short current-state summary and index, kept to about 80 lines or fewer. Update its current decisions, open questions, and next step when they change; do not append the full conversation history there.

Before ending each Diary planning conversation, append a short, dated summary to the current monthly file under `docs/discussions/`, even if no decision was made. Follow `docs/discussions/README.md`; start a new monthly file or numbered part rather than letting one file grow indefinitely. Write in plain language, not as a transcript or implementation guide, and separate confirmed decisions from ideas still being discussed. Preserve historical summaries; newer decisions belong in the current summary and, when appropriate, an ADR. Detailed behavior belongs in the spec and tickets.

### Development workflow

Follow the staged Skill workflow in `docs/agents/development-workflow.md`. Implement one ticket at a time, use TDD within that ticket, and run code review in a new session before moving to the next ticket.
