# 29 — Complete operator documentation and handoff

**What to build:** Hand Diary over as an owner-operable production system. The owner receives usable instructions, performs the critical operational exercises, and records a final MVP checklist that identifies the live version, safeguards, costs, and limitations.

**Blocked by:** 19 — Export portable Diary data; 20 — Back up and restore Diary locally; 21 — Evaluate live AI with synthetic Diary data; 25 — Automate daily backups in Azure; 26 — Release blue-green and roll back safely; 28 — Verify production security, privacy, and cost controls.

**Status:** ready-for-agent

- [ ] Runbooks cover initial Azure bootstrap, region/quota choice, Bicep and `what-if`, OIDC, Key Vault secret bootstrap and rotation, GHCR access, and Supabase owner provisioning.
- [ ] Runbooks cover manual production release, active/prior revision identification, Diary-only maintenance entry, admission closure, in-flight request and worker draining, verified pre-migration backup, compatible migration, data/API/worker smoke verification, deployment, explicit maintenance exit, and failed-check diagnosis.
- [ ] Failure instructions require maintenance to remain active with Diary traffic closed, use transaction rollback where supported, and otherwise follow the existing recovery runbook before any verified reopen.
- [ ] Runbooks cover export, daily backup status, isolated restore, embedding/work rebuild, and the rule that ordinary rollback does not restore the database.
- [ ] Runbooks cover OpenRouter production/evaluation keys, privacy settings, credit checks, budget pause/resume, backlog interpretation, and the prohibition on automatic top-up.
- [ ] Runbooks cover Supabase Free quota review and low-activity pause/resume, Azure and OpenRouter cost review, sanitized logs, and ingestion-cap behavior.
- [ ] The owner completes a guided schema-changing release and rollback exercise, can identify the deployed commit SHA and previous known-good revision, and demonstrates that non-Diary personal-site pages remain available throughout Diary maintenance.
- [ ] The owner completes or reviews the recorded isolated backup restore and AI budget recovery exercises.
- [ ] The final handoff checklist records selected regions, production URLs, release SHA, quota and cost checks, security/privacy verification, recovery results, live AI evaluation, known limitations, and runbook locations.
- [ ] The checklist confirms all MVP acceptance criteria and critical desktop/mobile journeys pass with no unresolved blocking defect.
- [ ] The handoff explicitly records that ML is not part of the MVP and may only be reconsidered after the documented data-age and active-day thresholds.
- [ ] The owner receives a step-by-step Azure deployment learning path suitable for repeating the process without relying on undocumented Portal memory.
