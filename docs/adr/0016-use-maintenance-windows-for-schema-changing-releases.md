# Use Maintenance Windows for Schema-Changing Releases

## Context

Ticket 08 accumulated repeated implementation and review cycles because production migration reasoning allowed the preceding application version to keep writing while separately transacted migration files were being applied. That concurrency creates gaps which are difficult to make safe across every old write path. Diary is an owner-operated service, while the rest of the personal website is independently useful, so a short Diary-only interruption is an acceptable MVP trade-off.

## Options

1. Require zero-downtime migrations and support concurrent writes from old and new backend versions throughout every migration.
2. Use a short Diary-only maintenance window for schema-changing releases, quiesce all Diary writers, and preserve expand-contract compatibility for the states before and after the migration.
3. Take the entire personal website offline whenever Diary has a schema-changing release.

## Decision

A production release containing a database schema migration uses a short Diary-only maintenance window. The personal website and all non-Diary pages remain available. Before migration work begins, the release stops accepting new Diary API requests, returns an explicit maintenance response for Diary reads and writes, waits for every in-flight Diary request to finish, and pauses or drains write-capable Diary background workloads. Old and new backend versions do not write concurrently while migrations run. A release-only route may exercise the zero-traffic candidate with synthetic data after migration, but it does not reopen normal Diary access.

After Diary is quiescent, the release creates and verifies a pre-migration logical backup, applies the ordered migrations using transactions where PostgreSQL supports them, validates the resulting data, provisions and privately verifies the selected commit-SHA API and worker, promotes that version while the maintenance gate remains closed, and runs post-deployment protected synthetic smoke checks. Diary traffic resumes only after the migrated data, API, worker, deployment identity, and critical smoke behavior have all passed verification.

If a migration or any later release gate fails, Diary remains in maintenance and no production Diary traffic is reopened. The release uses transaction rollback where available. If transaction rollback is insufficient, the operator follows the existing recovery runbook; database restore is not an automatic application rollback. A post-migration application rollback may select the immediately previous compatible application version, but it is verified while maintenance remains active before traffic resumes.

This decision complements [ADR 0012](./0012-manually-promote-blue-green-production-releases.md) and [ADR 0013](./0013-use-expand-contract-database-migrations.md). Expand-contract sequencing and compatibility with the immediately previous application version remain required before and after migration so application rollback stays viable. They do not require old and new versions to continue writing concurrently during migration execution.

## Consequences

- Schema-changing releases briefly interrupt Diary reads and writes, but do not interrupt other personal-site pages.
- The migration safety boundary is a drained, quiescent Diary service; same-Entry and other concurrent old-version writes during migration are outside the supported production contract.
- Release automation and runbooks must implement maintenance entry, request draining, writer quiescence, verified backup, migration, data and API verification, version promotion, smoke verification, and explicit maintenance exit.
- A failed migration or release verification can extend the maintenance window until rollback or recovery is complete.
- Expand-contract migrations still take multiple releases when structures must be removed, and the immediately previous application version remains a valid rollback target after migration.
- Zero-downtime database migration is not an MVP requirement. It may be reconsidered only through a later architecture decision with a concrete availability need and a tested concurrent-writer strategy.
