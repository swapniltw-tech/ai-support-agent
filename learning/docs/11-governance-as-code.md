# Phase 11 — Governance as code

## Goal
Move rules about what the AI may do, say, and spend out of prompts and scattered `if` statements into **versioned, reviewable, testable policy files** enforced at runtime and in CI.

## Concepts
- **Governance as code:** policies live in the repo (YAML/Rego), are reviewed in pull requests, tested, and enforced automatically. Auditors can see *what the rule was at any commit*.
- **Policy vs. prompt:** prompts *request* behavior; policies *enforce* it in code. Anything important must be enforced, not requested.
- **Policy decision point (PDP) / enforcement point (PEP):** one place decides allow/deny/require-approval; call sites ask it and obey.
- **What to govern:** tool permissions by role, approval requirements, data access by audience, allowed models, token/cost budgets, content rules (forbidden claims), retention periods, which prompt versions are approved for production.
- **Auditability:** every decision is logged (who, what, rule matched, outcome) and linked to a trace.
- **Change management:** prompts and policies are versioned artifacts. A change requires passing evals and red-team tests before merge.
- Optional external engines: **Open Policy Agent (OPA)** with Rego, or Cedar. We start with a hand-built YAML engine to understand the idea, and then optionally swap in OPA.

## Requirements
- `policies/` directory with YAML files, e.g.:
  - `tools.yaml`: per tool: allowed roles, `requires_approval`, rate limit, max calls per session
  - `data_access.yaml`: audience → allowed doc tags
  - `models.yaml`: allowed models per route, max tokens, budgets
  - `content.yaml`: forbidden claims/patterns, required disclaimers
  - `retention.yaml`: memory/history TTLs
- JSON-Schema (or pydantic) validation of policy files, so a malformed policy fails fast.
- `governance/engine.py`: `decide(action, context) -> Decision(allow|deny|needs_approval, rule_id, reason)`.
- Enforcement wired into: tool execution (Phase 5/6), retrieval filters (Phase 3), budgets (Phase 8), output checks (Phase 10), memory TTL (Phase 7).
- Audit log (append-only table or JSONL) of every decision, linked to the trace id.
- CI-style checks: policy schema validation, policy unit tests, and "prompt/policy change requires eval pass".

## Steps
1. Inventory every rule you already scattered through code and prompts (approval prompt, audience filter, budgets, forbidden claims). List them in a table with "enforced where?" and "tested?". You'll find gaps.
2. Design the YAML formats. Keep them boring and readable. Give every rule an `id` and a `description`.
3. Write loader + validation (pydantic models for each policy file). Break a file on purpose and confirm a clear error.
4. Write the decision engine as a pure function (no I/O) so it's trivially testable. Table-driven tests: `(role, tool) → decision`.
5. Replace hard-coded checks with engine calls, one area at a time. After each, re-run evals and the red-team suite.
6. Add the audit log and surface decisions as span attributes in Langfuse.
7. Add **policy tests**: `tests/policy/*.yaml` scenarios ("customer + create_ticket high priority → needs_approval"). Run them in CI.
8. Version prompts: `prompts/system.v3.md` with a manifest naming which version is approved per environment. A script refuses to deploy a version with no passing eval record. Store eval result hashes in `policies/approvals.yaml`.
9. Add a `scripts/governance_report.py`: summarizes decisions, denials by rule, approvals pending.
10. Optional: re-implement the tool-permission policy in **OPA/Rego** running in a docker container and compare. When is a full policy engine worth it?

## Checkpoint
- [ ] Changing a YAML rule changes behavior with no code change.
- [ ] Each rule has a test; malformed policies are rejected.
- [ ] Every allow/deny is in the audit log with a rule id.
- [ ] You can answer "what was the refund-claim rule on date X?" via git history.
- [ ] A prompt change without eval approval is refused by the check script.

## Stretch
- Policy simulation: replay last week's traces against a *proposed* policy to see what would have changed.
- Generate a human-readable policy summary from the YAML for compliance review.

## Pitfalls
- Policies so granular nobody can reason about them.
- Enforcement only in the prompt.
- Engine with side effects, making it hard to test.
- Policy and code drifting apart because the policy file isn't actually loaded in one path. Test every enforcement point.
