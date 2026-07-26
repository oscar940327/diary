# 23 — Deploy the Azure API foundation

**What to build:** Provision the reproducible Azure control plane and deploy the authenticated FastAPI image as a public, cost-constrained API. GitHub Actions uses short-lived identity, application secrets stay in Key Vault, and the service can scale to zero.

**Blocked by:** 02 — Enforce owner-only authentication; 22 — Package production images and CI.

**Status:** ready-for-agent

- [ ] Bicep is the source of truth for the supported production resources and every infrastructure release presents `what-if` output for review.
- [ ] Provisioning verifies Azure for Students quota in Japan East and uses the documented matched Singapore/Southeast Asia fallback only as a complete region-pair decision.
- [ ] GitHub Actions authenticates with repository- and release-context-restricted OIDC rather than a long-lived Azure client secret.
- [ ] Key Vault Standard, managed identity, least-privilege role assignments, and application secret references are provisioned without committing secret values.
- [ ] FastAPI runs on Container Apps Consumption with public HTTPS ingress, `minReplicas = 0`, `maxReplicas = 1`, and the private commit-SHA GHCR image.
- [ ] GHCR pull uses a dedicated package-read credential held as an Azure secret; Azure Container Registry is not provisioned.
- [ ] Production configuration uses the selected Supabase project, backend-only `SUPABASE_SECRET_KEY`, singleton owner registry, exact GitHub Pages CORS origin, and Azure-generated API hostname.
- [ ] Structured `INFO` console logging reaches a 30-day Log Analytics workspace; Application Insights is absent.
- [ ] Log Analytics has the initial 0.1 GB daily ingestion safety cap and owner notification.
- [ ] The Diary resource scope has a USD 5 monthly budget with owner alerts at 50, 80, and 100 percent, without disabling the student spending limit or enabling pay-as-you-go.
- [ ] A protected production smoke check verifies readiness, authentication rejection, owner access, and database connectivity without exposing real diary content.
