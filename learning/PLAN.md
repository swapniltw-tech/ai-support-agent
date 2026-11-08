# PolicyPal — Internal Policy & Customer Support Q&A Agent
### A step-by-step learning blueprint (Python + Claude SDK)

Start here. This file is the map. The detailed instructions live in `docs/`.

---

## 1. Project goals

**Product goal:** an agent that answers employee policy questions (HR, IT, security, expense) and customer support questions (refunds, shipping, warranty) from a company knowledge base. It cites its sources, refuses when it doesn't know, and can take a few safe actions (look up an order, create a ticket).

**Learning goal:** you learn modern AI-engineering concepts by building each one yourself. The project is the vehicle. Each phase teaches one concept, and each ends with something you can run and measure.

**Ground rules**
1. **You write the code.** The docs say *what* to build, *why*, and how to check it. They give hints and API names, not finished solutions. Ask Claude only when stuck, and ask for hints or reviews before asking for code.
2. **Measure before and after.** From Phase 3 on, every change is judged by evals, traces, and cost numbers. Don't go by gut feel.
3. **One new concept per phase.** Don't skip ahead. Later phases assume the earlier ones.
4. **Commit after every phase** (`git init` first) and tag it, e.g. `phase-04-done`.

---

## 2. What we're building

### Users and use cases
| Persona | Example question | Source |
|---|---|---|
| Employee | "How many days of parental leave do I get?" | HR policy docs |
| Employee | "Can I expense a $90 client dinner?" | Expense policy |
| Customer | "My order #1042 hasn't arrived, what now?" | Shipping FAQ + order lookup tool |
| Customer | "Can I return a opened item?" | Returns policy |

### Functional requirements
- **FR1** Answer questions grounded in a document corpus. Every claim has a citation (doc + section).
- **FR2** Say "I don't know / escalate" when the corpus doesn't cover the question. No guessing.
- **FR3** Call tools: `search_policies`, `get_order_status`, `create_ticket`.
- **FR4** Keep conversation history within a session, and remember user preferences across sessions.
- **FR5** Enforce policy rules: who can see what (employee vs customer), which tools need approval, and what the agent must never say.
- **FR6** Expose a chat interface: CLI first, then HTTP API (FastAPI).

### Non-functional requirements
- **NFR1 Quality:** at least 90% on a golden eval set (grounded, correct, cited). Regressions are caught by CI.
- **NFR2 Observability:** every request has a trace with tokens, latency, cost, and tool calls.
- **NFR3 Cost:** per-request and per-user token budgets, enforced in code.
- **NFR4 Reliability:** retries, timeouts, and fallbacks. A provider outage never produces a stack trace for the user.
- **NFR5 Security:** resists prompt injection from documents and users, with no PII leakage and least-privilege tools.
- **NFR6 Reproducibility:** `docker compose up` brings up the whole stack.

### Target architecture (end state)
```
 CLI / FastAPI ──► Agent service (your Python code)
                      │  agent loop · context builder · memory · guardrails
                      │
        ┌─────────────┼───────────────┬──────────────┐
        ▼             ▼               ▼              ▼
   AI Gateway     Vector DB       MCP Gateway     Postgres
   (LiteLLM)      (Qdrant)        ├ orders MCP    (history,
        │                         ├ tickets MCP    memory)
        ▼                         └ policy MCP
   Claude API
        │
   all of the above ──traces──► Langfuse (self-hosted)
   Policies-as-code (YAML + tests) enforced in CI and at runtime
```

---

## 3. The roadmap

Order is chosen so each phase gives you the tools to evaluate the next one: observability before evals, evals before tuning.

| # | Phase | Concepts covered (from your list) | Doc |
|---|---|---|---|
| 0 | Setup + Python primer | env, packaging, docker basics | `docs/00-setup-and-python-primer.md` |
| 1 | First contact with Claude | SDK, tokens, system prompts, streaming, basic error handling | `docs/01-first-contact.md` |
| 2 | Observability | Langfuse, traces, spans | `docs/02-observability.md` |
| 3 | Context engineering + RAG | context engineering, chunking, embeddings, citations | `docs/03-context-engineering-rag.md` |
| 4 | Evals | golden sets, LLM-as-judge, regression gates | `docs/04-evals.md` |
| 5 | Tool calling | tool schemas, structured outputs | `docs/05-tool-calling.md` |
| 6 | Agent loop engineering | loop, stop conditions, budgets of steps | `docs/06-agent-loop.md` |
| 7 | History + memory | conversation state, summarization, long-term memory | `docs/07-history-and-memory.md` |
| 8 | Cost, token budgeting, caching | prompt caching, budgets, model routing | `docs/08-cost-and-caching.md` |
| 9 | Error handling + resilience | retries, backoff, timeouts, fallbacks | `docs/09-resilience.md` |
| 10 | Security | prompt injection, PII, least privilege, red-teaming | `docs/10-security.md` |
| 11 | Governance as code | policy files, permission engine, CI checks | `docs/11-governance-as-code.md` |
| 12 | AI gateway | LiteLLM proxy, keys, rate limits, routing | `docs/12-ai-gateway.md` |
| 13 | MCP + MCP gateway | MCP servers/clients, gateway pattern | `docs/13-mcp.md` |
| 14 | Deep agent | planning, sub-agents, scratchpad files | `docs/14-deep-agent.md` |
| 15 | Capstone | FastAPI, compose, CI, hardening | `docs/15-capstone.md` |

### Certification support (Claude Certified Developer / Architect)
These run alongside the phases and don't change their order:
- `docs/certifications.md`: exam-domain → phase map, extra practice items, scenario journal (`SCENARIOS.md`), exam timing, and how to gap-check against the official exam guide. The domain data is from third-party sources, so verify it against the official guide.
- `docs/side-tracks.md`:
  - **Track A, Claude Code configuration** (CLAUDE.md, rules, skills, plan mode, hooks, headless/CI). Start after Phase 3.
  - **Track B, Agent SDK and Managed Agents comparison.** Do the SDK slice after Phase 6 and the write-up after Phase 14.
- Extra practice inside existing phases: structured output + validation-retry (Phase 5) and escalation/error-propagation design (Phases 9 and 14).
- Suggested exam timing: Developer after Phase 10, Architect after Phase 15 plus both side tracks.

Estimated effort: about 4–8 hours per phase if you hand-write and read the docs. Phases 0–6 give you a solid working agent. Phases 7–15 harden and extend it.

### Phase doc format
Every phase file has the same sections: **Goal → Concepts (plain English) → Requirements → Steps → Checkpoint (definition of done) → Stretch → Pitfalls → Reading**.

---

## 4. Target repo layout (grows phase by phase)
```
ai-support-agent/
├── PLAN.md  concept.md  docs/
├── pyproject.toml            # managed by uv
├── .env.example  .gitignore  # never commit .env
├── docker-compose.yml        # grows over time
├── data/policies/            # markdown corpus (you create in Phase 3)
├── src/policypal/
│   ├── config.py   llm.py   prompts/
│   ├── rag/        tools/   agent/   memory/
│   ├── guardrails/ governance/  api/
├── evals/        datasets/ judges/ run_evals.py
├── policies/     # governance YAML (Phase 11)
├── mcp_servers/  # Phase 13
└── tests/
```

---

## 5. Tech choices (and why)

| Need | Choice | Why |
|---|---|---|
| Python tooling | **uv** (installed) with Python 3.12 or 3.13 | Fast, one tool for venv + deps. We pin 3.12/3.13 because some AI libraries lag behind the newest Python (you have 3.15). |
| LLM | **Claude via the `anthropic` SDK** | Your requirement. Model ID is read from an env var so you can swap models. |
| Observability | **Langfuse** (self-host via docker compose) | Open source, great tracing + eval UI. |
| Vector DB | **Qdrant** (docker) | Simple, real server, teaches compose. |
| Embeddings | **fastembed** or **sentence-transformers** (local) | Anthropic has no embeddings endpoint; a local model is free. |
| Evals | Plain Python + pytest first, then Langfuse datasets | Understand the mechanics before adopting a framework. |
| Gateway | **LiteLLM proxy** | Open source, OpenAI-style gateway with keys, budgets, fallbacks. |
| MCP | official **`mcp`** Python SDK | Reference implementation. |
| API | **FastAPI** + pydantic | Standard, and teaches type hints. |
| Storage | **Postgres** | History + memory. |

**Model choice for learning:** Phases 1–4 are cheap on any model. Keep the model in `.env` (`ANTHROPIC_MODEL`). Suggested: start with `claude-opus-5-5` for best quality. When you reach Phase 8 (cost), you'll test cheaper options such as `claude-sonnet-5-5` and `claude-haiku-5-5` against your eval set and decide with data. **Check current pricing and set a spend limit in the Anthropic Console before you start.**

---

## 6. How to work through a phase
1. Read the phase doc fully once, with no coding.
2. Build the **Steps** in order. Try for 20+ minutes before asking for help.
3. Run the **Checkpoint**. If it's not met, don't move on.
4. Write 5 lines in `NOTES.md`: what you learned and what surprised you. This is the highest-value habit in the whole plan.
5. Commit and tag.

When you want help, use prompts like: *"Review my `llm.py` for bugs, don't rewrite it"* or *"Explain what `async with` does in my own code"* or *"Give me a hint for step 4, not the solution."*

---

## 7. Assumptions I made (tell me if any are wrong)
1. **Language:** Python, pip/uv-style project, running on macOS with Docker available.
2. **Corpus:** you'll write or generate fake company docs (I give you a recipe in Phase 3). No real company data.
3. **Orders/tickets:** backed by a fake local database, not a real system.
4. **Cloud:** everything runs locally. No AWS/GCP deployment in this plan.
5. **Depth:** conceptual understanding plus working code, not production-grade scale.

### Open questions for you
- Is a **Docker-based Postgres** fine for history/memory, or do you prefer SQLite to start? (Default: SQLite in Phase 7, Postgres in Phase 15.)
- Do you want a **web UI** at the end (e.g. a minimal Streamlit/Chainlit page), or is CLI + API enough? (Default: CLI + API.)
- Are you OK with **local embedding models** (about 100–500 MB download)? (Default: yes.)

If you don't answer, I'll go with the defaults.

---

## 8. Glossary starter (more in each phase)
- **Token:** chunk of text (~¾ of a word). You pay per token, and context windows are measured in tokens.
- **Context window:** the max tokens the model can see in one request (prompt + history + output).
- **System prompt:** standing instructions that frame every conversation.
- **RAG:** retrieve relevant docs first, then give them to the model with the question.
- **Eval:** an automated test for AI behavior, scored on a dataset.
- **Trace / span:** a record of one request, and its sub-steps (LLM call, tool call, retrieval).
- **Agent:** an LLM in a loop that can call tools until the task is done.
- **MCP:** a standard protocol for exposing tools/data to LLM apps.
