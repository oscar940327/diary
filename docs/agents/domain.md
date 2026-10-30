# Domain Docs

Before exploring the codebase, read `CONTEXT.md` and any relevant ADRs under `docs/adr/`.

On `main`, ADR 0018 defines the v2 rebuild. `CONTEXT.md` is the domain glossary;
current scope belongs in `DISCUSSION.md` and `.scratch/diary-v2/spec.md`.
ADRs 0001-0017 and `docs/archive/v1/` describe v1. Read them as historical
design evidence, not as automatic requirements for v2.

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
