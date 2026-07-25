# Domain Docs

Before exploring the codebase, read `CONTEXT.md` and any relevant ADRs under `docs/adr/`.

If these files do not exist, proceed silently. Domain-modeling skills create them lazily when terminology or architectural decisions are resolved.

## Layout

This repository uses a single-context layout:

```text
/
|-- CONTEXT.md
|-- docs/adr/
`-- src/
```

Use terminology defined in `CONTEXT.md`. If proposed work conflicts with an existing ADR, surface the conflict explicitly instead of silently overriding it.
