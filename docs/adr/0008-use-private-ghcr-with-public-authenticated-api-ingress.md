# Use Private GHCR with Public Authenticated API Ingress

## Context

The owner must access Diary from desktop and mobile browsers through the public GitHub Pages personal website. Azure therefore needs a publicly reachable HTTPS API. That requirement is independent of whether the packaged backend image is publicly downloadable. Azure Container Registry would add another persistent Azure resource, while GitHub Container Registry integrates with the source workflow and currently meets the single-user project's cost needs.

## Options

1. Publish the backend source and image publicly and let Azure pull without credentials.
2. Keep the backend source and GHCR image private while giving Azure a package-read credential.
3. Keep the backend private and create Azure Container Registry with managed-identity access.

## Decision

The backend source repository and GHCR image remain private for the MVP. GitHub Actions builds images tagged by immutable Git commit SHA. Azure Container Apps stores a dedicated package-read credential as a secret and uses it to pull the image. The FastAPI app still exposes public HTTPS ingress, but all personal-data operations require a verified Supabase owner token. The MVP does not create Azure Container Registry.

## Consequences

- The public GitHub Pages application works from mobile and desktop browsers even though the backend image is private.
- Image visibility is not treated as application authorization; FastAPI independently validates every protected request.
- No recurring Azure Container Registry resource is required.
- The GHCR pull credential must be created with minimum scope, stored only as an Azure secret, rotated, and revoked if exposed.
- Deployment and rollback use immutable commit-SHA image tags rather than `latest`.
- The registry decision must be revisited if GitHub pricing, private-package policy, or authentication support changes.
