# 26 — Release blue-green and roll back safely

**What to build:** Give the owner a deliberate production release path that verifies a new immutable revision before traffic, keeps the previous version available, and preserves database compatibility during rollback.

**Blocked by:** 23 — Deploy the Azure API foundation; 24 — Deploy Azure Queue, worker, and Blob storage; 25 — Automate daily backups in Azure.

**Status:** ready-for-agent

- [ ] Ordinary pushes run checks and build commit-SHA artifacts but cannot deploy production automatically.
- [ ] Production deployment starts only through a manual workflow whose input identifies the immutable version.
- [ ] A schema-changing release enters Diary-only maintenance, closes all new Diary API reads and writes, drains in-flight requests, and quiesces write-capable workers before backup or migration; non-Diary personal-site pages remain available.
- [ ] Versioned SQL migrations are applied in order and use transactions where supported.
- [ ] Schema-changing release verifies a pre-migration logical backup before migration begins.
- [ ] Migrations follow expand-contract compatibility so the immediately previous application revision can still run after migration as a rollback target; old and new versions do not write concurrently during migration execution.
- [ ] The ordered schema-changing sequence is maintenance entry, request and writer draining, backup creation and verification, transactional migration, migrated-data validation, selected-version provisioning, protected API/worker smoke verification, deployment promotion, post-deployment smoke verification, and explicit maintenance exit.
- [ ] A new Container Apps Green revision receives no normal production traffic until provisioning, startup, readiness, migration, data validation, image-SHA, privacy, and protected smoke checks pass; protected checks run while the public Diary surface remains in maintenance.
- [ ] API and worker promoted together use artifacts from the same selected commit SHA.
- [ ] Successful promotion sends all production traffic to Green and retains the prior known-good revision at zero traffic.
- [ ] A failed gate in a schema-changing release keeps Diary in maintenance with traffic closed; transaction rollback or the existing recovery runbook is used before any maintenance exit.
- [ ] Manual rollback routes traffic and worker selection to the prior immutable release without rebuilding.
- [ ] Rollback does not execute an automatic down migration or restore an old database.
- [ ] A post-migration application rollback verifies the immediately previous version against the migrated schema while maintenance remains active and resumes traffic only after smoke checks pass.
- [ ] An automated or guided exercise records successful maintenance entry, draining, backup verification, migration, smoke checks, deployment, maintenance exit, and return to the prior version, plus a failed-gate recovery that never reopens traffic prematurely.
