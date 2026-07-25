# Co-locate Supabase and Azure in Northeast Asia

## Context

The owner primarily accesses Diary from Taiwan. FastAPI and its background jobs perform repeated database round trips to Supabase, while Container Apps, Queue, Blob, and logging also communicate within Azure. Choosing unrelated regions would add avoidable latency and cross-region transfer. Region changes later require recreating regional Azure resources and coordinating database migration.

## Options

1. Choose each service's region independently based only on immediate availability.
2. Place Supabase in Singapore and Azure in Southeast Asia.
3. Prefer Supabase Tokyo and Azure Japan East, with Singapore and Southeast Asia as a matched fallback pair.

## Decision

The preferred production pair is Supabase Northeast Asia (Tokyo, `ap-northeast-1`) and Azure Japan East. All supported Azure backend resources use Japan East. Before provisioning, deployment verifies that the Azure for Students subscription has the required availability and quota. If Japan East is unavailable, both sides move together to Supabase Singapore and Azure Southeast Asia.

## Consequences

- The database and backend are geographically close to the owner and to each other.
- Azure API, Job, Queue, Blob, and logging traffic stays within one selected Azure region where supported.
- Deployment documentation must verify actual regional availability before creating resources.
- The system does not intentionally combine a Tokyo database with a Singapore backend or the reverse.
- Moving regions later requires planned recreation, migration, validation, and cutover rather than an in-place toggle.
