# Use a Bounded Entry-centered History Interface

## Context

After an owner changes Entry Time, History must show the moved Entry at its new
position. Ticket 08 repeatedly attempted to recover that Entry by starting from
a date-based History page and following at most five ordinary 20-Entry pages.
No fixed traversal limit can guarantee finding an Entry on a dense date: a
valid target can always lie beyond the chosen five-page, 100-Entry, or other
finite cap. Increasing the cap only moves the failure boundary, while removing
the cap would permit the frontend to download the owner's complete History.

The earlier Ticket 08 decision rejected an `around_entry_id` or other
Entry-centered backend interface. The latest independent review proved that
this restriction conflicts with the product guarantee that a successful Entry
Time change visibly locates the moved Entry within bounded work.

## Options

1. Continue scanning ordinary History pages with a larger fixed request or
   Entry-count limit.
2. Remove the limit and let the frontend traverse or download as much History
   as necessary to find the Entry.
3. Add a bounded Entry-centered History interface that locates the target at
   the data boundary and returns one fixed-size window plus incremental cursors.

## Decision

Add `GET /entries/{entry_id}/history-window` and use it for Ticket 08 Entry Time
recovery.

For a specified active, non-trashed Entry owned by the authenticated permanent
owner, a successful response guarantees all of the following:

- the target Entry is included and can be positioned visibly;
- only one fixed-size bounded History window is returned, independent of
  lifetime History size;
- the window is resolved from one consistent fresh snapshot;
- older and newer cursors from that snapshot permit later incremental loading;
- ordering is stable by microsecond Entry Time followed by Entry UUID; and
- neither the response nor its frontend use requires downloading complete
  History or scanning a fixed number of ordinary History pages to find the
  target.

FastAPI verifies the caller and authorizes the owner-owned target. PostgreSQL
RLS independently limits the target and surrounding History rows to the same
owner. A target belonging to another identity, a trashed target, and a
nonexistent target produce the same non-disclosing resource result and return
no target or surrounding History data.

Entry Time recovery owns a distinct viewport-cancellation state. Newer owner
navigation can cancel recovery positioning without clearing or weakening the
ordinary older/newer pagination anchor required by Ticket 04.

This decision **supersedes** the prior Spec and Ticket 08 decision that the MVP
must not add an `around_entry_id` or Entry-centered History backend interface.
The prior statements and all failed review and finding-fix records remain in
Ticket 08 as historical evidence, but they no longer govern implementation.

## Consequences

- Ticket 08 can guarantee moved-Entry navigation with bounded backend and
  frontend work, even when the Entry lies beyond any former page-scan limit.
- The interface adds a protected read contract and corresponding snapshot,
  cursor, ordering, non-disclosure, RLS, system, and browser test obligations.
- The frontend must replace fixed-page recovery scans rather than increase
  their request or Entry-count constants.
- Calendar, direct-search result, and RAG citation navigation may reuse the
  interface later, but Ticket 08 does not implement those integrations.
- Ordinary History pagination remains governed by Ticket 04's scroll-anchor
  contract and must be tested independently from Entry Time recovery
  cancellation.
