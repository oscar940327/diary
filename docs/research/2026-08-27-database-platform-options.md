# Diary database platform options

Checked against official documentation on 2026-08-27. Prices and quotas can change; verify the provider console before provisioning.

## Recommendation

Use a **second managed Supabase Free project dedicated to Diary** if the account currently has only one active Free project. Having another application on Supabase is not, by itself, a reason to move Diary: Supabase grants two Free projects across every organization where the user is an Owner or Administrator. A separate project gives Diary its own database, Auth users, API keys, quotas, and failure boundary while preserving the architecture already implemented. [Supabase billing documentation](https://supabase.com/docs/guides/platform/billing-on-supabase)

The fallback, only if both Supabase Free slots are already occupied and neither project can be paused, is **Neon Free plus a deliberately scoped authentication/data-access redesign**. Neon is the strongest low-cost PostgreSQL alternative, but it is not a connection-string-only replacement for this repository.

Do not choose Azure Database for PostgreSQL Flexible Server merely to spend the Azure student credit, and do not self-host Supabase for this single-user MVP. Both add materially more cost or operations than a second managed Supabase project.

## Why switching is unusually expensive here

Diary currently depends on the Supabase platform rather than only PostgreSQL:

- The browser authenticates with Supabase Auth and FastAPI verifies the Supabase JWT issuer.
- FastAPI calls Supabase PostgREST for the owner registry and Entry RPCs rather than opening a normal PostgreSQL connection.
- Migrations reference `auth.users`, `auth.uid()`, and Supabase's `anon`, `authenticated`, and `service_role` roles. RLS depends on PostgREST propagating the caller's JWT claims.
- The system and browser tests start the complete local Supabase stack and verify real Auth, PostgREST, RLS, HTTP, and Chromium paths.

These dependencies are visible in [`src/diary_api/config.py`](../../src/diary_api/config.py), [`src/diary_api/owner_registry.py`](../../src/diary_api/owner_registry.py), [`src/diary_api/entries.py`](../../src/diary_api/entries.py), the ordered [`supabase/migrations`](../../supabase/migrations), and [ADR 0015](../adr/0015-use-a-singleton-owner-registry.md). Consequently, moving to generic PostgreSQL requires redesigning the data-access and RLS identity boundary, not just changing `DATABASE_URL`.

## Comparison

| Option | Current cost/limits | Architecture impact | Backups and future RAG | Assessment |
|---|---|---|---|---|
| Separate Supabase project | Free allows two active projects across owned/administered organizations. Each Free project includes 500 MB database size; the plan includes 5 GB egress and 1 GB file storage. Free projects pause after one week of inactivity. Free has no automatic backups or PITR. Pro starts at USD 25/month, includes the first project, and additional projects start at USD 10/month; it includes 8 GB disk per project and seven-day daily backups. [Pricing](https://supabase.com/pricing) [Billing scope](https://supabase.com/docs/guides/platform/billing-on-supabase) | Lowest: keep Auth, PostgREST, JWT validation, roles, RLS, migrations, local stack, and tests. Provision a new owner account/registry row and replace environment URLs/keys. | PostgreSQL and future `pgvector` remain in the same platform. The planned daily logical backup to private Azure Blob is still important because Free has no managed automatic backup. | **Best fit.** Isolated from the other project and probably USD 0 for the current single-user workload. |
| Neon Postgres | Free currently lists 100 projects, 100 CU-hours/month per project, 0.5 GB storage/project, compute up to 2 CU, and up to six hours of time travel/restore. Idle compute scales to zero after five minutes and wakes on access. Paid Launch is usage-based (USD 0.106/CU-hour and USD 0.35/GB-month) with up to seven-day restore. [Neon pricing](https://neon.com/pricing) [Scale to zero](https://neon.com/docs/introduction/scale-to-zero) | High: replace Supabase PostgREST calls with direct FastAPI PostgreSQL access or another API layer; recreate the `auth` identity contract, database roles, per-transaction JWT claims, owner lookup, and RLS tests. Keeping Supabase Auth separately still does not preserve the existing `auth.users` foreign keys or `auth.uid()`/PostgREST behavior automatically. | Neon officially supports `pgvector`; `CREATE EXTENSION vector` enables it. Free restore is useful but short, so retain the planned portable logical backups. [Neon pgvector](https://neon.com/docs/ai/ai-concepts) | **Best non-Supabase alternative**, but defer the migration until there is a concrete limit/cost reason. Cold-start latency is acceptable for a personal diary if handled in the UI. |
| Azure Database for PostgreSQL Flexible Server | Managed, provisioned PostgreSQL with Burstable, General Purpose, and Memory Optimized tiers; minimum storage is 32 GiB. Compute billing stops when the server is stopped, but storage/backups continue to be billed and the server automatically starts after seven days. [Compute/storage](https://learn.microsoft.com/en-us/azure/postgresql/compute-storage/concepts-compute) [Stop/start](https://learn.microsoft.com/en-us/azure/postgresql/overview) [Stopped-server billing](https://learn.microsoft.com/en-us/azure/postgresql/backup-restore/concepts-backup-restore) | Same major Auth/PostgREST/RLS rewrite as Neon unless Supabase components are separately hosted. Azure-native networking and administration also add deployment work. | Supports allowlisted PostgreSQL extensions including vector dependencies. Automated PITR retention is 7–35 days; backup storage up to 100% of provisioned storage is included, with excess and geo-redundant usage billed. [Extensions](https://learn.microsoft.com/en-us/azure/postgresql/extensions/how-to-create-extensions) [Backups](https://learn.microsoft.com/en-us/azure/postgresql/backup-restore/concepts-backup-restore) | **Not recommended for this budget.** Azure for Students gives USD 100 for one year (renewable while eligible), only USD 8.33/month on average; an internet-available provisioned database plus minimum storage should not be assumed to fit that ceiling. Obtain the exact regional quote in the Azure calculator before considering it. [Azure for Students](https://learn.microsoft.com/en-us/azure/education-hub/about-azure-for-students) [Pricing calculator guidance](https://learn.microsoft.com/en-us/azure/postgresql/compute-storage/concepts-compute#price) |
| Self-host Supabase on Azure | Supabase recommends Docker; the complete stack needs at least 2 CPU, 4 GB RAM, and 40 GB SSD (4 CPU, 8 GB+, and 80 GB+ recommended). Managed backups/PITR, platform management, and advanced managed observability are unavailable. The operator owns patching, hardening, HA, backup/DR, monitoring, and uptime. [Self-hosting](https://supabase.com/docs/guides/self-hosting) [Docker requirements](https://supabase.com/docs/guides/self-hosting/docker) | Application compatibility can be high because Auth and PostgREST remain, but infrastructure and release complexity rise sharply; URLs, signing keys, SMTP, proxy/TLS, upgrades, backups, and secrets become owner-operated. | `pgvector` is possible, but every durability and recovery control must be built and tested. | **Reject for MVP.** The operational burden and VM/storage requirement are disproportionate and a poor use of the USD 100/year credit. |

## Practical decision rule

1. If only one Supabase Free project is active, create Diary as the second Free project and continue the current Tickets unchanged.
2. If two slots are active, check whether an inactive project can be paused (paused projects do not count toward the Free limit) before redesigning Diary.
3. If a third always-active free database is genuinely required, write a new ADR and migration Ticket for Neon; do not change providers inside Ticket 09 or another product Ticket.
4. Keep the existing local Supabase test environment even if production later moves. A provider migration needs additional parity tests rather than removing the current security regression suite.

## Provisioning implications for the recommended option

The new Diary Supabase project must be treated as production isolation, not as a schema inside the existing application's project:

- choose the already-decided region pair;
- apply the full ordered migration chain;
- disable public sign-up, create the one owner Auth user, and insert exactly that UUID into `public.diary_owners`;
- configure the GitHub Pages Magic Link redirect allowlist;
- rotate production `SUPABASE_URL`, publishable key, secret key, and JWT issuer configuration in GitHub/Azure without committing them;
- execute owner-only Auth, FastAPI, PostgREST, and RLS smoke tests;
- verify a logical backup and restore before storing real diary data.

This preserves the current defense-in-depth design and avoids reopening Tickets 02–09 solely because another Supabase project exists.
