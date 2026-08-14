# Use Expand-Contract Database Migrations

## Context

Blue-green application deployment can return traffic to a previous Container Apps revision, but it does not reverse changes already applied to Supabase PostgreSQL. A destructive migration could therefore make the previous application version unusable precisely when it is needed for rollback. Automatically restoring an earlier database backup would be worse for an ordinary release failure because Entries created after that backup could be lost.

## Options

1. Apply unrestricted schema changes with each release and automatically run down migrations during application rollback.
2. Restore the pre-release database backup whenever the application is rolled back.
3. Use versioned expand-contract migrations so the current and immediately previous application revisions remain compatible with the production schema.

## Decision

All production schema changes are ordered, versioned SQL migrations committed with the project. A release containing a schema change creates and verifies an additional logical backup before applying the migration.

Migrations use expand-contract sequencing. A first release adds backward-compatible tables, columns, constraints, or indexes and deploys code that tolerates the transition. Required data migration or backfill occurs without removing structures needed by the previous application revision. Obsolete structures may be removed only in a later release after the compatibility window has passed.

[ADR 0016](./0016-use-maintenance-windows-for-schema-changing-releases.md) defines how schema-changing production releases execute. Expand-contract compatibility applies to the stable schema states before and after migration and keeps the immediately previous application version available for rollback. It does not require the previous and new versions to accept concurrent production writes while migration files are executing; those releases quiesce Diary inside a maintenance window.

Normal application rollback changes Container Apps traffic and related workload versions but does not automatically run a down migration or restore the database. Migration failure stops the release before traffic moves to the new revision, using transactional execution where PostgreSQL supports it. Database restore remains a disaster-recovery operation.

## Consequences

- The immediately previous application revision can remain a usable rollback target after a schema migration.
- Entries written after deployment are not discarded merely to roll back application code.
- Schema history is reviewable and reproducible rather than dependent on Portal or dashboard edits.
- Releases with schema changes require a verified pre-migration backup and additional checks.
- Removing an old column or table normally takes more than one release.
- Application code may temporarily support both old and new representations.
- That compatibility supports staged releases and rollback, not concurrent old-version writes during migration execution; ADR 0016 supplies the maintenance boundary.
- Irreversible data transformations require explicit design, backup, and acceptance beyond the ordinary migration workflow.
- A rollback can restore application behavior but cannot automatically undo every external side effect produced by the newer version.
