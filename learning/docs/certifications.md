# Certification map — Claude Certified Developer & Architect

Goal: use the project as hands-on prep for Anthropic's certifications without changing the build order.

> **Caveat:** domain names and weights below come from third-party prep sites, not an official Anthropic guide (I couldn't find one publicly). Before you rely on this file, get the **official exam guide** (reportedly distributed via Anthropic's training platform / partner network) and re-check the table. Also confirm eligibility: some sources say the Architect exam is limited to the Claude Partner Network. I found no reliable information on the Architect – Professional level. Revisit this file once you have its guide.

---

## 1. Claude Certified Developer – Foundations (reported blueprint)

| Domain (weight) | Where you practice it |
|---|---|
| Applications & Integration (~33%): messages, tools, streaming, vision, thinking, caching, batch, error types and recovery, config | Phases 1, 5, 8, 9 (+ Phase 15 for the service wrapper) |
| Model Selection & Optimization (~17%) | Phase 8 (model/effort sweeps, cost-vs-quality table) |
| Agents & Workflows (~15%): agent loops, harnesses, managed deployment | Phases 6, 14, Side track B |
| Prompt & Context Engineering (~11%) | Phases 1, 3, 7 |
| Tools & MCP (~11%): tool descriptions, error handling, MCP server development | Phases 5, 13 |
| Security & Safety (~8%) | Phase 10 |
| Claude Code (~3%) | Side track A |
| Eval, Testing & Debugging (~3%) | Phases 2, 4 |

**Study emphasis:** the biggest domain is API mechanics. Make sure you can do these **from memory**, without docs: a messages call with system prompt and history, streaming, `stop_reason` handling, tool-use round trip, prompt caching with `cache_control` and verification via usage fields, batch API, thinking/effort settings, structured outputs, and mapping each SDK exception to the right recovery strategy.

## 2. Claude Certified Architect – Foundations (reported blueprint)

| Domain (weight) | Where you practice it |
|---|---|
| Agentic Architecture & Orchestration (~27%): loops, subagents, autonomy vs escalation | Phases 6, 14, Side track B |
| Claude Code Configuration & Workflows (~20%): CLAUDE.md hierarchy, rules, skills, plan mode, CI/CD | Side track A, Phase 15 CI |
| Prompt Engineering & Structured Output (~20%): explicit criteria, few-shot, JSON schema via tools, validation-retry loops, batch and multi-pass review | Phases 1, 3, 5 (Extra 1 below), 4 |
| Tool Design & MCP Integration (~18%): tool descriptions, structured error responses, distributing tools across agents, MCP config | Phases 5, 13, 14 |
| Context Management & Reliability (~15%): long conversations, escalation patterns, error propagation in multi-agent setups | Phases 7, 9 (Extra 2 below), 14 |

The exam is reportedly **scenario-based**, so the practice that matters is making and defending design decisions. See §4.

## 3. Extra practice items (small additions to existing phases)

**Extra 1: Structured output with validation-retry loop** (do inside Phase 5)
- Build an extraction task: turn a free-text customer email into `{intent, order_id, urgency, requested_action, needs_human}`.
- Enforce the schema three ways and compare: a tool-use schema, `output_config` structured output, and prompt-only JSON.
- Validate with pydantic. On failure, retry with the validation error fed back, bounded to 2 attempts, and record the repair rate.
- Add explicit-criteria prompts and 2–3 few-shot examples for ambiguous cases ("is this a refund request or a complaint?"). Measure false positives before and after.
- Run the same extraction over 50 emails with the Batch API and a multi-pass review (second call checks the first). Compare cost and accuracy with single-pass.

**Extra 2: Escalation and error-propagation design** (do inside Phase 9 / Phase 14)
- Write an **escalation policy** doc: when the agent must hand off to a human (low retrieval confidence, repeated tool errors, user asks, policy-sensitive topics, high-value refunds). Implement a `handoff_to_human` path that packages context (question, steps taken, sources, what failed).
- Give tool errors a structure, e.g. `{error_category, is_retryable, message}`. The model should be able to tell "retry" from "give up" from "ask the user".
- For Phase 14: when a sub-agent fails, define exactly what the lead receives (error summary, partial results) and test that failure doesn't silently turn into a confident wrong answer.

## 4. Scenario journal (do after every phase)

Add a `SCENARIOS.md` file. After each phase write 2 entries in this format:

```
Scenario: <a realistic situation, 2-3 lines>
Options considered: A / B / C
Decision + why: ...
What would change my mind: ...
```

Examples to seed it:
- Support bot answers refund questions wrongly 8% of the time. Prompt, retrieval, or tool problem? How do you find out?
- 5,000 conversations/day, 70% repetitive FAQs. Where do caching, routing, and batch fit?
- One agent with 30 MCP tools is picking wrong tools. Fix by description, by splitting agents, or by tool search?
- A sub-agent returns a plausible but unsourced claim. What controls catch it?
- Long conversation starts forgetting early constraints. Summarize, edit context, or memory?

Aim for ~30 entries by the end. They double as revision notes.

## 5. Suggested exam timing
1. **Developer – Foundations:** after Phase 10, plus Side track A basics. Spend about a week on a targeted review of the API-mechanics list in §1.
2. **Architect – Foundations:** after Phase 15 and both side tracks. Spend about a week on the scenario journal, reviewing every entry and writing the missing domains.
3. **Architect – Professional:** decide after you've read its official guide.

## 6. Gap-check routine
When you get an official exam guide:
1. List its domains and sub-topics in a table.
2. Map each to a phase, a side track, or "none".
3. For every "none", add a small exercise here. Don't add new phases.
4. Re-run this check whenever Anthropic publishes a new guide version.
