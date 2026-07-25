# Diary MVP

Status: ready-for-agent

## Problem Statement

The owner needs one durable place to capture personal records throughout the day without fitting them into a daily template or limiting each day to one note. Those records must remain readable as originally written, be easy to browse by date or search directly, and remain correctable without losing history.

The owner also needs the accumulated record to become useful as personal memory. AI should propose concise structured interpretations without replacing Original Content, and an Insight Agent should answer open-ended questions by retrieving relevant records, citing the exact evidence it used, distinguishing recorded facts from inference and general advice, and clearly admitting when the record is insufficient.

The system will contain irreplaceable and private material but will be reachable from the public internet and operated under a small student budget. It therefore needs owner-only authentication, explicit privacy boundaries, recoverable edits and deletion, portable export, tested backup restoration, controlled AI spending, reproducible deployment, and an operating procedure the owner can follow from both desktop and mobile.

## Solution

Build Diary as an owner-only web application integrated into the existing GitHub Pages personal website. The Diary page body is a React and TypeScript application built with Vite, while the existing site shell and existing pages remain unchanged. The browser authenticates through Supabase Auth and calls a separately deployed FastAPI API on Azure Container Apps.

Each submission creates an independent Entry whose complete Original Content is represented by immutable Entry Revisions. Entries are presented in a reverse-chronological, continuously scrollable history grouped by `Asia/Taipei` calendar date, with a calendar as an alternative navigation method. Editing Original Content creates another revision; changing Entry Time does not. Trash is recoverable, and permanent deletion is explicit.

Every current Entry Revision is saved before AI work begins. An Azure Queue and event-driven Container Apps Job asynchronously generate an AI Draft and retrieval embeddings through OpenRouter. AI Drafts contain only a short summary, controlled categories, and free-form tags. An AI Correction is stored separately and takes precedence without changing Original Content. Budget exhaustion pauses AI work safely and allows the eligible backlog to be resumed later.

Direct search returns matching Entries without answer generation. The Insight Agent performs hybrid retrieval over current, non-trashed Original Content using `pgvector`, `pg_trgm`, and Reciprocal Rank Fusion, then asks the configured model to synthesize a response. Answers bind citations to exact Entry Revisions and separate record-grounded statements, cross-record inferences, and general advice.

Production uses Supabase PostgreSQL, Azure Container Apps Consumption, Azure Storage Queue and Blob, private GHCR images, Azure Key Vault, Bicep, GitHub Actions OIDC, sanitized Log Analytics logging, scheduled logical backups, and manually promoted blue-green releases. The MVP is accepted through fixed synthetic system evaluation, private owner acceptance, recovery exercises, and an owner-oriented deployment handoff.

## User Stories

1. As the owner, I want to submit free-form text without completing a template, so that I can record thoughts immediately.
2. As the owner, I want every successful submit action to create one independent Entry, so that separate moments are not merged accidentally.
3. As the owner, I want to create multiple Entries on the same day, so that I can record events whenever they happen.
4. As the owner, I want blank submissions rejected, so that accidental empty Entries do not pollute my history.
5. As the owner on desktop, I want to submit with `Ctrl/Cmd + Enter`, so that frequent recording is fast.
6. As the owner, I want the new-Entry composer available from both history and calendar views, so that navigation does not block capture.
7. As the owner, I want the composer to open without replacing my current browsing position, so that I can continue reading where I left off.
8. As the owner, I want a new Entry to default to the current `Asia/Taipei` date and time, so that ordinary capture needs no date editing.
9. As the owner, I want to set a different Entry Time intentionally, so that late and backdated records appear on the correct date.
10. As the owner, I want browsing a past date not to backdate a new Entry automatically, so that context does not silently change saved data.
11. As the owner, I want a direct action to view the Entry I just saved, so that I can verify it without losing my prior browsing position.
12. As the owner, I want Original Content saved before any AI call, so that AI latency or failure never loses my writing.
13. As the owner, I want today's Entries and all prior Entries available in one history, so that the system feels like a continuous diary.
14. As the owner, I want history grouped by date, so that I can understand when each record belongs.
15. As the owner, I want complete Original Content visible in history, so that I do not have to open every Entry to read it.
16. As the owner, I want newer dates above older dates, so that the default order matches recent-first review.
17. As the owner, I want history to open at today by default, so that current recording is immediately visible.
18. As the owner, I want to scroll downward from today into older dates, so that I can review the past continuously.
19. As the owner, I want to scroll upward from a past date into newer dates, so that calendar jumps do not trap me in one direction.
20. As the owner, I want adjacent dates loaded incrementally, so that a long history does not require downloading every Entry at once.
21. As the owner, I want newly loaded date groups to preserve my visual scroll anchor, so that bidirectional loading does not make the page jump.
22. As the owner, I want a calendar showing which dates have Entries, so that I can navigate history spatially.
23. As the owner, I want to choose a calendar date and enter the continuous history at that date, so that calendar and history are two views of the same records.
24. As the owner, I want scrolling to continue across adjacent dates after a calendar jump, so that the selected date is an anchor rather than a separate page.
25. As the owner, I want calendar counts or presence indicators derived from non-trashed Entries, so that the calendar reflects active history.
26. As the owner, I want Entry dates and the meaning of today fixed to `Asia/Taipei`, so that mobile or travel timezone changes do not regroup my diary unexpectedly.
27. As the owner, I want the capture time retained separately from Entry Time, so that I can distinguish when I wrote a backdated record.
28. As the owner, I want to edit Original Content, so that I can correct or expand what I wrote.
29. As the owner, I want an Original Content edit to create a new Entry Revision, so that previous text is not overwritten.
30. As the owner, I want to see the current Entry Revision by default, so that history reflects my latest correction.
31. As the owner, I want to inspect prior Entry Revisions, so that I can audit how an Entry changed.
32. As the owner, I want to restore a prior revision by creating a new current revision, so that restoration does not rewrite history.
33. As the owner using two devices, I want a conflicting stale edit rejected clearly, so that one device cannot silently overwrite a newer revision.
34. As the owner, I want to change Entry Time without creating an Original Content revision, so that metadata changes are not confused with text changes.
35. As the owner, I want changing Entry Time to move the Entry to the correct date group, so that calendar navigation stays accurate.
36. As the owner, I want to move an Entry to Trash, so that accidental or unwanted records disappear without immediate destruction.
37. As the owner, I want trashed Entries excluded from history, calendar, search, RAG, AI processing, and analysis, so that deleted material does not influence normal use.
38. As the owner, I want to browse Trash separately, so that I can review removed Entries.
39. As the owner, I want to restore an Entry from Trash, so that deletion mistakes are recoverable.
40. As the owner, I want permanent deletion to require a separate explicit confirmation, so that destructive action is deliberate.
41. As the owner, I want permanent deletion to remove all revisions, AI results, citations' live navigation targets, and retrieval-index records belonging to the Entry, so that the Entry is actually destroyed.
42. As the owner, I want old Agent answers that cited a permanently deleted Entry to remain intelligible without exposing deleted content, so that conversation history does not falsely present a live source.
43. As the owner, I want Trash retained until I choose permanent deletion, so that the system does not impose an automatic purge deadline.
44. As the owner, I want each saved current Entry Revision to schedule AI processing automatically, so that structured records require no extra action.
45. As the owner, I want AI processing to happen asynchronously, so that saving an Entry remains responsive.
46. As the owner, I want visible `pending`, `processing`, `ready`, `failed`, and `blocked_budget` states, so that I understand what the AI is doing.
47. As the owner, I want the AI Draft to appear below Original Content, so that derived interpretation never replaces my writing.
48. As the owner, I want the AI section compact and collapsible, so that complete Original Content remains visually primary.
49. As the owner, I want an AI Draft summary of one to three sentences, so that it is useful without becoming another long diary.
50. As the owner, I want an AI Draft to choose one or more controlled categories, so that records can be filtered consistently.
51. As the owner, I want categories limited to learning, project progress, interviews and job search, exercise, mood, productivity, temporary idea, and other, so that category meaning does not drift.
52. As the owner, I want free-form tags for specific technologies, projects, activities, and interview topics, so that details are searchable without expanding the category list.
53. As the owner, I want the AI Draft to avoid invented scores, tasks, or completion states, so that it does not impose unsupported judgments.
54. As the owner, I want to correct the AI summary, categories, and tags, so that the structured interpretation can match my intent.
55. As the owner, I want an AI Correction stored separately from both Original Content and the AI Draft, so that each concept remains traceable.
56. As the owner, I want an AI Correction to take precedence in display and metadata use, so that my interpretation wins.
57. As the owner, I want regenerating an AI Draft not to overwrite my AI Correction, so that a model retry cannot erase my work.
58. As the owner, I want an explicit choice before discarding an AI Correction in favor of a regenerated Draft, so that precedence never changes silently.
59. As the owner, I want editing Original Content to make the previous revision's AI result stale, so that derived content never describes different text.
60. As the owner, I want the new current revision to receive a new AI Draft and embedding, so that display and retrieval follow current Original Content.
61. As the owner, I want a transient AI failure retried automatically once, so that temporary outages usually recover without intervention.
62. As the owner, I want a manual retry action after a second ordinary failure, so that repeated failures remain visible and controllable.
63. As the owner, I want duplicate Queue delivery not to create duplicate Drafts or embeddings, so that infrastructure retries are safe.
64. As the owner, I want an OpenRouter credit or key-limit failure treated as a budget block rather than an ordinary failure, so that it does not waste the normal retry allowance.
65. As the owner, I want AI calls paused after a budget block, so that the Queue does not create a costly retry storm.
66. As the owner, I want new Entries recorded while AI is budget-blocked, so that cost limits never block journaling.
67. As the owner, I want affected Entries labeled as waiting for AI budget recovery, so that missing Drafts are explained.
68. As the owner, I want to see how many current Entries are waiting for AI recovery, so that backlog size is visible.
69. As the owner, I want a Settings action to check budget and resume AI, so that I can recover after adding credit, raising the key limit, or waiting for reset.
70. As the owner, I want recovery to process newer eligible Entries first and eventually process the entire backlog, so that recent records become useful quickly without abandoning older ones.
71. As the owner, I want recovery to ignore trashed and superseded revisions, so that money is not spent on inactive content.
72. As the owner, I want another budget error to pause recovery immediately, so that one failed recovery attempt does not loop.
73. As the owner, I want the application unable to buy credit, enable automatic top-up, or raise its own key limit, so that spending changes always require my external approval.
74. As the owner, I want direct text search available during AI budget blocks, so that my Original Content remains findable.
75. As the owner, I want the Insight Agent withheld while any active Entry lacks its required embedding, so that an incomplete index is not presented as full-history evidence.
76. As the owner, I want the Insight Agent to return automatically after the eligible embedding backlog reaches zero, so that recovery requires no second manual switch.
77. As the owner, I want direct Entry search separate from the Insight Agent, so that simple lookup does not spend answer-generation tokens.
78. As the owner, I want direct search to combine semantic and exact-text matching, so that both meaning and specific names can be found.
79. As the owner, I want date, category, and tag filters in direct search, so that I can narrow results intentionally.
80. As the owner, I want search results to show the matching Entry and date, so that I can judge relevance.
81. As the owner, I want a search result to navigate to the Entry in continuous history, so that search reconnects to surrounding context.
82. As the owner, I want mixed Chinese and English records searchable, so that technical vocabulary does not break retrieval.
83. As the owner, I want exact project, company, technology, and person names discoverable, so that semantic similarity does not hide literal matches.
84. As the owner, I want retrieval limited to current revisions of non-trashed Entries, so that stale or removed content does not become normal evidence.
85. As the owner, I want short Entries retrieved as one coherent unit, so that brief notes are not fragmented unnecessarily.
86. As the owner, I want long Entries split primarily at paragraph boundaries, so that retrieved memory units preserve meaning.
87. As the owner, I want chunks from different Entries never merged, so that evidence remains attributable to one source.
88. As the owner, I want Agent retrieval to search my full active history by default, so that old relevant experience is not ignored.
89. As the owner, I want an explicit time expression in my question to narrow retrieval, so that questions about a period use the intended records.
90. As the owner, I want a matched chunk to allow loading its complete Entry, so that the Agent can answer with full local context.
91. As the owner, I want to ask open-ended questions about my personal history, so that accumulated records become practical memory.
92. As the owner preparing for an interview, I want the Agent to retrieve my prior projects and interview experiences before advising me, so that preparation reflects my actual background.
93. As the owner, I want every Agent turn to perform retrieval again, so that follow-up answers do not treat an earlier AI answer as personal evidence.
94. As the owner, I want persistent Conversations, so that I can revisit and continue prior reasoning.
95. As the owner, I want the full Conversation visible even when only a bounded context is sent to the model, so that interface history is not lost to token limits.
96. As the owner, I want Conversation messages and their citations stored, so that prior answers remain auditable.
97. As the owner, I want to delete a Conversation without deleting any Entry, so that chat organization cannot destroy diary evidence.
98. As the owner, I want record-grounded statements labeled and cited, so that I can distinguish evidence from model prose.
99. As the owner, I want cross-record inferences explicitly labeled as inference, so that synthesis is not mistaken for a recorded fact.
100. As the owner, I want general advice explicitly labeled as not coming from my records, so that general knowledge is not presented as personal experience.
101. As the owner, I want the Agent to say first when my records are insufficient, so that an unsupported answer is never disguised as evidence.
102. As the owner, I want optional general advice after an insufficient-evidence notice, so that the Agent can still be helpful without fabricating history.
103. As the owner, I want inline numbered citations, so that I can connect claims to sources while reading.
104. As the owner, I want a source list with Entry Time and a short Original Content excerpt, so that I can review evidence quickly.
105. As the owner, I want selecting a citation to open the exact cited Entry Revision, so that later edits do not change the apparent evidence.
106. As the owner, I want cited historical revisions marked when a newer revision exists, so that I understand why an old answer differs from current content.
107. As the owner, I want navigation from a citation to the current Entry in date-grouped history, so that I can inspect its present context.
108. As the owner, I want multiple matched chunks from one revision collapsed into one visible citation, so that source lists are not repetitive.
109. As the owner, I want a portable JSON/ZIP export, so that my records are not locked into one deployment.
110. As the owner, I want export to include Entries, every Entry Revision, AI Drafts, AI Corrections, categories, tags, Conversations, messages, and citations, so that non-rebuildable history is preserved.
111. As the owner, I want export to exclude credentials, API keys, and rebuildable embeddings, so that portability does not leak secrets or inflate the archive.
112. As the owner, I want one logical database backup created daily, so that irreplaceable records have an operational recovery path.
113. As the owner, I want backups stored in a private Azure Blob container, so that backup copies are not publicly reachable.
114. As the owner, I want the latest 30 daily backups retained, so that recovery has useful history without unbounded storage.
115. As the owner, I want old backup blobs removed through lifecycle management, so that retention is automatic and cost-bounded.
116. As the owner, I want restore to rebuild embeddings and unfinished derived processing, so that backups need not preserve rebuildable index state.
117. As the owner, I want a backup restored into an independent test database before MVP acceptance, so that backup success is demonstrated rather than assumed.
118. As the owner, I want passwordless Magic Link or OTP authentication, so that I can sign in from desktop and mobile without maintaining another password.
119. As the owner, I want public sign-up disabled, so that no other person can create an account.
120. As the owner, I want every protected API operation to verify my configured identity, so that a valid token for another identity is still rejected.
121. As the owner, I want unauthenticated requests rejected even though the API URL is public, so that an unguessable URL is not treated as security.
122. As the owner, I want the frontend bundle to contain no backend secret, so that public GitHub Pages hosting cannot expose private credentials.
123. As the owner, I want production CORS restricted to my exact GitHub Pages origin, so that arbitrary websites cannot call the API from my browser session.
124. As the owner, I want production logs to omit all diary text, prompts, answers, excerpts, authentication material, and secrets, so that monitoring does not become another personal-data store.
125. As the owner, I want sanitized operational logs retained for 30 days, so that recent failures can be diagnosed without long-term telemetry accumulation.
126. As the owner, I want a log-ingestion safety cap and notification, so that a runaway logging bug cannot consume the student credit silently.
127. As the owner, I want unique content and fake-secret markers checked against Azure logs during acceptance, so that redaction is verified end to end.
128. As the owner, I want the application usable in a modern mobile browser, so that I can record and review Entries away from my computer.
129. As the owner, I want responsive login, capture, history, Entry view, edit, and Agent flows, so that mobile support covers real use rather than only page loading.
130. As the owner, I want a Sidebar link labeled `DIARY` below `JOURNEY` and above `MktAgent`, so that the product name and intended personal-site navigation are consistent.
131. As the owner, I want Diary rendered directly rather than through an iframe, so that mobile layout, scrolling, and authentication redirects remain coherent.
132. As the owner, I want existing HOME, PROJECT, JOURNEY, MktAgent, and VideoNote behavior preserved, so that adding Diary does not rewrite unrelated pages.
133. As the owner, I want the backend to scale to zero and at most one replica, so that a single-user service remains cost-constrained.
134. As the owner, I want the Azure project budget to notify me at 50, 80, and 100 percent of USD 5 per month, so that abnormal infrastructure spending is visible.
135. As the owner, I want the Azure for Students spending limit retained, so that the project cannot silently become pay-as-you-go.
136. As the owner, I want production OpenRouter usage hard-limited to USD 5 per month with no automatic top-up, so that AI cost has an enforceable ceiling.
137. As the owner, I want live-model evaluation isolated behind a USD 1 monthly key, so that tests cannot consume the production allowance.
138. As the owner, I want Supabase to begin on the Free Plan, so that the MVP does not assume a recurring USD 25 subscription.
139. As the owner, I want Supabase quota reviews at 60, 80, and 90 percent, so that capacity decisions happen before restriction.
140. As the owner, I want production released only after I manually start the workflow, so that a normal push cannot replace the live backend.
141. As the owner, I want a new revision verified before it receives traffic, so that deployment failure leaves the known-good version active.
142. As the owner, I want traffic switched back to the previous immutable revision without rebuilding it, so that rollback is fast and reproducible.
143. As the owner, I want database migrations backward-compatible with the immediately previous application version, so that code rollback remains possible.
144. As the owner, I want a verified pre-migration backup before a schema-changing release, so that irreversible mistakes have a recovery point.
145. As the owner, I want normal rollback not to restore an old database automatically, so that Entries created after deployment are not discarded.
146. As the owner, I want written deployment, backup, restore, rollback, OpenRouter budget, AI recovery, and Supabase resume instructions, so that I can operate the system myself.
147. As the owner, I want a guided release and rollback exercise, so that the handoff teaches operation rather than only delivering files.
148. As the owner, I want a completed production handoff checklist, so that deployed version, verification results, limitations, and runbooks are recorded.

## Implementation Decisions

### Product and ownership boundary

- The product has one permanent owner identity. Single-user is a product boundary, not an MVP shortcut.
- Supabase Auth owns passwordless Magic Link or OTP sign-in. Public sign-up is disabled and the one allowed owner is provisioned administratively.
- FastAPI validates token signature, issuer, audience, expiry, and the configured owner identity on every protected request. Possession of another valid Supabase token is insufficient.
- PostgreSQL Row Level Security independently restricts personal tables to the configured owner. Backend authorization and RLS are defense in depth.
- The public frontend never receives a database secret, OpenRouter key, GHCR credential, Azure credential, or OpenRouter Management Key.
- The fixed product timezone is `Asia/Taipei`. All stored timestamps use UTC; date grouping, calendar boundaries, default Entry Time, and the meaning of today use the fixed owner timezone.
- Mobile support means a responsive web application in current mobile browsers. It does not introduce a native application or offline synchronization.

### Frontend composition and navigation

- Diary is a first-class page in the existing GitHub Pages personal website, not an iframe and not a separately navigated Azure-hosted frontend.
- Its Sidebar label is `DIARY` and the link is immediately below `JOURNEY` and above `MktAgent`. All shared header copies and responsive navigation sizing must account for the additional link.
- The existing HOME, PROJECT, JOURNEY, MktAgent, and VideoNote implementations remain vanilla HTML, CSS, and JavaScript and retain their current behavior.
- Only the Diary page body mounts a React and TypeScript application built with Vite.
- The Vite build uses the `/my-personal-website/` repository base and is incorporated into the existing GitHub Pages publication without dropping existing static files or assets.
- Public frontend configuration is limited to the Supabase project URL, Supabase publishable key, and public FastAPI base URL.
- Authentication callbacks return to the deployed Diary page. Local callback origins are configured separately and are not accepted by production CORS.
- The primary application surfaces are authentication, continuous history, calendar, direct search, Insight Agent Conversations, Trash, export, and operational Settings.
- A global capture action is reachable without leaving history or calendar. The composer is modal or drawer-like and preserves the underlying scroll position.
- History uses bidirectional cursor loading and explicit scroll anchoring. It does not fetch the entire lifetime history in one response.
- Selecting a calendar day switches to history with that day as the anchor. It does not open a disconnected one-day document.
- Entry cards always render complete current Original Content. AI-derived content is secondary, compact, collapsible, and state-aware.
- Desktop and mobile layouts expose the same data and actions; responsive presentation may differ but must not remove core capability.

### Domain model and relational storage

- `entries` holds stable Entry identity and lifecycle metadata: Entry UUID, owner UUID, editable Entry Time, current Entry Revision reference, immutable capture time, latest update time, and optional Trash time.
- `entry_revisions` holds immutable Entry Revision UUID, parent Entry UUID, monotonically increasing revision number, complete Original Content, and creation time.
- The current revision reference and revision sequence are constrained so an Entry cannot point to another Entry's revision and revision numbers cannot repeat within one Entry.
- An edit request carries the revision the client believed was current. If that precondition is stale, the API returns a conflict and the newer Entry rather than silently overwriting it.
- Entry Time changes update Entry metadata only. They do not create an Entry Revision or invalidate AI interpretation because Original Content did not change.
- Restoring an old revision copies its complete Original Content into a new immutable current revision.
- Trash is represented on the stable Entry. Queries for history, calendar, search, active retrieval, AI scheduling, and analysis exclude trashed Entries by default.
- Restoring from Trash clears the Trash state and re-establishes any missing current-revision AI work idempotently.
- Permanent deletion cascades through Entry Revisions, Entry-level AI derived records, processing records, and rebuildable retrieval-index rows after explicit confirmation.
- Conversation citations whose target is permanently deleted remain as a source-unavailable marker without a live excerpt or navigation target. The Conversation itself is not implicitly deleted.
- `ai_drafts` stores one or more generated proposals for a specific Entry Revision. Regeneration creates a new auditable generation and identifies which Draft is current.
- An AI Draft stores summary, controlled category values, normalized free-form tags, exact requested model slug, actual upstream provider when returned, request or generation identifier, input/output/reasoning token usage where available, cost metadata, prompt/schema version, and timestamps.
- `ai_corrections` stores the owner's current corrected summary, categories, and tags separately for a specific Entry Revision, with creation and update timestamps. Original Content revision history does not imply separate history for every AI Correction edit.
- Effective structured metadata resolves to AI Correction when present and otherwise to the current AI Draft. If neither is ready, effective metadata is empty.
- Regenerating an AI Draft changes the current generated proposal but leaves an existing AI Correction effective. Adopting a regenerated Draft requires an explicit action that discards the Correction.
- Controlled categories are learning, project progress, interviews and job search, exercise, mood, productivity, temporary idea, and other. Storage constraints reject unknown category values.
- Tags are trimmed, empty values removed, and duplicates collapsed case-insensitively while retaining a stable display spelling.
- `ai_processing` durably tracks the current Entry Revision's Draft and embedding obligations, aggregate user-visible state, attempt count, sanitized error code, scheduling timestamps, and completion timestamps.
- Processing state values are `pending`, `processing`, `ready`, `failed`, and `blocked_budget`. State transitions are checked atomically.
- Database uniqueness and transition rules permit no more than one active processing record for one Entry Revision.
- `retrieval_chunks` is a rebuildable active index containing the current non-trashed Entry Revision's chunk text, vector, model identifier, vector dimensions, Entry and Entry Revision identifiers, Entry Time, chunk position, and effective category/tag metadata.
- Retrieval-index rows are not evidence independent of Original Content. The referenced Entry Revision remains the canonical source.
- `conversations` stores stable Conversation identity, owner identity, title or display label, and lifecycle timestamps.
- `conversation_messages` stores ordered user and Agent messages, role, creation time, model/prompt metadata for Agent messages, and any status needed to render failed generation without treating it as evidence.
- `message_citations` binds an Agent message to the exact Entry UUID and Entry Revision UUID used, the source Entry Time, collapsed source-chunk positions, visible citation number, and a short display excerpt.
- Citation foreign-key behavior supports historical revisions and an explicit source-unavailable state after permanent deletion.
- A small application-control record represents the shared OpenRouter budget pause, when it began, its sanitized reason, and recovery progress. It contains no key value or personal content.
- Database migrations are ordered, versioned SQL changes. Production structure is never changed through undocumented dashboard edits.

### Entry and history API contract

- Entry creation accepts Original Content, optional intentional Entry Time, and a client idempotency key. It returns the saved Entry and current AI state only after the Entry Revision and durable processing record exist.
- A repeated creation request with the same idempotency key returns the same Entry rather than creating a duplicate.
- The API attempts Queue publication before reporting full processing scheduling success. A durable unsent work record supports reconciliation if Azure Queue publication fails after the database commit.
- History retrieval returns date-grouped Entries around an anchor with separate newer and older cursors. Cursor ordering is stable across equal Entry Times by including Entry identity.
- Calendar retrieval returns active Entry presence or counts for a requested owner-timezone month without returning full content.
- Entry detail returns stable Entry metadata, the current complete Original Content, current/effective AI metadata, processing state, and permitted actions.
- Revision history returns revision identifiers, sequence, timestamps, and complete content only to the authenticated owner.
- Original Content edit accepts the expected current revision and complete replacement content, creates a new revision, changes the current pointer, marks prior derived results stale, and schedules new processing.
- Entry Time change accepts a valid timestamp and returns the Entry's new owner-timezone grouping information.
- Revision restoration accepts a historical revision identifier and expected current revision and creates a new current revision.
- Move-to-Trash, restore, and permanent-delete operations are distinct contracts. Permanent delete requires an explicit confirmation value and is never the default delete behavior.
- Blank or whitespace-only Original Content is a validation error.
- Protected resource lookup does not reveal whether another owner's resource exists; unauthorized access is rejected consistently.

### AI Draft processing and Queue behavior

- FastAPI and the Queue worker depend on an internal AI gateway interface. The domain and API layers do not depend directly on an OpenRouter SDK response shape.
- Azure Storage Queue carries opaque work identifiers rather than Original Content or prompts.
- An event-driven Azure Container Apps Job processes Queue work with zero minimum executions and at most one concurrent execution.
- Queue delivery is treated as at-least-once. Every worker step checks the database state and writes Drafts, chunks, and terminal status idempotently.
- A current Entry Revision processing attempt produces a validated AI Draft and the required active retrieval chunks. A retry completes only missing valid outputs rather than duplicating successful outputs.
- Ordinary transient failure receives one automatic retry. The second ordinary failure becomes `failed` and requires the owner's manual retry.
- OpenRouter payment-required, account-credit, or API-key-limit failure becomes `blocked_budget` without incrementing the ordinary failure allowance.
- The first detected budget block atomically opens the shared budget pause. Workers stop issuing OpenRouter calls while the pause is open, and new obligations remain durable.
- The resume action checks the production inference key's current limit information without a Management Key, closes the pause for one bounded recovery attempt, and requeues eligible work newest first.
- A first recovered work item confirms account-credit availability. Another budget error reopens the pause immediately.
- Recovery selects only current revisions of non-trashed Entries with missing Draft or embedding obligations. It excludes superseded revisions and work already complete.
- The Settings status reports paused/active state and counts of eligible waiting, processing, failed, and complete recovery items.
- Insight Agent generation is rejected with a clear temporary-unavailable state while any eligible current revision lacks its required embedding. It returns automatically when the active embedding backlog is zero.
- Direct search remains available during budget pause; if embeddings are incomplete, it uses the complete `pg_trgm` text branch and clearly does not claim full semantic search.
- The application never invokes OpenRouter key-management APIs, purchases credits, raises limits, or enables automatic top-up.

### OpenRouter model and privacy contract

- OpenRouter is the sole production gateway for Draft generation, Agent answer generation, and embeddings.
- Environment configuration supplies exact model slugs. The defaults are `openai/gpt-5.4-mini` for AI Drafts, `openai/gpt-5.6-luna` for Insight Agent answers, and `openai/text-embedding-3-small` for embeddings.
- Production rejects mutable aliases such as `latest`.
- Every request denies provider data collection, requires a zero-data-retention endpoint, and requires the selected endpoint to support all requested parameters.
- Same-model provider fallback is allowed among privacy-eligible endpoints. Cross-model fallback is not sent or accepted.
- No eligible endpoint is a visible retryable failure; the application does not weaken privacy filters.
- OpenRouter private input/output logging and OpenRouter use of inputs/outputs remain disabled in account settings and are verified during production acceptance.
- Production and explicit live evaluation use separate inference keys. The production key has an initial USD 5 monthly hard limit; the evaluation key has an initial USD 1 monthly hard limit.
- Automatic credit top-up is disabled. Key limits and provider settings are owner-controlled external configuration.
- The AI Draft request uses a versioned structured-output schema. Invalid summary length, categories, tags, or response shape fails validation and follows normal retry behavior.
- AI prompts instruct the model to summarize only the supplied Original Content and not invent scores, mood ratings, productivity ratings, tasks, events, or facts.
- The system persists response routing and usage metadata needed for audit and cost review without persisting prompts or responses in operational logs.
- Model changes are evaluated independently by workload against the fixed Chinese and mixed-language synthetic set. A model is not upgraded solely because a stronger model exists.

### Retrieval and direct search

- Embeddings are generated exclusively from Original Content. AI Draft and AI Correction fields are retrieval metadata, not independent answer evidence.
- Only the current Entry Revision of a non-trashed Entry participates in the active retrieval index.
- A short Entry is one chunk.
- A long Entry is split at paragraph boundaries. A paragraph that remains oversized is split into approximately 500–800-token chunks with limited overlap.
- Chunks never combine content from different Entries.
- Reindexing a new current revision replaces the old revision's active index rows atomically after new rows are valid, preventing a mixed-revision active index.
- Retrieval supports a semantic branch using `pgvector` and a text branch using `pg_trgm`.
- Reciprocal Rank Fusion combines independently ranked semantic and text results. The fusion parameters are versioned configuration and are evaluated against fixed retrieval cases.
- Effective categories, tags, Entry Time, Entry UUID, Entry Revision UUID, and chunk positions remain attached to each result.
- Direct search accepts a query plus explicit date, category, and tag filters and returns Entry results without invoking an answer model.
- Search result ranking, matching excerpts, and navigation always resolve to the active current Entry Revision.
- Date, category, or tag constraints are applied to Agent retrieval only when explicit or reliably inferred; ambiguous filters broaden retrieval rather than silently excluding evidence.
- Agent retrieval searches the full active history by default.
- After chunk ranking, the Agent orchestration may load the complete current Original Content for selected Entries before answer generation.
- Multiple chunks from one Entry Revision can contribute evidence but collapse to one visible citation.
- The MVP has no LLM reranker.

### Insight Agent and citation contract

- Sending a user message creates or continues a persistent Conversation and starts a fresh retrieval pass for that turn.
- Previous Conversation messages may resolve references such as “that interview,” but previous Agent prose is never personal evidence.
- The model receives only a bounded subset of Conversation context plus the current turn's retrieved Original Content. The complete Conversation remains stored and visible.
- The Agent answer representation distinguishes record-grounded statements, explicitly labeled cross-record inferences, and explicitly labeled general advice.
- Every record-grounded claim has one or more inline numbered citations.
- General advice cannot carry a personal-record citation and cannot be phrased as an event the owner recorded.
- Cross-record inference cites its inputs and is labeled as inference rather than recorded fact.
- A versioned evidence-sufficiency gate evaluates retrieved support before generation and after structured answer validation.
- If personal evidence is insufficient, the response begins with an explicit insufficient-record statement. Optional general advice follows only under its own non-record label.
- The Agent cannot use web search, live browsing, external tools, reminders, email, calendar actions, or other service calls in the MVP.
- Citation numbering is stable within one Agent message, and each visible citation stores the exact Entry Revision used at generation time.
- Citation opening shows the complete cited revision, its Entry Time, and whether a newer current revision exists.
- Navigation from a citation to history opens the Entry's current position while preserving access to the cited historical snapshot.
- Editing an Entry never mutates the evidence snapshot shown by an old answer.
- Permanent deletion removes the source excerpt and live target from affected citations and displays a source-unavailable state.
- Conversation deletion removes its messages and citations but does not modify any Entry.

### Export, backup, and restoration

- Portable export is generated only after owner authentication and produces a versioned JSON manifest packaged as JSON/ZIP.
- Export contains stable Entries, every Entry Revision, AI Drafts, current AI Corrections, effective categories and tags, Conversations, messages, and citations.
- Export excludes Supabase credentials, OpenRouter and Azure keys, JWTs, Magic Links, queue messages, operational logs, vectors, and other rebuildable index state.
- The export format includes schema version, generation time, fixed timezone, and identifiers needed to preserve relations.
- A scheduled Container Apps Job creates one logical PostgreSQL backup daily and writes it to a private Blob container.
- Backup naming and metadata make creation time, source environment, schema version, and verification status identifiable without embedding secrets.
- Blob lifecycle management keeps the latest 30 daily backups and deletes older backups.
- Operational backups retain non-rebuildable Entry, AI Correction, Conversation, and citation data but omit active vectors and transient queue state.
- Restore targets a separate database unless an explicitly approved disaster-recovery cutover is underway.
- Restore validates representative Entry revisions, AI Correction precedence, Conversation/citation relations, owner authorization data, and schema version.
- After restore, active non-trashed current revisions are re-chunked and re-embedded, and unfinished eligible AI work is reconstructed idempotently.
- A normal application rollback never restores the database automatically.

### Production platform and infrastructure

- FastAPI runs on Azure Container Apps Consumption with public HTTPS ingress, `minReplicas = 0`, and `maxReplicas = 1`.
- The event-driven AI worker and scheduled backup Job run in the same selected Azure region as the API, Queue, Blob, and logging resources where supported.
- Supabase Tokyo and Azure Japan East are the preferred matched production pair.
- Deployment verifies Azure for Students availability and quota before provisioning. If Japan East is unavailable, the complete deployment uses Supabase Singapore and Azure Southeast Asia instead of splitting the pair.
- Production initially uses Supabase Free and one owner-only hosted project. There is no hosted staging environment.
- The existing GitHub Pages HTTPS hostname and the Azure-generated Container Apps HTTPS FQDN are used for the MVP. No custom domain is required.
- Azure infrastructure is declarative Bicep. The Azure Portal is for inspection and troubleshooting, not configuration source of truth.
- GitHub Actions authenticates to Azure with OIDC workload identity federation restricted to the intended repository and release context.
- Backend source and GHCR image are private. Images are tagged by immutable Git commit SHA; deployment never depends on `latest`.
- Container Apps pulls from GHCR with a dedicated package-read credential stored as an Azure secret. Azure Container Registry is not provisioned.
- Production application secrets are stored in Azure Key Vault Standard. Managed identities receive least-privilege secret-read access.
- Bicep defines the vault, identities, role assignments, secret references, and other non-secret configuration but never commits secret values.
- Versionless Key Vault references are used where automatic latest-version rotation is intended; rotation acceptance verifies the consuming revision or job picked up the new value.
- Local, test, and production environments use distinct URLs, credentials, and secret injection.
- Synthetic seeding and destructive reset operations refuse to run when the resolved environment is production.

### Release, migration, and rollback

- Ordinary pushes run checks and build the commit-SHA image but do not deploy production.
- Production release is a manually started GitHub Actions workflow whose input identifies the immutable version.
- A release with schema changes creates and verifies a pre-migration logical backup before applying migrations.
- Migrations use expand-contract sequencing. The first release adds compatible structures and transitional code; destructive removal occurs only in a later release after the previous revision no longer needs the structure.
- PostgreSQL migrations use transactions where supported. Migration failure stops the release before traffic promotion.
- FastAPI uses Container Apps multiple-revision mode for blue-green deployment.
- The new Green revision receives no production traffic until provisioning, startup, readiness, and protected smoke checks pass.
- API and AI-processing workloads promoted together use the same commit SHA.
- Successful promotion routes 100 percent of production traffic to Green while the immediately previous known-good revision remains available at zero traffic.
- A failed pre-traffic check leaves the current production revision untouched.
- Manual rollback routes traffic to the prior immutable revision and restores the related worker image version without rebuilding.
- Rollback does not run an automatic down migration and does not restore an old database.
- Bicep `what-if` output is reviewed before infrastructure changes are applied.

### Cost, observability, and privacy

- The Diary Azure resource group has an initial USD 5 monthly Cost Management budget with owner email notifications at 50, 80, and 100 percent.
- Azure budget alerts do not shut down resources automatically. The Azure for Students spending limit remains enabled, and no workflow upgrades the subscription to pay-as-you-go.
- Supabase quota usage is reviewed at 60, 80, and 90 percent. The product does not upgrade itself to a paid plan.
- Operations documentation explains Supabase Free low-activity pause detection and manual resume.
- Production emits structured `INFO` application events. `DEBUG` is off by default.
- Allowed log fields are UTC time, random correlation ID, route template, status, duration, opaque Job/Entry/Revision IDs, AI state, exact model, upstream provider, token/cost metadata, sanitized error type, retry count, queue delay, and deployment SHA.
- Logs never contain Original Content, revision content, AI Draft or Correction fields, Agent questions or answers, prompts, RAG evidence, citation excerpts, HTTP bodies, owner email, Magic Links, OTPs, JWTs, cookies, authorization headers, API keys, database credentials, connection strings, complete query strings, environment values, or raw provider error bodies.
- Exceptions are sanitized before emission. Third-party SDK messages are not trusted to be safe for logs.
- Azure Log Analytics retains Container Apps system and sanitized console logs for 30 days.
- The Log Analytics workspace has an initial 0.1 GB daily ingestion safety cap and an owner notification. The cap is an emergency brake, not normal filtering.
- Application Insights is not enabled in the MVP.
- Production log access is limited to the owner's Azure administration identity. Logs are absent from export and long-term backup.

### Documentation and handoff

- Operator runbooks cover initial Azure bootstrap, Bicep deployment, OIDC trust, Key Vault secret bootstrap and rotation, production release, rollback, backup, restore, OpenRouter credit and key limits, AI backlog recovery, Supabase pause/resume, log inspection, and cost review.
- The production handoff checklist records deployed commit SHA, selected regions, quota checks, infrastructure verification, security and privacy checks, product acceptance, recovery exercises, known limitations, and runbook locations.
- Handoff includes a guided exercise in which the owner starts a release, identifies active and prior revisions, interprets a failed check or sanitized log, verifies backup and budget status, and returns traffic to the prior revision.
- Portal instructions are explanatory operational guidance; reproducible resource configuration remains in Bicep.

## Testing Decisions

### Primary automated test seam

- The principal automated seam is the deployed-shaped backend system boundary: tests send real HTTP requests to FastAPI and observe only public API responses plus authorized, externally observable state.
- This seam runs locally against Supabase PostgreSQL started through the Supabase CLI, Azurite Queue and Blob emulation, the real asynchronous worker, and a deterministic fake implementation of the OpenRouter boundary.
- Tests do not replace the database, Queue, Blob store, authentication contract, or worker with in-memory repositories. The AI provider is the deliberate exception so the ordinary suite remains deterministic, private, fast, and free of model cost.
- The harness waits for asynchronous outcomes through public polling behavior with bounded deadlines; it does not call worker internals or mutate job state directly.
- Assertions favor durable product behavior over implementation structure: saved revisions, visible status, search results, Agent evidence, citations, deletion effects, export contents, and recovery state.

### Critical system scenarios

- Capture tests cover multiple Entries on one date, backdated Entries, blank rejection, UTC storage, Asia/Taipei grouping, and idempotent repeated create requests.
- History tests cover stable reverse-chronological pagination, loading in both directions around a selected date, calendar navigation, and Entries moved across date boundaries.
- Revision tests cover concurrent stale edits, immutable revision history, restoring an older revision as a new current revision, time-only edits, and regeneration without overwriting a Correction.
- Deletion tests cover trash visibility, exclusion from direct search and Agent retrieval, restore, permanent cascade deletion, and unavailable historical citations without disclosure of deleted source content.
- Queue tests cover enqueue-after-commit recovery, duplicate delivery, worker restart, processing lease recovery, one automatic retry, manual retry, and the transition to `blocked_budget`.
- Budget recovery tests verify that capture and direct text search remain available, resume requires an explicit owner action, only current non-trashed missing work is scheduled, work is newest-first, and Agent access remains blocked until the embedding backlog reaches zero.
- Authentication tests cover valid owner access, expired or invalid tokens, a non-owner token, absent credentials, protected export and restore operations, and exact production CORS origin handling.
- Search tests cover lexical-only matches, semantic matches, exact names, mixed Chinese and English, explicit date filters, corrected and regenerated revisions, trash exclusion, and deterministic RRF fusion.
- Agent tests verify fresh retrieval on every turn, conversation persistence without treating earlier answers as evidence, grounded-versus-inferred-versus-general-advice separation, abstention, exact revision citations, citation collapse, and navigation from a citation.
- Export and recovery tests verify the documented archive schema, secret and embedding exclusion, logical backup creation, restore into an isolated database, and reconstruction of derived embeddings and work state.

### Browser end-to-end coverage

- A deliberately small browser suite covers only the highest-risk owner journeys rather than duplicating every backend combination.
- Desktop and mobile-sized runs cover Magic Link/OTP completion, capture from the continuous history, calendar-to-history navigation, editing Original Content, correcting an AI Draft, direct search, asking the Insight Agent, opening a citation, trash and restore, and the budget-blocked recovery affordance.
- Browser assertions include keyboard focus, preserved scroll position after capture, complete Original Content visibility, readable citation/source presentation, and critical controls at a narrow mobile viewport.
- The personal website test confirms the `DIARY` navigation item appears below JOURNEY and above MktAgent and opens the direct Diary page without an iframe.

### Deterministic algorithm tests

- Focused pure tests are added only where a system-level failure would be hard to diagnose or boundary cases are numerous.
- These tests cover chunk boundaries and overlap limits, RRF ordering and tie behavior, citation deduplication, date grouping around UTC/Asia-Taipei boundaries, controlled-category validation, and valid AI/Queue state transitions.
- The suite does not require one unit test per internal function and does not lock tests to private class structure.

### AI quality evaluation

- Live-model evaluation is an explicit local command, separate from normal CI and production smoke tests.
- It uses only the dedicated evaluation OpenRouter key and the fixed synthetic dataset; it never sends real diary content.
- The manually designed dataset contains short, long, multi-topic, ambiguous, mixed-language, explicit-date, relative-date, and proper-name Entries across the intended life categories.
- Each scenario records expected supported facts, acceptable controlled categories, prohibited inventions, retrieval expectations, citation expectations, and questions that require abstention.
- AI Draft evaluation checks summary faithfulness, omission of unsupported facts, category validity, and useful but non-evidentiary tags.
- Insight Agent evaluation checks retrieval relevance, evidence fidelity, citation correctness, appropriate uncertainty, and clear separation of general advice.
- An invented personal event or fact, an incorrect citation, or a claim of personal evidence without supporting Entry content is a critical error. The release acceptance threshold for critical errors is zero.
- Model, provider, prompt version, dataset version, token use, approximate cost, and result are saved as evaluation metadata without storing real personal content.

### Production verification and release gates

- Production smoke checks use a dedicated synthetic canary record and protected owner access. They do not inspect or expose real diary content.
- Pre-traffic smoke verifies health, authentication enforcement, database connectivity, Queue submission, worker completion, Blob access required by operations, and a minimal synthetic search/citation flow.
- A release cannot receive traffic when migrations fail, readiness fails, the smoke check fails, the image SHA does not match, or required privacy configuration is absent.
- Before MVP acceptance, the owner performs and records one backup restore into a separate database, one AI budget-block-and-resume exercise, and one blue-green rollback exercise.
- A log-leak test injects unique synthetic markers into content, prompts, credentials, and provider errors, then confirms those markers are absent from application and platform-queryable logs.
- Ordinary CI must not require Azure credentials, Supabase production credentials, OpenRouter access, internet model calls, or real diary data.

### MVP acceptance criteria

- The owner can securely sign in from desktop and mobile browsers, create multiple free-text Entries per day, and later find the complete Original Content through history, calendar navigation, or direct search.
- Editing preserves immutable history; trash, restore, and permanent deletion have the documented effects across display, AI data, search, citations, and export.
- AI Draft processing is asynchronous, observable, editable through Correction, retryable, budget-safe, and unable to overwrite Original Content or a Correction.
- The Insight Agent retrieves from the complete active current-revision corpus, answers with exact record/date citations, distinguishes inference and general advice, and explicitly reports insufficient evidence.
- Export, daily backup, isolated restore, migration, blue-green release, and rollback procedures have been executed successfully and documented.
- The production system stays within the agreed security, privacy, deployment, logging, and cost controls.
- All ordinary automated suites pass, the live synthetic AI evaluation has zero critical errors, and no unresolved defect blocks a core owner journey.

## Out of Scope

- Public registration, additional accounts, multi-user tenancy, sharing, collaboration, teams, permissions, and role administration.
- scikit-learn models, ML-derived scores, predictive analytics, trend dashboards, and automated lifestyle or productivity conclusions.
- AI-generated numeric ratings, productivity scores, priority scores, tasks, action-item tracking, or automatic edits to Original Content.
- Reminders, scheduled Agent actions, email, push notifications, calendar notifications, and background personal coaching.
- Web browsing, third-party knowledge search, external tools, tool-using Agent actions, and evidence sourced from outside the owner's Entries.
- File, image, document, audio, and video attachments; voice capture and speech-to-text.
- Native iOS or Android applications, installable PWA requirements, offline-first behavior, and offline conflict synchronization.
- Automatic trash expiration or purge.
- LLM reranking of retrieval results.
- Refactoring or migrating the existing JOURNEY, MktAgent, VideoNote, or other personal-site pages to React.
- Embedding the Diary application through an iframe.
- A custom domain, custom production certificates, or domain migration.
- A permanently hosted staging environment.
- Azure Container Registry, Terraform, Application Insights, or an alternative cloud platform.
- Automatic subscription upgrades, automatic OpenRouter top-up, automatic budget-limit changes, or any application-held OpenRouter Management Key.

## Further Notes

- At specification time this repository contains project context and architectural decisions but no product implementation. This specification intentionally defines behavior and boundaries without prescribing source file paths or code snippets.
- The existing personal website is maintained separately. Its sidebar and build/deployment integration are part of the delivery surface, while the Diary backend and its private container image remain separate deployments.
- The USD 5 Azure project budget and the USD 5 production plus USD 1 evaluation OpenRouter monthly caps are conservative starting controls, not estimates of guaranteed spend. Changing them requires an explicit owner decision.
- ML may be reconsidered for exploratory analysis only after both conditions are met: at least 90 calendar days have elapsed since the first Entry and at least 60 distinct days contain active Entries. Predictive work additionally requires at least 180 days and an explicitly defined user outcome. Reaching a threshold starts a review; it does not add ML automatically.
- Production service availability, regional compatibility, and current pricing must be verified during deployment because cloud offerings can change. Any required deviation is recorded before deployment rather than silently changing this specification.
- `CONTEXT.md` and the accepted ADRs remain the governing record for high-cost decisions. If implementation discovery conflicts with them, work pauses for a documented decision instead of choosing an incompatible shortcut.
- The next intended workflow is to convert this ready-for-agent specification into implementation tickets with explicit dependencies, acceptance checks, and delivery order.
- No application code is authorized or produced by this specification step.
