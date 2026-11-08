# Phase 12 — AI gateway

## Goal
Route all model traffic through a gateway that centralizes keys, budgets, rate limits, fallbacks, logging, and model routing, so apps stop holding provider keys.

## Concepts
- **AI gateway:** a proxy between your apps and LLM providers. It provides one endpoint, virtual keys per team/app/user, spend limits, rate limits, retries/fallbacks, caching, load balancing, and unified logging.
- **Why:** swap models without touching app code, stop leaking the real provider key, enforce org-wide budgets, and get central observability.
- **LiteLLM proxy:** open-source gateway. Exposes OpenAI-compatible and Anthropic-compatible routes, config in YAML, Postgres for keys/spend, and can send callbacks to Langfuse.
- **Virtual keys:** keys issued by the gateway, each with its own budget, allowed models, and rate limit. Revocable without rotating the real key.
- **Tradeoffs:** extra hop (latency), a new single point of failure, and retries now exist in three places (SDK, app, gateway). Decide where each lives.
- **Compatibility caveat:** some newer Anthropic-specific features (new beta headers, thinking/caching options) may not pass through every gateway perfectly. Test the features you depend on.

## Requirements
- LiteLLM proxy + its Postgres in `docker-compose.yml`, with a `litellm-config.yaml`.
- Model aliases: `policypal-main`, `policypal-cheap`, `policypal-judge` mapped to real Claude models.
- Two **virtual keys**: `agent-prod` (budgeted, rate-limited) and `evals` (separate budget).
- Fallback: `policypal-main` → secondary model on error.
- Your app's `llm.py` points to the gateway via base URL and a virtual key, with no real provider key in the app environment.
- Gateway spend/logs visible, and traces still flow to Langfuse.

## Steps
1. Read the LiteLLM proxy docs (config.yaml, virtual keys, budgets, fallbacks, Langfuse callback).
2. Add LiteLLM + Postgres to compose. Put the real provider key and a master key in the gateway's env only.
3. Define the model list and aliases in the config. Start the stack and send a raw `curl` through the gateway to confirm it works.
4. Point your Anthropic SDK client at the gateway (`base_url=` / `ANTHROPIC_BASE_URL`) using a virtual key. Check the gateway's Anthropic-compatible route in its docs.
5. Run your eval set through the gateway. Compare results and latency with direct calls (overhead, and do all features work: caching fields, usage, streaming, tool calls?). Document anything that breaks.
6. Create virtual keys through the admin API. Give `evals` a low budget and watch it get cut off with a clear error. Handle that error in your app (`BudgetExceeded`).
7. Set rate limits (RPM/TPM) and confirm a 429 appears and your retry logic respects it.
8. Configure a fallback model and force a failure (invalid primary model) to see it trigger.
9. Wire the gateway callback to Langfuse (or keep app-level tracing. Choose one source of truth for traces to avoid duplicates, and write down why).
10. Decide your policy for retries: SDK `max_retries=0` + gateway retries, or the reverse. Update Phase 9 code to match.
11. Revoke a key and confirm the app fails safely.

## Checkpoint
- [ ] The app runs with zero provider keys in its environment.
- [ ] Budget and rate limits are enforced by the gateway.
- [ ] Fallback is demonstrated.
- [ ] You have a table of features verified through the gateway.
- [ ] Trace data isn't duplicated.

## Stretch
- Gateway-level guardrails (e.g. PII masking plugin) vs your in-app guardrails. Discuss when each fits.
- Response caching at the gateway (and why it's risky for personalized answers).
- Per-user keys with usage dashboards.

## Pitfalls
- Gateway swallowing provider-specific headers or params.
- Master key exposed to the app.
- Double retries causing delays and cost.
- Forgetting the gateway itself needs health checks and a restart policy.
