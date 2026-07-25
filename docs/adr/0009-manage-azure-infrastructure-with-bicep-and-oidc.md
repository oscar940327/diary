# Manage Azure Infrastructure with Bicep and OIDC

## Context

Diary has several related Azure resources whose region, scaling, ingress, storage, job, and logging settings must be reproducible. A Portal-only setup would leave important production configuration dependent on manual actions and memory. GitHub Actions also needs permission to deploy without exposing a long-lived Azure client secret. The project is Azure-only and does not currently require a cloud-neutral infrastructure tool.

## Options

1. Create and maintain Azure resources manually through Azure Portal and store a long-lived deployment credential in GitHub.
2. Define Azure resources with Bicep and let GitHub Actions authenticate through OIDC workload identity federation.
3. Define Azure resources with Terraform and manage its additional tooling and state.

## Decision

Azure infrastructure is defined with Bicep. Bicep files are the source of truth for supported production resource settings, and the deployment workflow runs `what-if` before applying infrastructure changes. GitHub Actions authenticates to Azure through an OIDC federated identity with short-lived credentials rather than a stored long-lived Azure client secret. Azure Portal remains available for inspection, monitoring, and troubleshooting, but manual Portal changes are not the authoritative configuration. Terraform is not introduced for the MVP.

## Consequences

- Production infrastructure can be reviewed, versioned, and recreated from the repository.
- Deployment instructions do not depend on remembering a sequence of Portal clicks.
- GitHub does not need to retain a reusable Azure client secret for deployment.
- Azure trust must be restricted to the intended repository, workflow or branch, and least-privilege deployment scope.
- Bicep and OIDC require an initial bootstrap procedure and add concepts the owner must learn.
- A `what-if` preview reduces accidental infrastructure changes but does not replace review and testing.
- Secrets such as OpenAI keys and database credentials must remain outside committed Bicep files and parameter files; their exact Azure storage and rotation mechanism is a separate decision.
- Direct Portal changes may drift from Bicep and should either be represented in Bicep or reverted.
- Terraform may be reconsidered if the project later spans multiple cloud providers or requires an existing Terraform-based platform workflow.
