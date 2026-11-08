# Phase 3 — Context engineering + RAG

## Goal
Make the agent answer from *your* documents, with citations, and refuse when the docs don't cover the question.

## Concepts
- **Context engineering:** deciding *what goes into the model's context window and in what shape*: instructions, retrieved docs, history, tool results. It's the main lever on quality and cost. Rule of thumb: the smallest set of high-signal tokens that makes the right answer likely.
- **RAG (retrieval-augmented generation):** `question → find relevant chunks → put them in the prompt → answer`.
- **Chunking:** splitting docs into pieces. Too big wastes tokens and dilutes relevance; too small loses meaning. Splitting on headings usually beats fixed-size splitting for policy docs.
- **Embeddings:** vectors that represent meaning. Similar text → nearby vectors. Anthropic has no embeddings endpoint, so we use a local model.
- **Vector search:** find the top-k nearest chunks to the question's embedding. **Hybrid search** adds keyword (BM25) matching. It's better for exact terms like "Form 14B".
- **Metadata filtering:** filter by `audience` (employee/customer), `doc_type`, `effective_date` before ranking.
- **Citations:** each chunk has an id; the model must cite those ids; you verify them in code.
- **Grounding / abstention:** instruct the model to answer only from provided context, and say so when it can't.
- **Delimiting untrusted text:** wrap retrieved docs in clear tags (e.g. `<document id="..."> ... </document>`). This helps structure and prepares for Phase 10.

## Requirements
- A corpus of **15–25 markdown policy docs** (see recipe below) with front-matter metadata (`audience`, `title`, `updated`).
- Ingestion script: load → chunk (by heading, with overlap fallback) → embed → upsert into Qdrant with metadata.
- `retrieve(question, audience, k)` returning chunks with scores.
- `answer(question)` building the prompt from retrieved chunks and returning answer + list of cited chunk ids.
- Citation check: reject or flag cited ids that weren't in the retrieved set.
- Abstention: a similarity threshold plus a prompt instruction.
- Everything traced in Langfuse, with retrieval as its own span.

## Corpus recipe
Ask Claude (outside the project) to generate a fictional company "Northwind" handbook: PTO, parental leave, expenses, remote work, security basics, password policy, incident reporting, returns, shipping, warranty, refunds, privacy. Ask for **realistic specifics** (numbers, thresholds, exceptions, conflicting-looking rules). Deliberately make 2 docs overlap and 1 outdated (older `updated` date). Read and edit them yourself so you know the ground truth. You need this for evals.

## Steps
1. `docker-compose.yml`: add Qdrant (`qdrant/qdrant`, port 6333, a named volume).
2. `uv add qdrant-client fastembed python-frontmatter`. Pick a small embedding model (e.g. BAAI/bge-small). Note the vector size, since the collection must match it.
3. Write the corpus into `data/policies/`.
4. Write `rag/chunking.py`: split on `##` headings, keep the doc title and heading path as chunk context, cap chunk length, and give each chunk a stable id (`doc-slug#section`). Unit test it.
5. Write `rag/ingest.py` (idempotent: re-running must not duplicate).
6. Write `rag/retrieve.py`. First vector only. Print the top 5 with scores for 10 questions and judge them by eye. Where does it fail?
7. Add the audience metadata filter. Verify an employee-only doc never shows up for a customer query.
8. Write `rag/answer.py` with the prompt: instructions in `system`; context chunks in the user turn, tagged with ids; question last. Require output like `answer text [doc-id#section]`.
9. Implement the citation validator and the "I don't know" path (threshold + prompt).
10. Run 20 questions: 10 answerable, 5 unanswerable, 5 tricky (conflicting or outdated docs). Record failures in `NOTES.md`. These become the seed of your eval dataset.
11. Experiment, one change at a time: chunk size, k, adding a reranking step, adding hybrid search, query rewriting (use the LLM to rewrite follow-ups into standalone queries). Note what helped. Phase 4 will let you measure this properly.

## Checkpoint
- [ ] Ask "How many weeks of parental leave?" → correct answer with correct citation.
- [ ] Ask something not in the docs → refusal / escalation, not a guess.
- [ ] Customer persona can't retrieve employee-only docs.
- [ ] Each trace shows retrieved chunks and the final prompt.
- [ ] You can explain why you chose your chunking strategy.

## Stretch
- Add a reranker (cross-encoder via a local model) over the top 20 → top 5.
- Prefer newer docs when two chunks conflict (use `updated`).
- Compare "stuff the whole corpus in the context" (the model has a huge window) vs RAG on cost, latency, and accuracy. A very instructive experiment.

## Pitfalls
- Embedding the question and docs with different models.
- Chunks without their heading context (they become ambiguous).
- Re-ingesting duplicates.
- Trusting citations without verifying them.
- Tuning by vibes. Wait for Phase 4 to claim improvements.
