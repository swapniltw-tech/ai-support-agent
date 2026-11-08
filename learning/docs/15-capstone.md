# Phase 15 — Capstone: ship it

## Goal
Package everything into a clean, reproducible service with an API, one-command startup, CI that enforces your quality gates, and runbooks.

## Concepts
- **Service boundary:** a FastAPI app exposing `/chat` (with streaming), `/health`, `/feedback`.
- **Authentication:** requests carry a token that maps to `user_id` + `role` + `audience`. This is the identity your tools and policies trust.
- **12-factor config:** env vars for config and secrets; same image across environments.
- **CI quality gates:** lint + unit tests + policy tests + eval thresholds + red-team thresholds, on every pull request.
- **Feedback loop:** thumbs up/down → Langfuse scores → new eval cases. This is how the system improves after launch.
- **Runbook:** a short doc describing what to do when things break.

## Requirements
- FastAPI service in `src/policypal/api/` with:
  - `POST /chat` (JSON, and an SSE streaming variant), session ids, auth dependency
  - `POST /feedback` (rating + comment → Langfuse score)
  - `GET /health` (checks DB, vector store, gateway)
- Multi-stage `Dockerfile` (uv-based, non-root user, no secrets baked in).
- Root `docker-compose.yml` including: app, Qdrant, Postgres, LiteLLM gateway, MCP servers + gateway, Langfuse (or an `include`d file). `docker compose up` starts everything.
- Postgres replaces SQLite for history/memory (with migrations. Try Alembic).
- GitHub Actions (or equivalent) workflow: ruff, pytest, policy validation, and a **small, cheap eval subset** with thresholds. A nightly job runs the full eval + red-team suite.
- Docs: `README.md` (quickstart), `docs/runbook.md`, `docs/architecture.md`, `docs/threat-model.md` (from Phase 10), and a final cost model.
- A **load test** (e.g. `locust` or `hey`) showing behavior under concurrency, with rate limits and budgets behaving.

## Steps
1. `uv add fastapi uvicorn[standard]`. Write the app skeleton with pydantic request/response models and dependency-injected agent/config.
2. Implement auth (static bearer tokens in a policy/config file are fine for the project). The token determines role and audience. Add tests: no token → 401.
3. Implement `/chat` non-streaming first, then streaming (SSE) using your Phase 1 streaming code and FastAPI's `StreamingResponse`.
4. Per-user rate limit and budget checks at the API edge (reuse governance engine).
5. Migrate storage to Postgres: schema + migrations, repository interface unchanged (you designed it as a layer, so only the implementation changes).
6. Write the Dockerfile; build, and run as non-root; verify no secrets in layers (`docker history`).
7. Assemble the full compose stack with healthchecks and `depends_on: condition: service_healthy`. Test from a clean clone: `cp .env.example .env && docker compose up`.
8. Write CI. Keep PR evals small (≈15 cases, cheap model) to control cost, and full evals nightly. Fail the build on threshold regressions.
9. Add the feedback endpoint and a script that turns low-rated traces into candidate eval cases for your review.
10. Load test with 20 concurrent users. Look at p50/p95 latency, error rate, cost, and gateway rate-limit behavior. Fix the top bottleneck.
11. Write the runbook: symptoms → checks → fixes for (a) provider outage, (b) cost spike, (c) bad-answer reports, (d) suspected injection, (e) Langfuse down. Practice one by killing a container.
12. Final review: walk the NFR list in `PLAN.md` and tick each with evidence (link to a trace, a test, or a metric).
13. Write a retrospective: what you'd change, what surprised you, what you'd learn next.

## Checkpoint
- [ ] Fresh clone → `docker compose up` → working chat via `curl`.
- [ ] CI blocks a PR that breaks an eval threshold (try it).
- [ ] Every NFR in `PLAN.md` has evidence.
- [ ] Runbook exercise done.
- [ ] Final cost-per-1,000-conversations number documented.

## Stretch
- Minimal web chat UI (Chainlit/Streamlit) with citations and feedback buttons.
- Deploy to a small VM or a managed container service.
- Claude Code in CI: finish Side track A (`docs/side-tracks.md`) by adding an automated review job on a small diff.
- Final certification pass: complete the gap-check in `docs/certifications.md` §6 and review all of `SCENARIOS.md`.
- Batch re-evaluation when policy docs change (doc-change → re-ingest → eval → alert).

## Pitfalls
- Baking `.env` into the image.
- Healthchecks that just return 200 without checking dependencies.
- Running full evals on every PR (expensive and slow).
- Letting CI pass with the eval step skipped.
- Docs that drift from reality. Treat them as part of "done".
