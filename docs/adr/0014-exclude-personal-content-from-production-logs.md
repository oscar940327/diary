# Exclude Personal Content from Production Logs

## Context

Diary processes private diary text, AI-derived content, authentication credentials, and RAG evidence. Container console output is collected by Azure logging, so an ordinary request-body logger, verbose SDK exception, or debug configuration could create uncontrolled copies of personal records and secrets. The owner still needs enough operational information to diagnose authentication, queue, deployment, AI-provider, and performance failures while staying within the student Azure credit.

## Options

1. Log complete requests, responses, AI prompts, and provider errors for maximum debugging detail.
2. Disable production application logs entirely and rely only on visible failures.
3. Emit sanitized structured operational events without personal content or secrets and retain them for a short fixed period.

## Decision

Production emits structured `INFO` logs, with `DEBUG` disabled by default. Allowed fields are limited to operational metadata such as UTC time, a random correlation ID, route template, response status and duration, opaque Job, Entry, and Entry Revision UUIDs, AI state, exact model and upstream provider identifiers, token and cost data, sanitized error type, retry count, queue delay, and deployment commit SHA.

Logs never contain Original Content, revision content, AI Drafts, AI Corrections, Agent questions or answers, RAG prompts or evidence, citation excerpts, request or response bodies, owner email, authentication material, secrets, database credentials, complete query strings, environment-variable values, or raw third-party error bodies. Exceptions and stack traces are sanitized before emission.

Azure Log Analytics stores Container Apps system logs and sanitized console logs for 30 days with an initial 0.1 GB daily ingestion safety cap and owner notification. Application Insights is not enabled for the MVP. Logs are accessible only through the owner's Azure administration identity and are excluded from diary exports and long-term backups.

Acceptance uses unique synthetic content and fake-secret markers, then searches the collected Azure logs and requires that none of those values appear.

## Consequences

- Azure operational logs do not become a secondary diary, conversation, prompt, or credential store.
- Common deployment, queue, retry, latency, model, and cost failures remain diagnosable through identifiers and structured events.
- Debugging content-dependent AI failures relies on private database records and synthetic reproduction rather than copying personal content into logs.
- Logging wrappers, exception sanitization, and marker-based leak tests are required.
- A 30-day retention period limits historical debugging depth.
- The daily ingestion cap reduces the impact of a runaway logging bug but may temporarily remove observability after it is reached.
- Omitting Application Insights reduces telemetry detail and infrastructure complexity; it may be reconsidered through a new privacy and cost review.
