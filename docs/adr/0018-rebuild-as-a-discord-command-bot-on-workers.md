---
status: accepted
date: 2026-10-30
---

# Rebuild Diary as a Discord command bot on Workers

The owner accepted a rebuild using TypeScript, Hono, Cloudflare Workers, and
Cloudflare D1. Discord is the first user interface, with HTTP interactions
for commands and forms; the first release has no separate website and does
not require a continuously connected discord.js Client. This choice keeps
the initial deployment small, targets free-tier operation, avoids Supabase
already used by another project, and retains a path to later Agent,
reminder, and web functionality.

## Version scope

- `v1` preserves the previous implementation and the discussions recorded
  before this decision. The local archive commit is `899f5d4`.
- `main` starts the v2 rebuild. `.scratch/diary-v2/` is its planning directory;
  `.scratch/diary/` and ADRs 0001-0017 document v1. Legacy platform, website,
  authentication, release, and history-window requirements do not govern v2.
  Any reused product rules must appear in the v2 specification explicitly.
- The prior FastAPI, Supabase, Azure, and React implementation remains in
  the tree temporarily as reference. Its removal and replacement require a
  scoped v2 ticket; this documentation change does not deploy a new runtime.
- The unmerged Ticket 09 branch remains separate. Archiving v1 does not
  assert that Ticket 09 passed review or merge it into either branch.

## Consequences

- Hono handles incoming HTTP requests. Diary rules are separate Modules
  that do not depend on Discord payloads or Hono request objects, so later
  entry points can reuse them. Add concrete abstractions when needed,
  rather than building a general plugin framework in advance.
- Personal records belong in the database; channel messages provide a
  readable presentation. Authentication must verify Discord requests and
  restrict personal operations to the configured owner; a private channel
  alone is not backend authorization.
- AI calls and durable scheduled work need their own designs. Choosing
  Hono does not supply an Agent engine, a queue, a scheduler, or vector search.
- Free-tier quotas are a constraint, not a promise that all future AI and
  storage needs will be free. Paid fallback or automatic upgrades are not
  part of the accepted direction.
- Hono can run on Node.js through an Adapter, but migrating D1 or background
  infrastructure still requires work. First-release commands, retention,
  revisions, exports, and the initial Agent scope remain to be specified.

## Considered options

Express can run on Workers and is a reasonable alternative. Hono was selected
for its direct Workers integration, TypeScript support, and small HTTP-facing
Interface. Elysia's Workers integration was documented as experimental when
evaluated. NestJS provides more framework conventions than this initial
single-owner deployment currently needs. A native Worker without a Web
framework is possible, but the owner asked to consider future expansion as
well as the first few commands.
