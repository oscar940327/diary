# Isolate Synthetic Evaluation from Production

## Context

Diary stores private personal history, while its AI and retrieval behavior needs repeatable synthetic evaluation. Loading synthetic Entries into production would pollute the owner's RAG evidence, and running development reset or seed operations against production could destroy real records. A separately hosted staging stack would improve cloud parity but add cost and operational work to a permanently single-user MVP.

## Options

1. Share one hosted Supabase project between development, synthetic evaluation, and production, separating records with flags or schemas.
2. Maintain separate hosted staging and production Supabase and Azure resources.
3. Use local Supabase and Azurite for development and synthetic evaluation, with one owner-only hosted production environment for private acceptance and normal use.

## Decision

Development, automated testing, and synthetic evaluation use a local Supabase stack and Azurite. Production uses the hosted Supabase project, GitHub Pages frontend, and Azure backend resources and contains only real owner-created Entries. The MVP does not maintain a hosted cloud staging environment. Ordinary tests use fake AI Adapters; live OpenAI evaluation is explicit and runs only against local synthetic data.

## Consequences

- Synthetic records cannot appear as evidence in the owner's production RAG history.
- Environment URLs, credentials, and secret files must differ across `local`, `test`, and `production`.
- Seed and destructive reset tooling must detect and refuse production configuration.
- Local development requires a Docker-compatible container runtime, the Supabase CLI, and Azurite.
- Local emulators reduce cost but do not guarantee complete cloud parity.
- Private production acceptance includes an end-to-end smoke test covering authentication, Queue processing, AI Draft generation, retrieval, and citations.
- Cloud-specific failures may be discovered only after deployment, so rollback, retry, logs, and backup restore remain acceptance requirements.
