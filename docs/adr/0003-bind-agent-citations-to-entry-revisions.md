# Bind Agent Citations to Entry Revisions

## Context

Insight Agent answers must remain auditable after Original Content is edited. A citation that stores only an Entry ID would silently resolve to newer content that the LLM never saw, making an old answer appear supported by evidence that changed after generation.

## Options

1. Store only the Entry ID and always open its current revision.
2. Copy cited text into every answer without retaining a relation to the source.
3. Store the Entry ID, exact Entry Revision ID, chunk references, Entry Time, and display excerpt used for the answer.

## Decision

Every record-grounded citation is bound to the exact Entry Revision used during generation. The answer renders inline numbered citations and a source list. Selecting a citation shows the cited revision and can navigate to the Entry in the date-grouped history. If a newer revision exists, the UI marks the cited snapshot as historical and offers access to the current revision.

## Consequences

- Old answers remain traceable to the evidence actually supplied to the LLM.
- Editing an Entry cannot silently change the apparent support for an existing answer.
- Citation storage and APIs must carry revision-level identifiers and support viewing historical revisions.
- The UI must distinguish a cited historical snapshot from the Entry's current revision.
