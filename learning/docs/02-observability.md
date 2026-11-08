# Phase 2 — Observability with Langfuse

## Goal
Make every LLM call visible: inputs, outputs, tokens, latency, cost, and errors. You do this *early* so every later phase is debuggable.

## Concepts
- **Why LLM observability is different:** the same input can give different output, bugs are "bad answers" not exceptions, and cost is per token. You need to see the actual prompt that was sent.
- **Trace:** one end-to-end request (e.g. a user question). **Span/observation:** a step inside it (retrieval, LLM generation, tool call). A **generation** is a span for an LLM call that records model and token usage.
- **Session / user id:** tags that group traces by conversation or user.
- **Scores:** numbers attached to a trace (e.g. thumbs up, eval result). Used heavily in Phase 4.
- **Self-hosting:** Langfuse v3 runs as several containers (web, worker, Postgres, ClickHouse, Redis, MinIO). Good compose practice.

## Requirements
- Langfuse running locally via docker compose, with a project and API keys.
- All LLM calls from `llm.py` produce a trace with: model, input messages, output, token usage, latency, cost.
- Traces carry `session_id` and `user_id` (fake ones for now).
- Secrets for Langfuse in `.env`.

## Steps
1. Get Langfuse's self-hosting compose file from its docs (search "Langfuse self-hosting docker compose") and save it as `infra/langfuse/docker-compose.yml`. Change the placeholder secrets. Run `docker compose up -d` and wait until it's healthy (first start takes a few minutes).
2. Open the UI (default `http://localhost:3000`), create an account, an org, a project, and API keys. Put them in `.env` (`LANGFUSE_PUBLIC_KEY`, `LANGFUSE_SECRET_KEY`, `LANGFUSE_HOST`).
3. `uv add langfuse`. Read the Python SDK docs for the current tracing API (it's built on OpenTelemetry and the interface has changed between versions, so use the docs, not memory).
4. Instrument `ask()`: wrap it so each call creates a generation with model, input, output, and `usage_details`. Try the decorator/context-manager style from the docs.
5. Make one trace per user question, with `session_id` set for the CLI chat session. Run a 4-turn chat and find it in the UI as one session.
6. Cause an error (bad model name). Confirm it appears in the trace with the error info.
7. Look at the cost column. If model pricing is missing, add a custom model definition in Langfuse settings.
8. Add a tiny `observe` helper of your own that records latency and attaches metadata (`app_version`, `prompt_version`). You'll use `prompt_version` to compare prompts later.
9. Make sure flushing happens on exit (short scripts can exit before traces are sent).

## Checkpoint
- [ ] A trace shows system prompt + user message + reply + tokens + cost.
- [ ] Sessions group multi-turn chats.
- [ ] Errors are visible.
- [ ] Langfuse volumes persist across `docker compose down` / `up`.
- [ ] You can answer from the UI: "which call was slowest/most expensive today?"

## Stretch
- Also emit OpenTelemetry directly from the Anthropic SDK and compare with Langfuse's integration (read the SDK's OpenTelemetry docs).
- Manage prompts in Langfuse Prompt Management and fetch them by label.

## Pitfalls
- Version mismatch between SDK and server (v2 vs v3 docs). Read the docs for the version you installed.
- Traces missing because the process exited before flush.
- Logging PII into traces. Note this now, and we'll handle it in Phase 10.
- Compose services needing 4–6 GB RAM. Check Docker Desktop's memory setting.
