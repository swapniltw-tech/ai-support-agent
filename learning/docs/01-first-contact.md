# Phase 1 — First contact with Claude

## Goal
Understand exactly what goes over the wire when you "call an LLM", and build a thin, reusable wrapper (`llm.py`) that all later phases use.

## Concepts
- **Messages API:** you send a list of `messages` (alternating `user`/`assistant`) plus an optional `system` prompt. You get back `content` blocks, a `stop_reason`, and `usage` (token counts).
- **Stateless:** the model remembers nothing. "Conversation" means you resend the history every time. This fact drives Phases 7 and 8.
- **Tokens:** input tokens (everything you send) and output tokens (what it writes) are billed separately. Output costs more.
- **`max_tokens`:** a hard cap on the reply length. If hit, `stop_reason == "max_tokens"` and the answer is cut off.
- **Streaming:** receive the answer as it's generated. Better UX, and recommended for long outputs.
- **Thinking and effort:** newer models can reason before answering. You control depth via `output_config={"effort": ...}`. You'll experiment in Phase 8. For now, defaults are fine.
- **Sampling params** (`temperature` etc.): they're removed or restricted on the newest models. Don't rely on them. Control behavior through prompts.
- **Prompting basics:** be explicit about role, task, constraints, and output format. Put stable instructions in `system`.

## Requirements
- `src/policypal/llm.py` exposing a function like `ask(question, *, system=None) -> LLMResult`, where `LLMResult` holds `text`, `input_tokens`, `output_tokens`, `stop_reason`, `latency_ms`, `model`.
- A streaming variant that yields text pieces.
- A first draft of the **PolicyPal system prompt** in `src/policypal/prompts/system.md`, loaded from file (prompts are code. Keep them in files and version them).
- Basic error handling with the SDK's typed exceptions (`anthropic.RateLimitError`, `anthropic.APIConnectionError`, `anthropic.APIStatusError`). Just catch and print clearly for now. Phase 9 does it properly.

## Steps
1. Read the Anthropic Messages API docs page and the Python SDK README (start from docs.claude.com → "Build with Claude"). Note the shape of the response object.
2. Write `ask()` with `client.messages.create(model=..., max_tokens=..., system=..., messages=[...])`. Return the text from the first `text` content block.
3. Print `response.usage`. Ask the same question with 3 differently sized prompts and watch input tokens change.
4. Force a truncation (`max_tokens=20`) and observe `stop_reason`.
5. Multi-turn by hand: build a `messages` list in a loop in a tiny CLI (`input()` → append user → call → append assistant). Observe that tokens grow every turn. This is the "aha" for cost.
6. Add streaming with `client.messages.stream(...)` as a context manager and iterate over `text_stream`.
7. Write the first system prompt: role (support/policy assistant), scope, tone, "answer only from provided policy text; otherwise say you don't know", answer format. Test it with 5 questions, including 2 off-topic and 1 adversarial ("ignore your instructions").
8. Make a deliberate failure: wrong model name, invalid API key, no network. Note which exception class each raises.
9. Write 3 pytest tests for pure helpers (e.g. prompt loading, result parsing). Don't call the live API in unit tests.

## Checkpoint
- [ ] Wrapper returns text + token counts + latency.
- [ ] Your CLI chat works across turns and you can explain why token usage grows.
- [ ] You can explain `stop_reason` values you've seen (`end_turn`, `max_tokens`).
- [ ] You know which exception each failure produced.
- [ ] System prompt lives in a file.

## Stretch
- Compute cost per call yourself from token counts and the current price per million tokens (keep prices in a config dict).
- Use `client.messages.count_tokens(...)` to count tokens before sending.

## Pitfalls
- Appending the whole response object to `messages` instead of just its content. Messages need `{"role": ..., "content": ...}` form.
- Forgetting `max_tokens` (it's required).
- Putting the system prompt inside `messages` (it's a separate parameter).
- Trying to set `temperature` on a model that rejects it. Read the 400 error.
- Logging the API key.

## Reading
Anthropic docs: Messages API, Streaming, Prompt engineering overview, Errors.
