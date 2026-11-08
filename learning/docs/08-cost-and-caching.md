# Phase 8 — Cost, token budgeting, caching

## Goal
Know what each request costs, cap it, and cut it using caching, model/effort choice, and context hygiene, with evals proving quality didn't drop.

## Concepts
- **Cost = input tokens × input price + output tokens × output price** (cached reads are much cheaper than fresh input). Look up current prices and keep them in config.
- **Cost per *completed task*** is the real metric, not cost per request. A cheaper model that needs more retries isn't cheaper.
- **Prompt caching:** the API stores a prefix of your prompt so repeat requests read it at a discount and faster. It matches on an **exact prefix**, in this order: tools → system → messages. Change one byte early and everything after it misses the cache.
  - Mark breakpoints with `cache_control: {"type": "ephemeral"}` (or use top-level automatic caching, see docs).
  - There is a **minimum prefix length** for caching. Short prompts silently don't cache.
  - Verify via `usage.cache_creation_input_tokens` / `usage.cache_read_input_tokens`.
  - Cache TTL is short (about 5 minutes by default), so it helps with steady traffic and agent loops.
- **Silent cache killers:** timestamps in the system prompt, random ordering of tools, per-request ids at the top, editing earlier messages.
- **Levers, roughly in order:** (1) caching, (2) trimming wasted context, (3) output limits, (4) effort level, (5) smaller model for easy steps (routing), (6) batch API for non-urgent work (about half price).
- **Budgets:** per-request token cap, per-session cap, per-user daily cap, org monthly cap. Enforce in code (and later at the gateway).
- **Semantic/response caching:** caching *answers* for repeated questions. Cheap but risky for policy that changes or personalized answers. Only for safe, public, FAQ-style queries.

## Requirements
- `cost.py`: compute USD cost from a `usage` object, including cache read/write tokens. Unit tested.
- Cost shown per request, per session, and in eval summaries; recorded in Langfuse.
- Prompt caching enabled on the stable prefix (tools + system prompt + possibly a static policy block), with a **cache-hit-rate** metric.
- Budget enforcement: `BudgetExceeded` raised when a per-session or per-user daily cap is hit, with a friendly user message.
- A **model/effort comparison** over your eval set producing a cost-vs-quality table.
- Optional: simple router: cheap model for intent classification/query rewrite, stronger model for final answers.

## Steps
1. Write `cost.py` with a price table and tests using hand-calculated examples.
2. Build a cost report script over Langfuse traces or your own logs: total, avg per question, p95.
3. Enable caching: place `cache_control` on the system prompt (and tools). Make the prefix large enough to qualify (test the minimum). Send the same request twice and confirm `cache_read_input_tokens > 0`.
4. **Break the cache on purpose** (add a timestamp to the system prompt) and watch hits vanish. Then fix it, moving volatile content after the last breakpoint.
5. In the agent loop, confirm that later steps read the earlier prefix from cache. Compute savings across a multi-step run.
6. Trim waste: smaller retrieved context (lower k, shorter chunks), truncated tool outputs, tight `max_tokens`. Re-run evals after each change.
7. Effort sweep: run your eval at `low`, `medium`, `high` (parameter lives in `output_config`; see docs). Plot quality vs. cost. Pick per route.
8. Model sweep: run the eval on `claude-opus-5-5`, `claude-sonnet-5-5`, `claude-haiku-5-5`. Check the SDK/docs for current IDs and prices. Decide where a cheaper model is good enough, and use the eval as the proof, not intuition.
9. Implement budget enforcement and tests (fake usage numbers, no API calls).
10. Try the Batch API for running your eval set at lower cost. Note the latency tradeoff.
11. Write a one-page "cost model": expected cost per 1,000 conversations under your final config.

## Checkpoint
- [ ] You can state the average cost of an answered question to within ~10%.
- [ ] Cache hit rate is measurable and >0 on repeat traffic.
- [ ] A budget cap triggers a graceful message.
- [ ] Cost-vs-quality table exists, and you made at least one config change based on it.
- [ ] You can name 3 ways to silently destroy your cache.

## Stretch
- Task budgets / compaction features from the API docs for long agent runs.
- Semantic answer cache for the public FAQ route, with TTL and invalidation when docs change.
- Alerting on cost spikes (Langfuse dashboards).

## Pitfalls
- Optimizing cost before you have evals. You'll cut quality blindly.
- Assuming caching works without checking the usage fields.
- Different models have different cache namespaces. Switching models mid-conversation resets it.
- Counting only input tokens, forgetting that "thinking" tokens are billed as output.
- Setting `max_tokens` so low it truncates answers (costly retries).

## Reading
Anthropic docs: prompt caching, token counting, batch processing, pricing, effort.
