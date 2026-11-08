# Phase 9 — Error handling + resilience

## Goal
The agent degrades gracefully. Provider hiccups, slow tools, and bad model output never become user-visible crashes or runaway spend.

## Concepts
- **Error taxonomy** (Anthropic API): 400 invalid request (don't retry, fix it), 401/403 auth, 404, 413 too large, 429 rate limited (retry with backoff, honor `retry-after`), 5xx / 529 overloaded (retry), connection and timeout errors (retry). Each has a typed SDK exception.
- **Retries:** exponential backoff with **jitter** so clients don't stampede. Retry only *idempotent*/safe operations. Cap attempts and total time.
- **The SDK already retries** (default 2 times on 408/409/429/5xx and connection errors). Know what it does before layering your own, to avoid retry multiplication.
- **Timeouts:** per request, per tool, and per whole agent run. Streaming avoids long-request timeouts.
- **Idempotency:** retrying `create_ticket` must not create two tickets. Use idempotency keys.
- **Circuit breaker:** after repeated failures, stop calling the dependency for a cooldown period.
- **Fallbacks:** secondary model, cached answer, or a human handoff message.
- **Refusals and truncation:** `stop_reason: "refusal"` and `max_tokens` are not exceptions but must be handled.
- **Output validation:** model output that should be JSON may be invalid. Validate (pydantic) and retry/repair a bounded number of times.
- **Error taxonomy for users:** separate what you log (details) from what you say (calm, actionable).

## Requirements
- `resilience.py` with: a retry decorator (backoff+jitter, retryable error set, max attempts, max elapsed), timeout helpers, and a simple circuit breaker.
- Tool-call wrapper: timeout + error → `is_error` tool_result.
- LLM wrapper that handles typed exceptions explicitly (most-specific first) and converts to your own error types (`LLMUnavailable`, `LLMBadRequest`, `BudgetExceeded`, ...).
- Fallback chain: primary model → secondary model → canned "escalate to human" response.
- Idempotency keys on write tools.
- Structured-output validation with bounded repair.
- Failure-injection tests.

## Steps
1. Read the SDK docs on retries/timeouts and the error-codes page. Write down your retry policy (what, how many, how long) *before* coding.
2. Write the retry helper and test it with a flaky fake function (fails twice, then succeeds). Verify delays grow and jitter applies (inject a fake sleep and clock).
3. Decide: use the SDK's built-in `max_retries` or your own? Configure the client (`max_retries`, `timeout`) accordingly, and avoid double retrying.
4. Map SDK exceptions to your error types in `llm.py`: `RateLimitError`, `APIConnectionError`/`APITimeoutError`, `InternalServerError`, `BadRequestError`, `AuthenticationError`, the generic `APIStatusError`.
5. Implement the circuit breaker and test open → half-open → closed transitions with a fake clock.
6. Implement fallback to a second model (also test using a fake). Record in the trace that a fallback occurred.
7. Add tool timeouts with `asyncio.wait_for` or thread timeouts. Test with a `sleep(10)` tool.
8. Make `create_ticket` idempotent by key. Test double-submission.
9. Handle `max_tokens` and `refusal` stop reasons in the agent loop with user-friendly outcomes.
10. **Chaos tests:** a flag that injects 429s, timeouts, and malformed JSON at a configurable rate. Run your eval set with 20% injected failures and measure success rate and added latency.
11. Build a user-facing error message table (internal error → what the user sees).
12. **Certification extra:** do "Extra 2: Escalation and error-propagation design" from `docs/certifications.md` (escalation policy doc, `handoff_to_human` path with packaged context, structured tool errors with `is_retryable`).

## Checkpoint
- [ ] With 20% injected transient errors, ≥95% of eval questions still succeed.
- [ ] No stack trace is ever shown to users.
- [ ] Retries are bounded in count and time.
- [ ] Double-submitted ticket creation yields one ticket.
- [ ] Traces show retries and fallbacks.

## Stretch
- Use the Messages `fallbacks` feature of the API (server-side) vs your own client-side chain. Compare.
- Dead-letter queue for failed jobs.
- Rate-limit-aware concurrency in the eval runner.

## Pitfalls
- Retrying 400 errors (will never succeed, wastes money).
- Retries multiplying (SDK retries × your retries × gateway retries).
- Swallowing exceptions (`except Exception: pass`).
- Retrying non-idempotent writes.
- No overall deadline, so a "retrying" request hangs for minutes.
