# Version Original Entry Content Instead of Overwriting It

## Context

Diary must preserve user-authored records over the long term while still allowing corrections. AI Drafts, AI Corrections, embeddings, and future analysis are derived from a particular version of Original Content. Overwriting content in place could leave derived data associated with text that no longer exists and would discard the user's original input.

## Options

1. Overwrite Original Content in place and regenerate derived data.
2. Keep Entry content immutable and require corrections as separate Entries.
3. Keep a stable Entry identity and create an immutable Entry Revision for every Original Content edit.

## Decision

Use a stable Entry identity with immutable Entry Revisions. The newest revision is displayed by default. AI Drafts and AI Corrections are tied to a specific Entry Revision. When a new revision is created, derived results for the previous revision become stale and are excluded from display and retrieval while a new AI Draft is produced.

## Consequences

- The complete user-authored history remains available for inspection and restoration.
- Derived AI content and embeddings can always be traced to the exact Original Content used to create them.
- Editing requires revision-aware queries and stale-result handling rather than a simple content overwrite.
- Storage usage increases slightly, but Entry text is expected to be small.
