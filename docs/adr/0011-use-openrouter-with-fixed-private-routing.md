# Use OpenRouter with Fixed Private Routing

## Context

Diary sends highly personal diary text to language and embedding models. The owner wants OpenRouter as the API entry point, while the project has already selected separate models for AI Draft generation, Insight Agent answers, and embeddings based on cost and expected quality. OpenRouter can simplify API access and route one model across multiple upstream providers, but unrestricted routing or model fallback could change quality, price, supported parameters, and data-handling behavior without an application release.

## Options

1. Call OpenAI directly with an OpenAI API key.
2. Use OpenRouter with its default routing and permit automatic fallback to other models and providers.
3. Use OpenRouter as the sole AI gateway with exact model slugs, privacy filters, and no cross-model fallback.

## Decision

The MVP uses OpenRouter as its sole AI API gateway. The configured workloads use the exact slugs `openai/gpt-5.4-mini`, `openai/gpt-5.6-luna`, and `openai/text-embedding-3-small`; mutable aliases such as `latest` are prohibited in production.

OpenRouter may retry another eligible upstream endpoint only for the same exact model. It must not silently change to a different model. Every production request sets provider data collection to deny and requires a zero-data-retention endpoint. Requests that have no eligible endpoint fail visibly and use the application's normal retry behavior rather than relaxing the privacy policy. Required model parameters must be supported by the selected endpoint.

OpenRouter private input/output logging and use of inputs/outputs remain disabled at the account level. The OpenRouter API key is stored in Azure Key Vault. Derived AI records retain the exact requested model slug, actual upstream provider when available, request or generation identifier, token usage, and prompt or schema version.

## Consequences

- The backend uses one API credential and one gateway for text generation and embeddings.
- The selected model allocation and evaluation results remain meaningful because failures do not silently switch to another model.
- Same-model endpoint fallback can improve availability without intentionally changing model behavior.
- Diary text passes through OpenRouter and an eligible upstream provider, creating an additional external dependency and privacy boundary.
- Strict zero-data-retention and data-collection filters may reduce endpoint availability and cause otherwise serviceable requests to fail.
- Production account settings and per-request privacy fields both require deployment verification.
- OpenRouter pricing, model availability, routing metadata, and privacy behavior must be monitored for changes.
- Switching gateways later should remain localized behind the internal AI boundary, but it still requires regression evaluation and may require regenerating embeddings.
