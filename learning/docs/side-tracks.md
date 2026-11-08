# Side tracks (run alongside the main phases)

Two short tracks that fill the certification gaps found in `docs/certifications.md`. Neither blocks the main build.

---

# Side track A — Claude Code configuration & workflows

**When:** start after Phase 3 (you have a real codebase to configure), finish by Phase 15.
**Effort:** 4–6 hours total, split into small pieces.

## Goal
Use Claude Code as a tool on this repo and learn how to configure it for a team: shared instructions, scoped rules, skills, safe planning, and CI integration.

## Concepts
- **CLAUDE.md:** persistent project instructions Claude Code loads at start. They exist at several levels (user-level, project-level, and in subdirectories), and more specific levels add to the broader ones. Read the memory docs for the exact hierarchy and precedence. Don't guess.
- **Rules files** (`.claude/rules/`): instructions that apply only to matching paths (e.g. tests vs. policies). Check the docs for the frontmatter format.
- **Skills:** packaged, reusable instructions (and optionally scripts) Claude loads when relevant. They can restrict which tools they may use.
- **Plan mode vs. direct execution:** plan mode lets Claude research and propose before touching files. Use it for risky or multi-file changes, and direct execution for small, clear edits.
- **Permissions and settings:** allow/deny lists for commands, so safe commands don't prompt and dangerous ones are blocked.
- **Hooks:** automatic actions on events (e.g. run `ruff` after edits).
- **Headless / CI mode:** running Claude Code non-interactively in a pipeline (e.g. automated review on pull requests).
- **Subagents** inside Claude Code: specialized helpers with their own context and tool limits (the same idea as your Phase 14 sub-agents).

## Steps
1. Read the official Claude Code docs sections for: memory/CLAUDE.md, settings and permissions, skills, subagents, hooks, and headless usage. Take notes in `SCENARIOS.md`.
2. Write the project `CLAUDE.md` (short and specific: how to run tests and evals, code style, directory map, "never commit .env", "evals must pass before prompt changes"). Test whether Claude follows it. Remove lines that don't change behavior.
3. Add a subdirectory-level instruction file for `policies/` or `evals/` and confirm it applies only there. Add one path-scoped rule.
4. Create one **custom skill**, for example `add-eval-case` (given a failed trace, produce a dataset row in your format). Restrict its tools and test it.
5. Set up permissions: allow `uv run pytest`, `uv run ruff`, deny reading `.env`. Verify a denied action is actually blocked.
6. Add a hook that runs `ruff format` or tests after edits. Break something deliberately to see it fire.
7. Use **plan mode** for a real change (e.g. add a new tool end-to-end). Compare the experience to direct execution on the same type of change. Write down when each was better.
8. Create a subagent for code review with a read-only tool set.
9. Run Claude Code headless in a script on a sample diff and capture output as JSON. Then wire an optional CI job for automated review (Phase 15). Keep cost in mind: use a small diff and a cheaper model.

## Checkpoint
- [ ] CLAUDE.md, one scoped rule, one skill, permissions, and one hook all work and are committed.
- [ ] You can explain the configuration hierarchy and when you'd use plan mode vs direct execution.
- [ ] You ran Claude Code non-interactively once.
- [ ] 5+ scenario entries about Claude Code decisions in `SCENARIOS.md`.

## Pitfalls
- Giant CLAUDE.md files. Context is a budget, so keep only lines that change behavior.
- Putting secrets or machine-specific paths in shared project config.
- Overly broad permissions "to stop the prompts".

---

# Side track B — Agent SDK and Managed Agents comparison

**When:** after Phase 6 for the Agent SDK, after Phase 14 for the comparison write-up. Managed Agents is a reading plus optional small build.
**Effort:** about 4–6 hours.

## Goal
Understand the four ways to build an agent and be able to choose between them. This is a typical architect-level question.

## The four approaches
| # | Approach | You own | Use when |
|---|---|---|---|
| 1 | Manual loop on the Messages API (what you built in Phase 6) | The loop, tools, hosting | Full control, custom tools only |
| 2 | Messages API tool-runner helper in the SDK | Tools and hosting; SDK runs the loop | Same as 1, less boilerplate |
| 3 | **Claude Agent SDK** (separate package, Claude Code's harness as a library) | Your prompt/options and hosting; it supplies the loop, built-in tools (files, shell, search), context handling, subagents, hooks | Coding/file-heavy agents on your own infrastructure |
| 4 | **Managed Agents** | Agent config; Anthropic runs the loop and hosts the sandbox | You want hosted, long-running, versioned agents |

(Details change, so verify against the current docs for each.)

## Steps
1. Read the official docs for the Agent SDK (Python package `claude-agent-sdk` at the time of writing, so confirm the name) and Managed Agents. Note the primitives each exposes: tools, permissions, sessions, subagents, hooks.
2. **Agent SDK exercise:** rebuild a slice of PolicyPal, such as the policy-research task from Phase 14, with the Agent SDK. Expose your retriever as a custom tool (SDK-supported tool/MCP mechanism, per the docs) and restrict built-in tools to what's needed.
3. Run it on the same inputs as your hand-built version. Compare: lines of code, quality (use your eval), cost, latency, observability (can you still trace it?), and control (limits, approvals, budgets).
4. **Managed Agents reading/mini-build:** define one agent with a system prompt and a read-only toolset, start a session, and watch the event stream. If your account lacks access, do the reading only and write the comparison from the docs.
5. Write a 1-page decision guide in `docs/agent-approach-decision.md` (your own words): for each of the four approaches, when you'd choose it for PolicyPal and for a different product (e.g. a code-migration bot, a nightly report agent).
6. Add 5+ scenario entries to `SCENARIOS.md`.

## Checkpoint
- [ ] The same task runs on both your loop and the Agent SDK, with an eval comparison.
- [ ] Decision guide written.
- [ ] You can explain who hosts what in each of the four approaches.

## Pitfalls
- Confusing the **tool-runner helper** (in the regular API SDK) with the **Agent SDK** (a different product).
- Assuming the SDK gives you the same governance, budgeting, and tracing for free. Check what you'd have to re-add.
- Comparing on one example. Use your eval set.
