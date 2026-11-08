# Phase 7 — History + memory

## Goal
Give the agent a working conversation history that doesn't blow up the context, plus long-term memory that persists across sessions.

## Concepts
- **History (short-term):** the messages of the current conversation, which you resend every request. Cost and latency grow with length.
- **Context limits:** even with huge windows, long contexts cost more, are slower, and quality can degrade ("context rot"). Manage it deliberately.
- **History strategies**
  - *Full:* simplest, until it isn't.
  - *Sliding window:* keep last N turns.
  - *Summarization:* replace older turns with a summary.
  - *Context editing:* drop old tool results (they're usually big and stale).
  - *Server-side compaction:* the API can summarize for you (beta, see docs). Understand the manual version first.
- **Long-term memory:** facts that outlive a session (preferences, the user's department, an open ticket). Types: *semantic* (facts), *episodic* (past interactions), *procedural* (learned instructions).
- **Memory write policy:** what is worth remembering? Saving everything creates noise and privacy risk.
- **Memory read policy:** retrieve only relevant memories into context, not all of them.
- **Memory tool pattern:** give the model tools like `save_memory` / `recall_memory` and let it manage them, with your code enforcing rules.
- **Privacy:** memory is stored personal data. It needs scoping per user, expiry, and delete-on-request.

## Requirements
- Persistent conversations: `conversations` and `messages` tables (SQLite now). Resume a session by id.
- A **history manager** that, given the stored messages, returns what to send: with a token budget, keeping the system prompt + most recent turns + a rolling summary of older ones.
- Old tool results are trimmed or replaced with a stub once they're no longer needed.
- **Long-term memory store** per `user_id`: save/recall/delete, with timestamps and a source reference. Stored as rows plus embeddings (reuse Qdrant, with a `user_id` filter).
- `save_memory` / `recall_memory` tools (user-scoped by *session*, not by model-provided args).
- A user command to list and delete memories ("what do you remember about me?" / "forget that").

## Steps
1. Design the schema on paper (messages: id, conversation_id, role, content JSON, tokens, created_at). Store content as JSON, since blocks like tool_use aren't plain strings.
2. Write the repository layer (`memory/store.py`) with plain `sqlite3` or SQLAlchemy. Test it.
3. Make the CLI resumable: `--session <id>`.
4. Write `history.build_context(messages, budget_tokens)`. Count tokens with `client.messages.count_tokens` or a cheap estimate. Test with a synthetic 100-turn conversation.
5. Implement the summarizer: when history exceeds a threshold, summarize the oldest turns with an LLM call and store the summary as a message (keep the original rows, just don't send them). Check summary quality by asking a question that depends on an early detail.
6. Trim old tool results. Measure token savings on a realistic conversation.
7. Build the long-term memory store and the two tools. Write rules: only save stable, useful facts; never save secrets/PII beyond what's allowed; require the model to state *why*.
8. Test across sessions: tell it your department in session A, and see it use that in session B.
9. Add the "list/forget" user flow and a retention rule (e.g. expire after 90 days).
10. Add eval cases: multi-turn dependent questions ("and what about for contractors?"), memory recall across sessions, and **memory isolation** (user A's facts never appear for user B).

## Checkpoint
- [ ] Conversations survive restarts.
- [ ] A 50-turn chat stays within a token budget with correct answers about early facts.
- [ ] Cross-session memory works and is user-isolated.
- [ ] You can delete a user's memory entirely.
- [ ] Token-per-turn growth graph is flat-ish after summarization kicks in.

## Stretch
- Compare your summarization against the API's server-side compaction feature.
- Memory consolidation job: periodically merge duplicates and drop stale facts.
- Store episodic memories of resolved tickets and surface them for similar future issues.

## Pitfalls
- Summaries that drop critical details (names, numbers, decisions). Prompt it to preserve them.
- Breaking tool_use/tool_result pairing when trimming history. They must stay matched.
- Letting the model choose which `user_id` to save memory under.
- Prompt-injection via memory: a malicious doc or message gets "remembered" and replayed forever. Treat memory as untrusted input (Phase 10).

## Reading
Anthropic docs: context windows, context editing, compaction, memory tool.
