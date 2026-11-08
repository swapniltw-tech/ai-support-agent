# Phase 6 — Agent loop engineering

## Goal
Turn the manual tool dance from Phase 5 into a robust, bounded agent loop you fully understand and control.

## Concepts
- **Agent = LLM + tools + loop.** The loop: call model → if it wants tools, run them, append results → repeat → stop when it answers.
- **Stop conditions:** natural (`end_turn`), and *forced*: max steps, max tokens, max wall-clock time, max cost, repeated-identical-call detection.
- **Workflow vs. agent:** a workflow is code-controlled steps (e.g. classify → retrieve → answer). An agent lets the model decide the steps. Prefer the simplest thing that works. Use an agent only where flexibility is needed.
- **Stop reasons to handle:** `end_turn`, `tool_use`, `max_tokens` (truncated, maybe continue or fail), `pause_turn`/`refusal` (respect them).
- **Loop failure modes:** infinite tool loops, tool-thrash, ignoring errors, context growing every step, giving up too early.
- **Observability of loops:** each iteration is a span; the whole run is one trace.
- **Human-in-the-loop (HITL):** pausing before risky tool calls for approval.

## Requirements
- `agent/loop.py` with `run_agent(user_message, history, ctx) -> AgentResult` (answer, steps, tokens, cost, stop_reason, tool_calls).
- Hard limits via a `Limits` config: `max_steps` (e.g. 8), `max_total_tokens`, `timeout_s`.
- Loop-detection: stop if the same tool+args repeats ≥3 times.
- Tool execution through your registry, with parallel calls handled (concurrently if independent. Start sequential).
- Approval hook: `create_ticket` requires confirmation via a callback (CLI prompts `y/n`).
- Graceful degradation: if limits hit, return an honest "I couldn't finish; here's what I found + escalation" response, never a crash or a silent cut.
- Full trace: parent trace → per-step generation spans → tool spans.

## Steps
1. Write the loop as a plain `while` with a step counter. No frameworks, no tool-runner helper. Append **the full assistant content** each time, then the tool results.
2. Return a rich `AgentResult` dataclass; log each step's stop_reason and token use.
3. Add limits one by one, writing a test for each: a fake "model" function (dependency injection: pass the LLM caller in as a parameter) that keeps asking for tools, to prove the step limit works. Testing agents without paying for API calls is a key skill.
4. Add repeated-call detection (hash of tool name + sorted args).
5. Add the approval hook and a test with an auto-deny callback.
6. Write the final-answer step: when the loop ends by limit, make one last call with "summarize what you know, state what's missing" and no tools.
7. Tune the system prompt for agent behavior: when to search before answering, to cite, to ask clarifying questions rather than guess, and when to escalate to a human.
8. Compare **workflow vs. agent** on your eval set: implement a fixed pipeline (always retrieve → answer) and compare accuracy, steps, tokens, and latency with the agent. Write down which wins and why.
9. Add multi-turn: pass prior `messages` into the loop (full memory design is Phase 7).
10. Extend evals with trajectory checks: did it call the right tools, within N steps, without unnecessary calls?

## Checkpoint
- [ ] Agent answers multi-tool questions end to end.
- [ ] Each limit is covered by a unit test using a fake model.
- [ ] A trace shows every step with timing and tokens.
- [ ] Workflow-vs-agent comparison table is in `NOTES.md`.
- [ ] Unapproved write calls never execute.

## Stretch
- Run independent tool calls concurrently with `asyncio.gather`.
- Stream the final answer while tools run in earlier steps.
- Add "reflection": a self-check pass that verifies the draft against retrieved context before sending.

## Pitfalls
- Dropping `tool_use` blocks when appending the assistant turn, which breaks the next request.
- Unbounded context growth within a single run (large tool results). Truncate or summarize results.
- Ignoring `max_tokens` truncation mid-tool-call.
- Letting limits live only in the prompt ("don't use more than 5 steps"). Enforce in code.
- Building a complex agent where a 3-step workflow would do.

## Reading
Anthropic: "Building effective agents" (essay) and the tool-use docs on the agentic loop.
