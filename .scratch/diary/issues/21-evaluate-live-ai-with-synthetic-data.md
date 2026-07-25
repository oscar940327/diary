# 21 — Evaluate live AI with synthetic Diary data

**What to build:** Create a deliberate, low-cost live-model quality gate that evaluates both AI Drafts and Insight Agent answers against fixed fictional records, without using real diary content or running in ordinary CI.

**Blocked by:** 11 — Connect the private OpenRouter gateway; 16 — Enforce Insight Agent evidence boundaries.

**Status:** ready-for-agent

- [ ] A manually designed versioned dataset contains no real personal data, copied third-party diary, or identifying secret.
- [ ] Cases cover short, long, multi-topic, ambiguous, mixed Chinese/English, explicit-date, relative-date, proper-name, and intended category examples.
- [ ] Each case records expected supported facts, acceptable categories, prohibited inventions, retrieval expectations, citations, and required abstention.
- [ ] AI Draft evaluation checks summary faithfulness, category validity, useful tags, and absence of invented facts, scores, or tasks.
- [ ] Agent evaluation checks retrieval relevance, evidence fidelity, citation correctness, uncertainty, inference labeling, general-advice labeling, and insufficient-evidence behavior.
- [ ] Invented personal events/facts, incorrect citations, or unsupported claims of recorded evidence are critical errors, with zero accepted for release.
- [ ] Evaluation runs only through an explicit local command using the dedicated evaluation key and never the production inference key.
- [ ] Model, provider, prompt version, dataset version, token use, approximate cost, and result are retained as evaluation metadata.
- [ ] The command refuses a production environment and does not send real Diary rows.
- [ ] Ordinary CI remains deterministic, offline from live models, and free of OpenRouter credentials.
