# 15 — Answer the first grounded Insight Agent question

**What to build:** Deliver the first complete personal-memory question path. The owner asks a question, Diary retrieves relevant current Original Content, the Agent model synthesizes an answer, and the stored message cites the exact Entry Revisions used.

**Blocked by:** 14 — Add chunking, embeddings, and hybrid memory retrieval.

**Status:** ready-for-agent

- [ ] The owner can create a Conversation by sending an open-ended question.
- [ ] Each sent question starts a fresh hybrid retrieval pass over the full active history by default.
- [ ] Selected chunks may load their complete Entry Revision content before generation.
- [ ] The model receives only retrieved Original Content and a bounded conversation context, never AI metadata as personal evidence.
- [ ] The generated Agent message and user message are durably ordered within the Conversation.
- [ ] Every grounded claim has inline numbered citations.
- [ ] The source list shows Entry Time and a short Original Content excerpt for each exact cited revision.
- [ ] Multiple contributing chunks from the same revision collapse into one visible citation.
- [ ] The stored citation retains Entry identity, exact Entry Revision identity, collapsed chunk positions, citation number, and source time.
- [ ] A browser test demonstrates an interview-preparation question grounded in synthetic project and interview Entries.
- [ ] Real-HTTP tests verify persistence, retrieval, model invocation through the fake boundary, and exact citation relations.
