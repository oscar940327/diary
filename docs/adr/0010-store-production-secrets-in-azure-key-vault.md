# Store Production Secrets in Azure Key Vault

## Context

The production backend requires sensitive values such as AI-provider credentials, database access details, and the private GHCR pull credential. These values must not be exposed in the public frontend, committed to Git, or embedded as plaintext in tracked Bicep parameters. Multiple Container Apps workloads need controlled access, and the owner needs a practical way to rotate secrets without editing application source.

## Options

1. Store production values directly as Azure Container Apps secrets.
2. Store production values in Azure Key Vault Standard and expose them to Container Apps through managed-identity-backed Key Vault references.
3. Operate a separate third-party secret-management service.

## Decision

Production backend secrets are stored in Azure Key Vault Standard. Required Container Apps applications and jobs use managed identities with least-privilege access to retrieve Key Vault secrets. Container Apps exposes referenced values to workloads as secret-backed environment variables, so application code does not manage Key Vault credentials. Tracked Bicep files may define the vault, identities, role assignments, and secret references, but secret values are supplied through a secure bootstrap process and are not committed.

Versionless secret references are preferred where automatic use of the latest version is appropriate. The deployment and rotation procedures verify that updated values are refreshed and that affected workloads restart or redeploy as required.

## Consequences

- Production secrets are centrally managed, encrypted, versioned, and independently rotatable.
- Git, GitHub Pages, container images, Bicep source, and committed parameter files contain no secret values.
- Workloads authenticate to Key Vault without a stored Key Vault username or password.
- Each managed identity receives only the secret-read permissions needed by that workload.
- The deployment requires additional Key Vault, managed-identity, RBAC, bootstrap, and troubleshooting steps.
- Key Vault operations consume a small part of the Azure credit and must be included in cost monitoring.
- A secret update is not considered complete until the consuming app or job has been verified with the new value.
- Local development continues to use separate local secret files or environment injection and never retrieves production secrets.
