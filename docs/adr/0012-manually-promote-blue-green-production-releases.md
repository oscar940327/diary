# Manually Promote Blue-Green Production Releases

## Context

Diary is an owner-operated production system containing irreplaceable personal records. Automatically deploying every push would let an unverified change immediately affect desktop and mobile use. The backend source and image are versioned by Git commit SHA, and Azure Container Apps supports immutable revisions and traffic switching. The owner also needs a deployment process that can be learned and operated without reconstructing hidden setup knowledge.

## Options

1. Automatically deploy every successful push directly to the production revision.
2. Build and test automatically, then require a manually started production workflow that replaces the running version in place.
3. Build and test automatically, then require a manually started blue-green release that verifies a new revision before switching traffic and retains the previous revision for rollback.

## Decision

Tests and commit-SHA image builds run automatically, but production deployment starts only when the owner invokes a GitHub Actions `workflow_dispatch` release and selects the intended version.

FastAPI uses Azure Container Apps multiple-revision mode. The workflow provisions a new revision without assigning it production traffic, waits for startup and readiness checks, and runs deployment smoke checks. Only a successful revision receives 100 percent of production traffic. The immediately previous known-good revision remains available with zero production traffic for rapid rollback. If pre-traffic verification fails, the existing revision continues serving traffic. A post-release rollback changes traffic back to the previous revision and does not rebuild or rely on a mutable image tag.

API and AI-processing workloads released together use the same commit-SHA image version. The handoff includes a written owner runbook and a guided deployment and rollback exercise.

## Consequences

- A successful push cannot unexpectedly replace the production backend.
- New code is checked in its production Azure environment before receiving normal frontend traffic.
- The previous immutable image and revision provide a fast application rollback path.
- Multiple-revision configuration, traffic labels, health endpoints, and smoke checks add deployment complexity.
- A zero-traffic revision may briefly consume compute during verification, but can scale back to zero afterward.
- Manual release approval adds a deliberate step to every production update.
- Traffic rollback does not roll back database schema or external side effects, so database migrations require a separate compatibility policy.
- The owner must be able to identify the active revision, inspect a failed workflow, start a release, and perform a rollback using the documented procedure.
