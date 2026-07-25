# Development workflow

Diary uses the following Skill workflow. Do not skip directly from discussion to implementation, and do not combine multiple implementation tickets in one pass.

| Step | Skill or phase | Purpose | Completion condition |
| --- | --- | --- | --- |
| 1 | `setup-matt-pocock-skills` | Initialize the project documents, Issue Tracker, and documentation locations used by this Skill set. | Project setup is complete and Codex knows where documents and tickets belong. |
| 2 | `grill-with-docs` | Clarify the MVP one primary question at a time while maintaining terminology, decisions, and unresolved questions in project documents. | Core ambiguity is removed and Codex explicitly says the project is ready for `to-spec`. |
| 3 | `to-spec` | Turn confirmed requirements into a formal MVP specification without product code. | The specification covers scope, non-goals, behavior, boundary cases, testing decisions, and acceptance criteria. |
| 4 | `to-tickets` | Split the specification into vertically sliced tickets that can each be completed and tested independently. | Tickets have a clear order, dependencies, acceptance criteria, and sufficiently small scope. |
| 5 | `implement` | Implement exactly one selected ticket and no unrelated feature. | The ticket's behavior, tests, and required documentation are complete. |
| 6 | `tdd` | During implementation, first add a test that fails for the expected reason, then write the minimum implementation that makes it pass and refactor while green. | The test changes from a verified failure to a pass and genuinely exercises the ticket behavior. |
| 7 | `code-review` | In a new session, review the completed ticket for defects, specification drift, code smells, and maintainability. | Serious findings are fixed and the review passes. |
| 8 | Next ticket | Repeat `implement` → `tdd` → `code-review` for the next dependency-ready ticket. | Every MVP ticket is complete. |
| 9 | `improve-codebase-architecture` | After the codebase has grown, inspect shallow modules, fragmented logic, and unnecessary abstractions. | Use only when architectural friction is visible; it is not a mandatory step for every ticket. |

## Operating rules

- The active implementation unit is one Issue Tracker ticket.
- `tdd` is normally used inside the `implement` work for that ticket; it is not permission to expand the ticket.
- Run `code-review` in a fresh session after the ticket implementation is complete.
- Resolve blocking review findings before selecting the next ticket.
- Select the next ticket only when its dependencies are complete.
- If implementation reveals a conflict with the specification, `CONTEXT.md`, or an accepted ADR, stop and document the decision instead of silently changing the product.
- Use `improve-codebase-architecture` only when concrete architectural problems have appeared or after a meaningful group of tickets, not as routine cleanup after every ticket.
