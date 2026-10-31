## Agent skills

### Active version

`main` is the Diary v2 rebuild. Start with the plain-language decisions in `docs/tech-stack.md` and the current summary in `DISCUSSION.md`. The old application, tests, dependency files, and CI have been removed from `main`; the `v1` branch preserves them. Active planning lives in `openspec/changes/`, and archived capability specs live in `openspec/specs/`. `.scratch/diary/`, the earlier `.scratch/diary-v2/` draft, and `docs/adr/` are historical references, not the active v2 work queue. Do not continue legacy Ticket 09 as v2 work.

### Task tracking

Use the selected OpenSpec change's `tasks.md` to track work. Its numbered groups are called stages; the user chooses which stages to run in each apply session. Do not create additional Markdown tickets or require a separate ADR. See `docs/agents/issue-tracker.md` for the distinction from historical records.

### Triage labels

The five-state labels in `docs/agents/triage-labels.md` apply to historical issue files. Active OpenSpec work uses task checkboxes and CLI status, not a second ticket status system.

### Domain docs

This is a single-context repository. See `docs/agents/domain.md`.

### Discussion notes

`DISCUSSION.md` is a short current-state summary and index, kept to about 80 lines or fewer. Update its current decisions, open questions, and next step when they change; do not append the full conversation history there.

Before ending each Diary planning conversation, append a short, dated summary to the current monthly file under `docs/discussions/`, even if no decision was made. Follow `docs/discussions/README.md`; start a new monthly file or numbered part rather than letting one file grow indefinitely. Write in plain language, not as a transcript or implementation guide, and separate confirmed decisions from ideas still being discussed. Preserve historical summaries. Keep the current technology choices in `docs/tech-stack.md`, written in simple, plain language; link to it instead of duplicating the full decision in other files. Detailed behavior and implementation work belong in OpenSpec specs, design, and tasks.

### Development workflow

Implement each change on a dedicated branch based on `main`, such as `change/<change-name>`. Create or switch to that branch before writing implementation code; commit there and use a pull request to propose merging into `main`. Preserve unrelated worktree changes and keep them out of the PR.

Follow the OpenSpec workflow in `docs/agents/development-workflow.md`. During apply, execute only the stages the user selected, use TDD for behavior changes, mark only verified tasks complete, and stop at the requested boundary. If no stage range was specified, clarify the range before implementation. Respect stage dependencies; do not silently include unselected stages. Run independent code review in a new session at the change's review stage before deployment acceptance. Existing authorization applies; do not ask again for already authorized actions.
