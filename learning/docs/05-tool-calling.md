# Phase 5 — Tool calling

## Goal
Let Claude call your Python functions (search policies, look up an order, create a ticket), safely and with validated inputs.

## Concepts
- **Tool calling:** you describe tools (name, description, JSON schema). Claude may respond with a `tool_use` block ("call `get_order_status` with `{order_id: 1042}`"). *Your code* runs the function and sends back a `tool_result`. Claude never executes anything itself.
- **The description is a prompt.** Claude picks tools based on names and descriptions, so write them like onboarding docs for a new hire: when to use it, when not to, what the args mean.
- **`stop_reason == "tool_use"`** tells you the model wants a tool run.
- **Parallel tool calls:** one reply can contain several `tool_use` blocks. Run them all and return all results together in **one** user message.
- **`tool_use_id`:** each result must reference the id of its call.
- **Errors as results:** if a tool fails, return a `tool_result` with `is_error: true` and a helpful message so the model can recover.
- **Strict tool use:** `strict: true` guarantees inputs match your schema.
- **Structured outputs:** a separate feature for forcing the *final answer* into a schema (`output_config.format`). Use it when you need JSON back, not for tool calls.
- **Note on forcing tools:** on the newest models, forcing a specific tool via `tool_choice` `any`/`tool` may be rejected. Use `auto` plus clear instructions. Check the docs for your model.
- **Read vs. write tools:** reads are low-risk; writes (create ticket) need confirmation, idempotency, and limits (see Phases 10–11).

## Requirements
- A fake **business database** (SQLite) with `orders` (id, customer, status, eta, items) and `tickets`.
- Three tools:
  - `search_policies(query, audience)`: wraps your Phase 3 retriever
  - `get_order_status(order_id)`: read-only
  - `create_ticket(summary, priority)`: write, idempotent via a client-generated key
- Pydantic models for each tool's input. Generate the JSON schema from them (`Model.model_json_schema()`).
- A tool registry (dict of name → function + schema), so adding a tool is one place.
- Input validation, error-to-`tool_result` conversion, and tracing of each tool call as a span.

## Steps
1. Create the SQLite DB with seed data (script in `scripts/seed_db.py`).
2. Implement the three plain Python functions with no LLM involved. Unit test them.
3. Define pydantic input models and the registry. Write careful descriptions.
4. Make **one** API call by hand with `tools=[...]`. Ask "Where is order 1042?" and print the raw response. Study the `content` list: a `text` block, a `tool_use` block, and the `stop_reason`.
5. Execute the tool yourself, append the assistant message (with its tool_use) and a user message with the `tool_result`, call again, and get the final answer. Do this manually *once* before automating it in Phase 6.
6. Test failure paths: nonexistent order id, malformed args (use your pydantic validation), a tool that raises. Return `is_error` results and see how Claude reacts.
7. Ask a question needing two tools ("status of order 1042, and what's the return window?"). Observe parallel calls and return both results in a single message.
8. Try ambiguous questions to see if tool descriptions steer correctly. Rewrite a description, then re-test.
9. Add a structured-output exercise: a `classify_intent` step returning `{intent, urgency, needs_human}` via a schema. Understand how it differs from a tool.
10. **Certification extra:** do "Extra 1: Structured output with validation-retry loop" from `docs/certifications.md` (email-extraction task, three enforcement methods compared, bounded retries, few-shot, batch + multi-pass review).
11. Add tool-selection cases to your eval dataset (expected tool + args) and a code grader.

## Checkpoint
- [ ] Order and policy questions trigger the right tools with valid args.
- [ ] Bad input produces a recoverable error, not a crash.
- [ ] Tool calls show up as spans in Langfuse.
- [ ] You can explain the exact message sequence: user → assistant(tool_use) → user(tool_result) → assistant.
- [ ] Eval includes tool-selection accuracy.

## Stretch
- Try the SDK's tool-runner helper (`client.beta.messages.tool_runner`) after you've hand-written the loop, and compare.
- Add `strict: true` and see what changes.

## Pitfalls
- Returning a `tool_result` without the matching `tool_use` in the previous assistant message.
- Splitting parallel results across several user messages.
- Vague tool descriptions, then blaming the model.
- Letting the model supply identifiers it shouldn't (e.g. other customers' ids). Foreshadows Phase 10: identity comes from the *session*, never from model-provided args.
- Parsing tool input by string matching. Always use `json`/pydantic.
