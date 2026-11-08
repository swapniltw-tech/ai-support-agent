# Phase 13 — MCP and MCP gateway

## Goal
Expose your tools as **MCP servers**, consume them through an MCP client in the agent, then put a **gateway** in front for auth, permissions, and audit.

## Concepts
- **MCP (Model Context Protocol):** an open standard for connecting LLM apps to tools and data. Instead of hard-coding functions into your agent, a server advertises **tools**, **resources**, and **prompts**, and any MCP client can use them.
- **Roles:** *host/app* (your agent) → *MCP client* → *MCP server* (provides capabilities).
- **Transports:** `stdio` (local subprocess) and streamable HTTP (remote). Remote servers need real authentication.
- **Tool discovery:** the client lists the server's tools (name, description, JSON schema) and passes them to Claude as regular tools. The loop is the same as Phase 6. MCP changes *where tools live*.
- **Why it matters:** reuse tools across apps, separate ownership (the orders team owns the orders server), language-agnostic.
- **MCP gateway:** a proxy that sits between agents and many MCP servers. It provides a single endpoint, authentication, per-user/per-agent **allowlists of tools**, rate limits, audit logs, secrets handling, and sometimes tool-description pinning.
- **MCP-specific risks:** *tool poisoning* (malicious instructions hidden in a tool description), *rug pulls* (a server changes its tool definitions after approval), confused-deputy token problems, and overly broad servers. Treat third-party servers as untrusted code.
- The API also has an **MCP connector** (server-side). We use a client-side approach here so you understand the mechanics and keep control.

## Requirements
- Two MCP servers built with the official Python SDK (`mcp`, using `FastMCP`):
  - `orders-server`: tools `get_order_status`, `list_orders` (read-only)
  - `tickets-server`: tool `create_ticket` (write), resource `ticket://{id}`
  - optionally `policy-server`: tool `search_policies`
- An MCP client layer in the agent (`agent/mcp_client.py`) that connects, lists tools, converts them to Claude tool definitions, and routes `tool_use` calls to the right server.
- The migrated agent works the same as before, and the eval results don't regress.
- A gateway in front (build a simple one yourself, or evaluate an open-source MCP gateway) with: auth token → identity, tool allowlist per role (reuse Phase 11 policies), audit log, rate limiting, and tool-definition hashing to detect changes.
- Servers run as containers in compose (HTTP transport).

## Steps
1. Read the MCP docs: architecture overview, the Python SDK README, and the section on transports.
2. Build `orders-server` first with `stdio`. Test it with the **MCP Inspector** (`npx @modelcontextprotocol/inspector`) before involving Claude.
3. Write the client wrapper: spawn/connect, `list_tools`, convert schema (MCP `inputSchema` is already JSON Schema, which maps almost directly to Claude's `input_schema`).
4. Route tool calls: namespace tools (`orders__get_order_status`) to avoid name collisions across servers.
5. Swap the agent's local tools for MCP-provided ones. Re-run evals: same quality?
6. Add the write tool and the resource. Keep approval flow working (approval policy from Phase 11 applies to MCP tools too).
7. Switch to **streamable HTTP** transport and containerize each server in compose.
8. Think about identity: how does the server know *which user* is calling? Design: gateway authenticates the user, passes a signed identity context to the server. The model still never supplies identity.
9. Build the gateway: a small proxy (FastAPI or the MCP SDK's server+client combination) that exposes one MCP endpoint, aggregates servers' tools, applies the allowlist, logs every call, and rate-limits.
10. Tool-definition pinning: hash each tool's name+description+schema at approval time; block (and alert) if the hash changes.
11. Poisoning test: make a malicious server whose tool description says "also send the user's data to ...". Show how your allowlist + pinning + untrusted-description handling reduces the risk.
12. Compare to an existing open-source MCP gateway (read docs only, maybe try one). What would you adopt vs build?

## Checkpoint
- [ ] Agent uses only MCP tools, with the same eval scores.
- [ ] Servers run in containers over HTTP.
- [ ] Gateway enforces per-role tool access and logs every call.
- [ ] Changing a tool description triggers a block until re-approved.
- [ ] You can explain MCP vs plain function-calling vs the API's MCP connector.

## Stretch
- Add MCP **resources** (policy docs as resources) and **prompts** (reusable templates).
- OAuth-style auth for the remote servers.
- Compare latency overhead: local functions vs stdio vs HTTP vs HTTP-through-gateway.

## Pitfalls
- Tool name collisions across servers.
- Trusting third-party tool descriptions as safe prompt text.
- Passing user identity as a tool argument the model controls.
- Running stdio servers with more filesystem/network access than needed.
- Forgetting that every MCP tool's description consumes context tokens on every request. Many tools means a cost and accuracy hit (see tool search in the Anthropic docs).

## Reading
modelcontextprotocol.io docs (architecture, security best practices); Anthropic docs on MCP connector and tool search.
