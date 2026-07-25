# Run AI Processing from an Azure Queue

## Context

Original Content must be saved and returned to the user without waiting for AI processing. FastAPI is hosted on Azure Container Apps with scale-to-zero, so in-process background work could be interrupted by a restart, deployment, or scale-down. AI failures must be retryable without duplicating work for the same Entry Revision.

## Options

1. Run the AI request synchronously inside the Entry creation request.
2. Start an in-process FastAPI background task after returning the HTTP response.
3. Enqueue the Entry Revision ID in Azure Storage Queue and process it with an event-driven Azure Container Apps Job.

## Decision

FastAPI first persists the Entry Revision and an idempotent AI-processing record, then publishes the Entry Revision ID to Azure Storage Queue and returns success. An event-driven Azure Container Apps Job consumes queued work with zero minimum executions and at most one concurrent execution. It updates the processing state and stores the AI Draft or final failure.

An OpenRouter account-credit or API-key-limit error uses the distinct `blocked_budget` state and opens a shared budget pause. The pause durably accumulates eligible work without repeatedly calling OpenRouter. After the owner restores credit or changes the external key limit, an explicit Settings action checks the current key state and resumes current, non-trashed Entry Revisions idempotently, newest first. Another budget error immediately restores the pause. The application cannot purchase credit, raise the limit, or store an OpenRouter Management Key.

## Consequences

- Entry capture remains fast and valid even when the AI provider is slow or unavailable.
- Queued work survives API restarts, deployments, and scale-to-zero.
- Duplicate delivery must be safe; database constraints and processing-state transitions enforce one active job per Entry Revision.
- Budget exhaustion does not create a retry storm or consume the ordinary one-retry failure allowance.
- Eligible current work can be reconstructed and requeued after budget recovery without processing superseded or trashed revisions.
- Insight Agent remains unavailable until the active embedding backlog is complete, while non-AI Entry operations and direct text search continue to work.
- Recovery requires an explicit owner action after an external OpenRouter credit or key-limit change.
- Deployment requires an Azure Storage account, queue, managed access, and a separately configured Container Apps Job.
- The worker incurs compute usage only while processing queued work, but the queue and job add operational complexity.
