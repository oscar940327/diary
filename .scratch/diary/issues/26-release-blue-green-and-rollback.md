# 26 — Release blue-green and roll back safely

**What to build:** Give the owner a deliberate production release path that verifies a new immutable revision before traffic, keeps the previous version available, and preserves database compatibility during rollback.

**Blocked by:** 23 — Deploy the Azure API foundation; 24 — Deploy Azure Queue, worker, and Blob storage; 25 — Automate daily backups in Azure.

**Status:** ready-for-agent

- [ ] Ordinary pushes run checks and build commit-SHA artifacts but cannot deploy production automatically.
- [ ] Production deployment starts only through a manual workflow whose input identifies the immutable version.
- [ ] Versioned SQL migrations are applied in order and use transactions where supported.
- [ ] Schema-changing release verifies a pre-migration logical backup before migration begins.
- [ ] Migrations follow expand-contract compatibility so the immediately previous application revision can still run.
- [ ] A new Container Apps Green revision receives no production traffic until provisioning, startup, readiness, migration, image-SHA, privacy, and protected smoke checks pass.
- [ ] API and worker promoted together use artifacts from the same selected commit SHA.
- [ ] Successful promotion sends all production traffic to Green and retains the prior known-good revision at zero traffic.
- [ ] A failed pre-traffic check leaves the existing production revision untouched.
- [ ] Manual rollback routes traffic and worker selection to the prior immutable release without rebuilding.
- [ ] Rollback does not execute an automatic down migration or restore an old database.
- [ ] An automated or guided exercise records a successful release and return to the prior version.
