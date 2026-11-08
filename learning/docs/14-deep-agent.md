# Phase 14 — Deep agent

## Goal
Handle **complex, multi-part requests** that overflow a single simple loop, using planning, sub-agents with isolated context, and a scratchpad. Also learn when *not* to.

## Concepts
- **"Deep" agent pattern:** four ingredients: (1) an explicit **plan** (todo list) the agent updates, (2) **sub-agents** that do focused work in their own fresh context and return only a short result, (3) a **scratchpad / virtual filesystem** for notes and intermediate artifacts, and (4) a detailed system prompt describing how to work.
- **Context isolation:** a sub-agent can read 30 pages and return a 10-line summary, keeping the lead's context clean. This is the main benefit.
- **Orchestrator–worker:** a lead agent decomposes the task, delegates, and synthesizes.
- **Costs:** multi-agent systems burn many more tokens and add latency and failure modes. Use them for tasks that are broad, parallelizable, or context-heavy. Don't use them for a simple lookup.
- **Example tasks here:** "Compare our remote-work, expense, and security policies and list conflicts or gaps", "Prepare a briefing on all rules affecting a new contractor's first week", "Audit the handbook for outdated sections."
- **Termination and budgets** matter even more. Every sub-agent needs its own limits, plus a global budget.
- Libraries exist (LangChain "deepagents", Claude Agent SDK, managed offerings). We hand-build a small version first. Afterwards you can compare with a library and decide.

## Requirements
- `agent/deep/` module with:
  - **Planner tools:** `write_todos` / `update_todo` (state kept in run context)
  - **Scratchpad tools:** `write_note`, `read_note`, `list_notes` (an in-memory or temp-dir virtual FS, per run)
  - **`delegate(task, tools, budget)`** which runs a fresh sub-agent loop (reuse Phase 6's `run_agent`) and returns its final text only
- Roles: `researcher` (retrieval-heavy, read-only tools), `analyst` (reads scratchpad notes, finds conflicts), `writer` (final report). Each has its own system prompt and tool allowlist.
- Global limits: max sub-agents, depth 1 (no recursive spawning), per-sub-agent step/token limits, total cost cap.
- Parallel delegation for independent sub-tasks.
- Final output is a structured report with citations.
- Whole run is one trace, with sub-agents as nested spans.
- Routing: simple questions use the Phase 6 agent. Only "complex" ones enter deep mode, decided by a cheap classifier or explicit flag.

## Steps
1. Write 6–8 complex test tasks and define what a good output contains. Add them to a separate eval set (`evals/datasets/deep.jsonl`) with rubric-based judging (the Phase 4 judge pattern).
2. **Baseline first:** run the single-agent loop on them. Record quality, steps, tokens, cost. You need this to know whether the deep design is worth it.
3. Implement scratchpad tools and a todo tool. Give the single agent these and see if planning alone improves results.
4. Implement `delegate`: build the sub-agent's system prompt, tool subset, and limits, call `run_agent`, return only the final summary. Verify context isolation by comparing token counts in the lead versus in the sub-agents.
5. Add role prompts and tool allowlists (governance policy from Phase 11 should govern which roles may use which tools).
6. Add parallelism for independent delegations with `asyncio.gather` and a concurrency cap.
7. Add global budgets and failure handling: a sub-agent that fails or times out yields an error summary. The lead decides whether to retry, proceed with a caveat, or abort.
8. Prompt the lead agent with explicit guidance: when to delegate, how to write good delegation briefs (goal, context, expected output format, what to avoid), and to verify sub-agent claims against sources before finalizing.
9. Compare on your deep eval set: baseline vs +planning vs +sub-agents. Table: quality, cost, latency, steps.
10. Security pass: sub-agent outputs are untrusted data for the lead (a poisoned doc can propagate). Apply Phase 10 delimiters and checks to delegation results.
11. Do **Side track B** from `docs/side-tracks.md`: run the same tasks on the Claude Agent SDK, compare with your hand-built version using your eval set, and write the decision guide. Also do the sub-agent failure-propagation exercise from `docs/certifications.md` (Extra 2).

## Checkpoint
- [ ] Deep mode beats the baseline on at least some complex tasks, and you have numbers on the cost.
- [ ] Sub-agent context is isolated (lead's context stays small).
- [ ] Global and per-agent limits hold under a stress test.
- [ ] Simple questions don't enter deep mode.
- [ ] You can state clearly when deep agents are *not* worth it.

## Stretch
- Allow the lead to ask the user clarifying questions before planning.
- Checkpoint and resume long runs (persist the plan + scratchpad).
- Skills-style loading: give sub-agents domain playbooks loaded on demand.

## Pitfalls
- Sub-agents returning too much text and defeating the isolation.
- Vague delegation briefs → garbage results.
- Unbounded fan-out (cost explosion).
- Trusting sub-agent claims without sources.
- Using deep mode because it's cool, not because it's needed.

## Reading
Anthropic: "How we built our multi-agent research system" and "Building effective agents".
