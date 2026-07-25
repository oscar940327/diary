# 14 — Add chunking, embeddings, and hybrid memory retrieval

**What to build:** Extend direct lookup into the retrieval foundation for personal memory. Current Original Content is chunked, embedded, searched through semantic and text branches, and fused deterministically while retaining exact Entry Revision attribution.

**Blocked by:** 11 — Connect the private OpenRouter gateway; 13 — Search Original Content directly.

**Status:** ready-for-agent

- [ ] Embeddings are generated only from Original Content; Draft and Correction metadata never become independent evidence.
- [ ] A short Entry remains one chunk, while long content splits paragraph-first into the accepted approximate size with limited overlap.
- [ ] No chunk combines text from different Entries.
- [ ] Active retrieval contains only the current revision of each non-trashed Entry.
- [ ] Reindexing replaces old active rows atomically after the new revision's chunks are valid.
- [ ] Semantic `pgvector` and text `pg_trgm` rankings are fused with versioned Reciprocal Rank Fusion configuration.
- [ ] Results retain Entry, exact Entry Revision, Entry Time, chunk order, and effective category/tag metadata.
- [ ] Direct search uses hybrid ranking when the semantic index is complete and continues with the full text branch when it is not.
- [ ] Filters and navigation continue to resolve to current active Entries.
- [ ] Focused tests cover paragraph and oversized-paragraph boundaries, overlap, RRF order and ties, revision replacement, mixed language, exact names, and Trash exclusion.
- [ ] Real-HTTP tests verify retrieval against Supabase PostgreSQL and the fake embedding provider.
