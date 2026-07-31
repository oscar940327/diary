# Diary

Diary is a personal, long-term system for capturing, retrieving, and analyzing the owner's records. The owner can add free-form text at any time, with multiple Entries per day and no required template.

## Domain language

**Entry**:
A stable record created by one user submission. Multiple Entries may belong to the same calendar day; editing an Entry creates an Entry Revision rather than another Entry.
_Avoid_: Daily note, diary page

**Entry Time**:
The user-selected date and time under which an Entry appears in the calendar and continuous history. It defaults to the current time but may be changed for a late or backdated Entry.
_Avoid_: Creation time

**Original Content**:
The user-authored free-form text belonging to an Entry, represented by immutable Entry Revisions and kept separate from all AI-derived content.
_Avoid_: AI input, summary

**Entry Revision**:
An immutable version of an Entry's Original Content. The newest revision is displayed by default, while earlier revisions remain available for history and restoration.
_Avoid_: Backup, AI Draft

**AI Draft**:
An AI-generated proposal containing a summary and structured interpretation of an Entry. It is derived content and does not replace Original Content.
_Avoid_: Final result, source record

**AI Correction**:
A user-authored correction to an AI Draft. When present, it is the version displayed and consumed in preference to the AI Draft.
_Avoid_: AI Draft, Original Content

**Insight Agent**:
The question-answering assistant that retrieves relevant Original Content and asks an LLM to synthesize a response grounded in those records. It is distinct from the future tool-using or reminder Agent.
_Avoid_: Search box, reminder Agent

**Conversation**:
A persistent multi-turn exchange with the Insight Agent. Prior messages provide conversational context, while personal evidence must still be retrieved from Original Content on every turn.
_Avoid_: Entry, evidence source

## Project goal

- Preserve personal records over the long term.
- Support records about learning, project progress, interviews and job searches, exercise, mood, productivity, temporary thoughts, and other topics without requiring a fixed input format.
- Make past records retrievable and analyzable without inventing evidence that is not present.

## Long-term direction

- Preserve the complete original content submitted by the user.
- Use AI to produce summaries and structured data from free-form Entries.
- Split records into personal-memory units suitable for retrieval.
- Use RAG to answer open-ended questions about the user's history.
- Cite relevant Entries and dates in answers.
- Explicitly state when the records do not provide sufficient evidence.
- Use scikit-learn to analyze long-term productivity and life patterns.
- Add an AI Agent that can use tools, including future reminder capabilities.
- Use a separate frontend and backend and eventually integrate the product into the user's existing personal website.
- The currently anticipated backend is FastAPI.
- The currently anticipated database is Supabase PostgreSQL, with pgvector as a possible future extension.

Items in this section are directions, not commitments to the first MVP.

## Confirmed decisions

- The product name is `Diary`; the personal website Sidebar presents it as `DIARY`.
- Entry capture accepts free-form text without a required template.
- Each successful submit action creates exactly one Entry.
- A user may create any number of Entries during the same day.
- Every Entry is stored independently; Entries from the same day are not merged into one daily document.
- The core relational model separates stable `entries` from immutable `entry_revisions`.
- An Entry stores its UUID, owner UUID, `entry_at`, current revision reference, creation/update timestamps, and optional trash timestamp.
- An Entry Revision stores its UUID, parent Entry, sequential revision number, complete content, and creation timestamp.
- Editing Original Content adds an Entry Revision to the same Entry; it does not create another Entry.
- `entry_at` stores the user-editable Entry Time and controls calendar grouping and ordering.
- `created_at` stores the immutable system capture time, while `updated_at` records the latest modification time.
- Timestamps are persisted as UTC. Calendar grouping, display, and the definition of today use the fixed owner timezone `Asia/Taipei`.
- The MVP does not automatically switch diary grouping to the browser's timezone; a backdated or travel Entry can be assigned by editing `entry_at`.
- Original Content is versioned as immutable Entry Revisions. Editing creates a new revision instead of overwriting an existing revision.
- AI Draft and AI Correction records are associated with the specific Entry Revision they interpret.
- After an Original Content edit, derived results from the previous revision become stale and are excluded from display and retrieval; a new AI Draft is produced for the new revision.
- The newest Entry Revision is displayed by default, and previous revisions remain available for inspection or restoration.
- Deleting an Entry moves it to a recoverable Trash instead of immediately destroying it.
- Trashed Entries are excluded from the history, calendar, search, RAG, AI processing, and analysis.
- Restoring an Entry returns it to normal use.
- Permanent deletion requires an explicit confirmation and removes the Entry, all Entry Revisions, all derived AI results, and all vector-index records.
- The MVP does not automatically purge Trash; permanent deletion is initiated manually by the owner.
- Diary is permanently a single-user product for its owner, not merely a single-user MVP.
- Public registration, additional accounts, sharing, collaboration, and role management are not planned.
- The application will be deployed as a website reachable over the public internet.
- Public deployment requires an owner-only authentication boundary; an unguessable URL is not considered access control.
- The owner must be able to open the personal website from a modern mobile browser, authenticate, and use the core Diary recording and history flows. This is responsive web support, not a native mobile application.
- Authentication uses Supabase Auth with one pre-created owner email and passwordless Magic Link or OTP.
- Public sign-up is disabled. `public.diary_owners` contains exactly one administratively provisioned row and is the authoritative permanent owner identity; the database rejects a second row.
- FastAPI reads the singleton owner registry with a backend-only Supabase secret and accepts protected requests only when the verified token subject matches that row. `DIARY_OWNER_ID` is not a second configuration source.
- PostgreSQL RLS independently compares the caller identity with the same owner row, preserving defense in depth even if either the API authorization path or a direct database path is misconfigured.
- Browser code may use only a Supabase publishable key. Supabase secret keys and AI provider keys remain in backend environment variables and are never exposed to the browser.
- The FastAPI backend is deployed to Azure Container Apps on the Consumption plan.
- Azure Container Apps uses `minReplicas = 0` and `maxReplicas = 1` so the single-user service can scale to zero, constrain cost, and accept cold starts.
- The preferred production region pair is Supabase Northeast Asia (Tokyo, `ap-northeast-1`) with all supported Azure backend resources in Japan East.
- Before provisioning, the deployment process verifies Japan East availability and quota for the Azure for Students subscription.
- If Japan East cannot host the required resources, the complete pair changes to Supabase Southeast Asia (Singapore, `ap-southeast-1`) and Azure Southeast Asia. The database and Azure backend are not intentionally split between Tokyo and Singapore.
- The Container Apps environment, FastAPI app, Container Apps Job, Storage Queue, backup Blob container, logs, and any required registry resources use the same selected Azure region where supported.
- Azure infrastructure is defined and reproduced with Bicep rather than relying on manual Azure Portal configuration.
- Bicep is the source of truth for supported Azure resource settings, and deployment previews use Bicep `what-if` before changes are applied.
- GitHub Actions authenticates to Azure through OIDC workload identity federation and short-lived credentials rather than a stored long-lived Azure client secret.
- Azure Portal is used for inspection, monitoring, and troubleshooting, not as the primary source of infrastructure configuration.
- The MVP does not introduce Terraform because its Azure-only infrastructure does not currently justify a second infrastructure-management ecosystem.
- Tests and immutable commit-SHA image builds run automatically, but they do not automatically release a new backend version to production.
- A production release requires the owner to start a GitHub Actions `workflow_dispatch` workflow and explicitly select the version being released.
- FastAPI uses Azure Container Apps multiple-revision mode for a blue-green release: a new revision is provisioned and checked before it receives production traffic.
- Production traffic moves to a new revision only after its startup, readiness, and smoke checks pass.
- The immediately previous known-good revision remains available at zero production traffic so the release workflow can quickly return all traffic to it.
- A failed pre-traffic verification leaves the existing production revision serving traffic. A detected post-release problem triggers a manual rollback workflow rather than rebuilding an old image.
- API and AI-processing workloads released together use the same immutable commit-SHA image version.
- Handoff must include an owner-oriented deployment and rollback runbook, plus a guided exercise in starting a release, identifying the active revision, reading failures, and restoring the previous revision.
- Supabase PostgreSQL schema changes are committed as ordered, versioned SQL migrations and are not performed as undocumented manual production edits.
- A release containing a production schema change creates and verifies an additional pre-migration logical backup before applying the migration.
- Production migrations follow an expand-contract policy: first add backward-compatible structures, deploy code that tolerates the transition, migrate or backfill data, and remove obsolete structures only in a later release.
- Destructive schema changes are not bundled into the release that first stops using the affected structure.
- The immediately previous application revision must remain compatible with the migrated schema so blue-green traffic rollback remains usable.
- Normal rollback switches application traffic and related workload versions but does not automatically run a down migration or restore the production database.
- Full database restore is reserved for disaster recovery because using it as an ordinary release rollback could discard Entries created after the backup.
- A failed migration stops the release before production traffic moves to the new revision; transactional migration behavior is used where PostgreSQL supports it.
- Production backend secrets are stored in Azure Key Vault Standard rather than committed files or direct secret values in Bicep parameter files.
- FastAPI, Container Apps Jobs, and other required Azure workloads read Key Vault secrets through managed identities with least-privilege access.
- Container Apps consumes Key Vault references as secret-backed environment variables; application code does not receive credentials for accessing Key Vault.
- Versionless Key Vault references are used where automatic rotation is appropriate, with deployment verification covering secret refresh and workload restart behavior.
- The initial deployment guide must identify which values require manual secure bootstrap, and secret rotation must not require modifying tracked source files.
- The backend source repository and its GitHub Container Registry image remain private during the MVP.
- GitHub Actions builds the backend image and tags it with the immutable Git commit SHA. Deployment does not rely on the mutable `latest` tag.
- Azure Container Apps pulls the private GHCR image with a dedicated credential limited to package-read access and stored as an Azure secret.
- The MVP does not create Azure Container Registry. Registry cost and policy are reconsidered only if GHCR no longer meets the project's security or cost needs.
- Container image privacy does not make the website private: FastAPI uses public HTTPS ingress so the GitHub Pages frontend and mobile browsers can reach it, while every personal-data operation still requires a valid owner token.
- The Diary frontend is integrated as a first-class page in the owner's existing `personal_website` repository and is hosted by its existing GitHub Pages deployment.
- The MVP continues to use the existing GitHub Pages HTTPS URL at `https://oscar940327.github.io/my-personal-website/` and does not require purchasing or configuring a custom domain.
- FastAPI uses the HTTPS FQDN generated by Azure Container Apps; the generated API hostname is application configuration and is not a URL the owner normally enters.
- Supabase Auth redirect URLs and production CORS use the exact GitHub Pages origin and Diary route as appropriate.
- A future custom website or API domain is a reversible post-MVP change that requires coordinated DNS, TLS, CORS, Supabase redirect, and frontend API-base updates.
- The Sidebar label is `DIARY` and appears immediately below `JOURNEY` and above `MktAgent`.
- The Diary page renders the application directly and does not embed a separately hosted application through an iframe.
- The existing personal website, MktAgent, and VideoNote remain on their current vanilla HTML/CSS/JavaScript approach. They are not migrated or refactored as part of the Diary MVP.
- Only the Diary page body is implemented as a React and TypeScript application built with Vite and mounted inside the existing static page shell.
- The GitHub Pages deployment builds the Diary assets while publishing the existing static pages unchanged. Vite's base path must match the `my-personal-website` repository path.
- GitHub Pages serves only public frontend assets, the Supabase publishable key, and the public Azure API base URL. All secrets remain in backend environment variables.
- The browser authenticates with Supabase Auth and sends the Supabase access token to the Azure-hosted FastAPI API. FastAPI validates the token and the authoritative singleton owner identity on every protected request.
- Production CORS permits only the exact GitHub Pages origin or an explicitly configured future custom origin; local development origins are configured separately.
- FastAPI persists the Entry Revision and enqueues its ID in Azure Storage Queue before returning success.
- An event-driven Azure Container Apps Job consumes queued AI work, with zero minimum executions and at most one concurrent execution.
- Queue messages and database constraints make AI job creation idempotent for each Entry Revision.
- Azure spending is constrained by the annual Azure for Students credit; non-Azure services such as Supabase and an external AI API have separate costs.
- The Diary Azure resource group has an initial USD 5 monthly Cost Management budget with owner email notifications at 50, 80, and 100 percent; this budget is an alert and not an automatic resource shutdown.
- The Azure for Students spending limit remains enabled and the project must not automatically upgrade the subscription to pay-as-you-go.
- Production OpenRouter usage uses a dedicated API key with an initial USD 5 monthly hard limit and no automatic credit top-up.
- Explicit live-model evaluation uses a separate OpenRouter API key with an initial USD 1 monthly hard limit so test usage cannot exhaust the production AI allowance.
- Reaching an OpenRouter limit must not prevent saving, viewing, editing, exporting, or text-searching Original Content; only AI-dependent processing and answers may become unavailable.
- Supabase production initially uses the Free Plan and does not add a payment method or paid upgrade as part of the MVP deployment.
- Supabase usage is reviewed at 60, 80, and 90 percent of applicable Free Plan quotas. Approaching a limit triggers a capacity review rather than an automatic paid upgrade.
- Operations documentation covers recognizing and manually resuming a low-activity paused Supabase Free project.
- The initial cost limits are deliberately conservative and may be changed only by an explicit owner decision informed by observed usage.
- Production application logs use structured `INFO` events and keep `DEBUG` logging disabled by default.
- Logs may contain UTC timestamps, random request correlation IDs, route templates, response status and duration, opaque Job, Entry, and Entry Revision UUIDs, AI state, exact model and upstream provider identifiers, token and cost metadata, sanitized error types, retry counts, queue delay, and deployment commit SHA.
- Logs must never contain Original Content, Entry Revision content, AI Drafts, AI Corrections, Agent questions or answers, RAG prompts or evidence, citation excerpts, HTTP bodies, owner email, Magic Links, OTPs, JWTs, cookies, authorization headers, API keys, database credentials, connection strings, complete query strings, environment-variable values, or unsanitized third-party error bodies.
- External-service exceptions and stack traces are sanitized before logging so provider messages cannot echo diary content, prompts, secrets, or request parameters.
- Azure Log Analytics stores production Container Apps system and sanitized console logs for 30 days and uses an initial 0.1 GB daily ingestion safety cap with owner notification.
- The Log Analytics daily cap is an emergency spike safeguard, not the primary filtering mechanism; reaching it may make the system temporarily unobservable.
- The MVP does not enable Application Insights. Additional telemetry is reconsidered only if sanitized structured logs cannot diagnose production problems.
- Production log access is limited to the owner's Azure administration identity. Operational logs are excluded from diary exports and long-term backup archives.
- Deployment acceptance writes unique synthetic content and fake-secret markers through test paths, searches collected Azure logs, and requires that none of those marker values appear.
- Final MVP acceptance includes automated functional and fixed synthetic AI evaluation, with zero Critical AI errors and no unresolved Critical runtime dependency or container-image vulnerability.
- Repository and built frontend secret scans must find no real credential, and the browser bundle may contain only the Supabase publishable key and public API configuration.
- Production infrastructure acceptance verifies selected-region availability and quota, reviewed Bicep `what-if` output, Azure budget alerts, Key Vault references, managed-identity permissions, Queue and Job configuration, Blob lifecycle, Log Analytics retention and cap, exact CORS, disabled public sign-up, owner-only RLS, and unauthenticated `401` or `403` behavior.
- Release acceptance verifies a commit-SHA private GHCR image, pre-migration backup when applicable, successful Green revision startup and readiness, protected API smoke tests, matching API and AI Job image versions, and an intentional traffic promotion.
- Production product acceptance covers desktop and mobile owner login, Entry CRUD, continuous date history, calendar navigation, revisions, Trash, direct search, export, asynchronous AI Draft and AI Correction preservation, Insight Agent retrieval, exact citations, and insufficient-evidence behavior.
- AI-provider acceptance verifies exact OpenRouter model slugs, zero-data-retention and data-collection restrictions, no cross-model fallback, separate production and evaluation key limits, and disabled automatic top-up.
- Recovery acceptance verifies backup restoration into an independent test database, embedding reconstruction, idempotent duplicate Queue delivery, locally simulated `blocked_budget` recovery, and an actual blue-green traffic rollback exercise.
- MVP handoff includes owner-oriented Azure deployment, backup and restore, rollback, OpenRouter credit and limit, AI backlog recovery, and Supabase resume runbooks.
- The owner completes a guided production exercise that starts a release, identifies the active revision, reads a failed check or log, verifies backup and budget state, and returns traffic to the previous revision.
- A completed production handoff checklist records the deployed commit SHA, infrastructure verification, product acceptance, recovery exercises, known limitations, and runbook locations.
- The MVP uses OpenRouter as the single API gateway for AI Draft generation, embeddings, and Insight Agent answers; application workloads do not call OpenAI directly.
- The OpenRouter API key is stored in Azure Key Vault and is never exposed to the frontend or committed configuration.
- Exact OpenRouter model slugs are configured through backend environment variables rather than hard-coded in application logic.
- The default quality-balanced model allocation is `openai/gpt-5.4-mini` for AI Draft generation, `openai/gpt-5.6-luna` for Insight Agent answers, and `openai/text-embedding-3-small` for embeddings.
- Production does not use mutable model aliases such as `latest`.
- OpenRouter must not automatically fall back from a configured model to a different model. Provider fallback is allowed only for the same exact model and only among endpoints that satisfy the project's privacy and parameter requirements.
- Every production OpenRouter request denies provider data collection and requires a zero-data-retention endpoint. If no eligible endpoint is available, processing fails visibly and follows the existing retry behavior rather than weakening privacy restrictions.
- OpenRouter private input/output logging and OpenRouter use of inputs/outputs remain disabled at the account level.
- Each derived AI result records the requested exact model slug, actual upstream provider when available, request or generation identifier, token usage, and prompt or schema version.
- Narrow internal AI boundaries must permit a future gateway or provider change without altering the domain model.
- The project prefers measured quality over either the cheapest or the strongest model by default. A model is upgraded only when representative Chinese diary and Agent evaluations show that the current model does not meet the agreed acceptance threshold.
- Model upgrades are scoped to the failing workload: AI Draft, Insight Agent answer generation, and retrieval embeddings are evaluated and changed independently.
- The project maintains a fixed, manually designed synthetic evaluation dataset that contains no real personal data and is not copied from the owner's diary or from third-party records.
- Synthetic evaluation Entries cover the product's diary domains and deliberately exercise short, long, multi-topic, ambiguous, mixed-language, date-sensitive, and proper-noun inputs.
- Each synthetic case defines required source facts, prohibited inventions, acceptable categories, and related Agent questions with expected evidence or expected abstention.
- Synthetic evaluation data is loaded only into an isolated test database and must never enter the production database or the owner's RAG history.
- Real diary content may be used for private manual acceptance but must not be committed to Git or copied into automated test fixtures.
- Local development and automated evaluation run against a local Supabase stack started through the Supabase CLI and a Docker-compatible container runtime.
- Azure Queue and Blob behavior is exercised locally through Azurite. The local emulators are never exposed as production services.
- The MVP has no separately hosted cloud staging environment. The only hosted environment is the owner-only production environment.
- Ordinary automated tests use deterministic fake AI Adapters and do not call OpenAI. A live-model evaluation must be explicitly enabled and uses only synthetic data in the local test environment.
- Environment configuration distinguishes `local`, `test`, and `production`, with different URLs, credentials, and secret files.
- Any synthetic-data seed or destructive database-reset operation must refuse to run when configured for production.
- Private owner acceptance runs in production using real owner-created Entries, followed by an end-to-end smoke test of Queue processing, AI Draft generation, retrieval, and citations.
- MVP completion uses two gates: a deployment-ready system gate against fixed synthetic data, followed by private owner acceptance against representative real diary use.
- The deployment-ready gate covers Entry creation, display, search, editing, revision restore, Trash and restore; asynchronous AI states and retry; grounded retrieval, exact-revision citations, and insufficient-evidence behavior; owner-only authentication and authorization; portable export; backup restore; and zero Critical AI errors.
- A Critical AI error is an invented personal event or fact, an incorrect citation, or a claim that personal evidence exists when the records do not support it.
- Private owner acceptance exercises at least one real short, long, multi-topic, and mixed-language Entry, plus direct fact, time-range, cross-record synthesis, planning/advice, and insufficient-evidence Agent questions.
- Private owner acceptance also verifies AI Correction preservation, calendar-to-history navigation, continuous date scrolling, and citation navigation using the owner's real writing style.
- Private owner acceptance verifies that login, new Entry creation, history navigation, and Entry viewing work in a modern mobile browser.
- The coverage counts are requirement-based smoke coverage, not statistical quality claims. Real acceptance data remains private in the deployed database.
- Settings provides a portable JSON/ZIP export containing Entries, all Entry Revisions, AI Drafts, AI Corrections, categories, tags, Conversations, messages, and citations.
- Portable export excludes credentials, API keys, and rebuildable embeddings.
- A scheduled Azure Container Apps Job creates one logical database backup per day and stores it in a private Azure Blob Storage container.
- Azure Blob lifecycle management retains the latest 30 daily backups and deletes older backup blobs.
- Operational backups retain all non-rebuildable user and Agent data but exclude embeddings and transient queue/job state.
- Restore rebuilds embeddings from active Original Content and requeues any required unfinished derived processing.
- MVP acceptance requires successfully restoring a backup into a separate test database and verifying representative data.
- The primary frontend experience must let the user access both today's Entries and all previous Entries at any time.
- The history view is a continuously scrollable view that groups Entries by date and displays their content across adjacent days.
- The calendar is an alternative way to navigate all Entries. Selecting a calendar date switches to the continuous date-grouped history positioned at that date; scrolling continues into adjacent dates.
- The continuous history is reverse chronological: newer dates are above older dates.
- The default position is today. Scrolling downward reveals older dates, while scrolling upward from a past date reveals newer dates.
- The client incrementally loads adjacent date groups near either scroll boundary instead of downloading the full history at once.
- Every loaded Entry displays its complete Original Content.
- A global new-Entry action is available from both the continuous history and calendar.
- The new-Entry composer opens without leaving the current browsing position, accepts free text, and defaults `entry_at` to the current `Asia/Taipei` time.
- A backdated Entry requires an intentional date/time change. Saving while browsing a past date does not silently assign that viewed date.
- After saving, the current browsing position is preserved and the UI offers an action to view the new Entry.
- Blank Entries are rejected, and desktop clients may submit with `Ctrl/Cmd + Enter`.
- Direct Entry search and the Insight Agent are separate frontend actions.
- Direct search uses the same hybrid retrieval foundation but returns Entry results without invoking the answer-generation LLM.
- Direct search supports date, category, and tag filters and navigates from a result to the Entry in the continuous history.
- Insight Agent questions invoke retrieval and answer generation and are stored in Conversations.
- Each Entry exposes a compact action menu for editing Original Content, changing Entry Time, viewing revision history, and moving the Entry to Trash.
- Editing Original Content opens a dedicated editor and creates a new Entry Revision.
- Changing Entry Time updates `entry_at` without creating an Original Content revision.
- Restoring historical Original Content creates a new current Entry Revision rather than deleting or rewriting revision history.
- AI Correction editing and AI Draft regeneration are exposed inside the Entry's AI section.
- Trash provides restore and separately confirmed permanent-delete actions.
- Original Content, AI Draft, and AI Correction are separate concepts.
- A user can correct an AI Draft. The AI Correction is stored separately and takes precedence.
- Regenerating an AI Draft must not overwrite an AI Correction without the user's approval.
- Each Entry in the continuous history displays its complete Original Content, followed by a compact, collapsible, and editable AI Draft or AI Correction.
- The user-visible AI Draft contains only `summary`, `categories`, and `tags`.
- `summary` is a short one-to-three-sentence description.
- `categories` is a multi-select field using the controlled values learning, project progress, interviews and job search, exercise, mood, productivity, temporary idea, and other.
- `tags` is a free-form list for specific topics such as a technology, project, activity, or interview.
- An AI Correction can edit the same three fields.
- Saving an Entry Revision completes before AI processing and never waits for an AI response.
- Every new Entry Revision automatically schedules asynchronous AI processing.
- AI processing exposes `pending`, `processing`, `ready`, `failed`, and `blocked_budget` states.
- An AI failure never invalidates or hides Original Content.
- A failed AI job is retried automatically once; after a second failure, the Entry exposes a manual retry action.
- Only one active AI-processing job may exist for the same Entry Revision.
- An OpenRouter account-credit or API-key-limit error moves affected processing to `blocked_budget` rather than consuming the ordinary failure retry count.
- After a budget block is detected, a shared budget pause prevents workers from repeatedly calling OpenRouter; new AI work remains durably recorded for later processing.
- Entries affected by a budget pause display that AI processing is waiting for budget recovery, while all non-AI Entry operations remain available.
- The Settings UI provides a manual `Check budget and resume AI` action after the owner adds OpenRouter credit, raises the production key limit, or waits for its monthly UTC reset.
- Resume checks the current production API key's reported limit state without storing an OpenRouter Management Key. The first bounded work attempt validates account-credit availability; another budget error immediately pauses processing again.
- Recovery requeues only the current revision of each non-trashed Entry that lacks required AI Draft or embedding work. Historical revisions, superseded jobs, and trashed Entries are not processed.
- Budget recovery is idempotent, processes newer affected Entries first, and eventually completes the entire eligible backlog without creating duplicate AI results.
- The UI reports the number of eligible Entries still waiting or processing during recovery.
- Insight Agent personal-history answers remain unavailable while any eligible current Entry is missing its required embedding because otherwise a negative or incomplete answer could be mistaken for a full-history result.
- Insight Agent is automatically available again when the eligible embedding backlog reaches zero; direct Original Content text search remains available throughout recovery.
- The application never changes the OpenRouter spending limit, purchases credit, or enables automatic top-up. Those actions require an explicit owner change in OpenRouter.
- Editing Original Content makes derived results for the previous revision stale and schedules the new revision for processing.
- When semantic retrieval is implemented, embeddings are created from Original Content only.
- AI Draft and AI Correction fields may be used as retrieval metadata, but they are not independent evidence for an answer.
- Only the current Entry Revision of a non-trashed Entry participates in normal retrieval.
- Previous Entry Revisions remain in PostgreSQL but are excluded from the active RAG index.
- A short Entry is indexed as one chunk. A long Entry is split at paragraph boundaries, with oversized paragraphs split into roughly 500-800-token chunks with limited overlap.
- Chunks from different Entries are never merged, even when the Entries share a date.
- Each chunk carries its Entry ID, Entry Revision ID, Entry Time, chunk position, categories, and tags.
- Retrieval searches the full active history by default. Explicit temporal language in the question may add a date-range filter.
- After a chunk match, the Insight Agent may load the complete current Original Content of that Entry before answering.
- Retrieval combines `pgvector` semantic similarity with `pg_trgm` text matching.
- Reciprocal Rank Fusion merges semantic and text-match rankings before evidence is supplied to the LLM.
- Mixed Chinese, English, and exact technical or project names must be covered by retrieval evaluation.
- Date, category, and tag filters are applied only when the question explicitly or reliably implies them.
- The MVP does not add a separate LLM reranker.
- Scikit-learn models, productivity trend analysis, and analytics dashboards are excluded from the MVP.
- Exploratory ML may be reconsidered only after at least 90 calendar days from the first Entry and Entries on at least 60 distinct active days.
- Reaching the 90-day threshold triggers a data-quality and target-definition review; it does not automatically approve an ML feature.
- Predictive productivity models require at least 180 days of history and an explicitly defined, user-provided outcome.
- RAG answers must be grounded in retrieved Original Content and cite the corresponding Entry and date.
- When retrieved Original Content is insufficient, the system must explicitly state that the records do not provide enough evidence.
- RAG and the Insight Agent are core MVP capabilities, not deferred long-term enhancements.
- Every Insight Agent question first runs retrieval against the owner's Original Content, then supplies the retrieved evidence to an LLM for synthesis.
- The Insight Agent supports open-ended requests that combine multiple past experiences, such as preparing for an interview based on previous interview and project Entries.
- Insight Agent responses separate record-grounded statements, cross-record inferences, and general LLM advice.
- Record-grounded statements cite the supporting Entry and date.
- Cross-record inferences are explicitly labeled as inferences.
- General advice is allowed but is explicitly labeled as not coming from personal records.
- If retrieval finds insufficient personal evidence, the response says so before offering any general advice.
- The Insight Agent must never present general knowledge or an inference as an experience the owner actually recorded.
- The Insight Agent supports persistent multi-turn Conversations that can be revisited and continued.
- Conversation messages and their citations are stored.
- Every user turn performs retrieval again; previous Agent answers may clarify conversational references but are never treated as evidence about the owner.
- The full Conversation remains available in the UI, while the LLM receives only context that fits the configured token budget.
- Deleting a Conversation does not delete any cited Entry.
- Record-grounded statements use inline numbered citations and a source list containing Entry Time and a short Original Content excerpt.
- Selecting a citation opens the complete cited Entry Revision and offers navigation to the Entry in the date-grouped history.
- Citation metadata stores both Entry ID and the exact Entry Revision ID used to generate the answer.
- If a cited Entry later receives a newer revision, the old answer still shows the cited snapshot and indicates that a newer revision exists.
- Multiple matched chunks from the same Entry Revision collapse into one visible citation.
- Core ambiguities must be resolved before implementation begins.
- Confirmed decisions are documented during the design discussion.

## Open questions

- None at the MVP-definition level. Minor implementation details may be resolved in the specification only when they do not change a confirmed product or architecture decision.

## Current MVP boundary

The MVP is a publicly reachable but owner-only web application, so unauthenticated access to personal records and mutation APIs is prohibited. It uses Supabase Auth with a single pre-created owner identity, passwordless email login, and no public sign-up. Secrets remain on the backend. FastAPI runs on Azure Container Apps Consumption with scale-to-zero and at most one replica. Original Content is saved and displayed before automatic asynchronous AI processing; AI failures are visible and retryable but never invalidate an Entry. The product includes a continuously scrollable, date-grouped history that displays the complete Original Content of each Entry across adjacent days. A calendar provides an alternative view and navigation method: selecting a date switches to the continuous history at that position. Each Entry places its compact, collapsible, and editable AI Draft or AI Correction below the Original Content. User correction must not overwrite Original Content or silently replace a prior AI Correction. The MVP also includes an Insight Agent that retrieves Original Content with RAG before asking an LLM to synthesize a cited answer. Other long-term capabilities must not be treated as MVP requirements until explicitly selected.

## Explicitly out of scope

- Public user registration
- Multiple user accounts
- Sharing Entries with other users
- Collaboration features
- Role and permission management
- AI-generated productivity scores
- AI-generated mood scores
- AI-generated task lists or completion states
- Scikit-learn models
- Productivity or life-pattern analytics dashboards
- Proactive reminders, schedules, email notifications, and push notifications
- An Agent that invokes external tools or performs actions in other services
- Live web browsing or web search by the Insight Agent
- Images, file attachments, voice input, and speech-to-text
- Native iOS or Android applications
- Offline mode and offline synchronization
- Automatic Trash purging
- A separate LLM reranker
- AI modification of Original Content
- Migration or refactoring of the existing HOME, PROJECT, JOURNEY, MktAgent, or VideoNote implementations

## Next item

Ticket 05 calendar navigation and its review-finding fixes are awaiting a new
fixed-range code-review session. The latest blocking finding was test-only:
the Calendar midnight browser regression installed a running fake clock at
`2026-04-30 23:59:59 Asia/Taipei`, so authentication, routing, and page setup
could consume the final second before the initial April assertions. A red run
of the unchanged test with `--repeat-each=20 --workers=4` produced 12 passes
and 8 failures, all waiting for the missing initial `April 2026` view.

The regression now pauses the installed fake clock at April 30 before any page
setup. Only explicit `runFor`/`fastForward` calls advance it. The same repeated
concurrent command is green 20/20 and still verifies April 2026, April 30 as
Today, the explicit transition to May 2026, May 1 as Today, the `2026-05`
Calendar request, preservation of an owner-browsed April across the next
midnight, and May 2 as Today after returning to May. No Calendar production
implementation changed.

Personal Website verification is green: typecheck passed, all 18 Chromium E2E
tests passed, the production build and built-site verification passed, and
`git diff --check` passed. Diary verification is green: mypy passed for 18
source files, pytest passed 52 tests with the existing Starlette/httpx warning,
the local Supabase reset applied all eight ordered migrations, schema lint
returned no findings, and `git diff --check` passed. Diary CI pins Personal
Website commit `ab99cf8a101e2d0a294a6b1be740ed18b0207e47` through pin commit
`59e3ae6282c5e6fc4e0abaa65f8a6bc7b28a7194`.

The next fixed-range review starts at Diary
`891636e3c680a0bb7f032e64a0f779210302ff44` and Personal Website
`4bebbb5301260a4f1fa1a4ea594d2904e5243c13`. Its Personal Website endpoint is
`ab99cf8a101e2d0a294a6b1be740ed18b0207e47`; its Diary endpoint is the commit
containing this documentation record, whose immutable SHA is reported as the
final local Diary HEAD in the session handoff. Ticket 06 has not started and
must wait for Ticket 05 to pass that review.
