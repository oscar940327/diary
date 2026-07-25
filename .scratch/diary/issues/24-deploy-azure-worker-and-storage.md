# 24 — Deploy Azure Queue, worker, and Blob storage

**What to build:** Extend the Azure deployment so saved Entry work flows through private Storage Queue to an event-driven Container Apps Job, with Blob storage available for operational artifacts and all secrets supplied through the accepted identity boundary.

**Blocked by:** 11 — Connect the private OpenRouter gateway; 22 — Package production images and CI; 23 — Deploy the Azure API foundation.

**Status:** ready-for-agent

- [ ] Bicep provisions Queue and private Blob resources in the same selected Azure region as the backend where supported.
- [ ] FastAPI publishes opaque work identifiers to Queue without including Original Content or prompts.
- [ ] The worker runs as an event-driven Container Apps Job with zero minimum executions and no more than one concurrent execution.
- [ ] API and worker deployments use artifacts from the same selected commit SHA.
- [ ] Managed identity and Key Vault references grant only the storage and secret access each workload requires.
- [ ] Production OpenRouter model, privacy, and separate-key configuration is injected without appearing in image layers, deployment output, or logs.
- [ ] Duplicate Queue delivery, worker interruption, and unsent-work reconciliation retain their tested idempotent behavior in the deployed shape.
- [ ] Storage containers and queues are not anonymously accessible.
- [ ] A synthetic protected smoke flow saves an Entry, observes Queue processing, and reaches a ready Draft without reading real owner content.
- [ ] Platform and application logs expose state, delay, retries, opaque identifiers, provider/model usage, and deployment SHA but no personal content or secret.
