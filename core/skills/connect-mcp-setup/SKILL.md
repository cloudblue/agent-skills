---
name: connect-mcp-setup
description: Use when connecting an agent to the CloudBlue Connect MCP server for the first time, or when a Connect connection stopped working — the client config, the API token and its module permissions, and the error diagnosis. Owns the Connect permission model. Triggers on "set up Connect MCP", "my Connect token gets 403", "no Connect tools show up", or whenever another skill hands over a 401/403.
version: 0.1.0
license: Apache-2.0
metadata:
  hermes:
    tags: [CloudBlue, Connect, MCP, Setup, Authentication]
    category: productivity
    related_skills: [connect-navigator]
---

# Connect MCP Setup

You are helping the user connect their MCP client to CloudBlue Connect, or
diagnosing a connection that doesn't work. This is a configuration skill:
the key steps — minting a token, editing client config — happen in the
Connect UI and on the user's machine, so you guide and verify rather than
execute. No Connect tools are needed beyond listing them to verify.

## The one endpoint

All of Connect is reachable through a single MCP endpoint:

```
POST https://api.connect.cloudblue.com/public/v1/mcp
Authorization: ApiKey SU-XXXX-XXXX-XXXX:<secret>
```

One entry in the client's MCP config exposes the whole catalog —
roughly 100 tools spanning nine domains (pricing, fulfillments, products,
listings, usage, helpdesk, tier accounts, marketplaces, assets).

There are **no per-module URLs**. If a config, doc, or old example points
at a path with a module segment after `mcp` (`/public/v1/mcp/<module>/`),
it is stale — replace it with the single endpoint above.

## Mint the token

In the Connect UI: **Account → Tokens → Create token**.

Two permission rules decide what works:

1. The token must carry the **MCP** permission. Without it, *every* tool
   call returns `403`, regardless of what else the token can do.
2. Each tool additionally requires the permission of the **module that owns
   its domain** — enforced by visibility, not by `403`: the gateway omits
   the tools of unpermitted modules from the catalog. A token with MCP but
   without Pricing sees no `pricing_*` tools at all, and calling one by
   name returns `MCG_001` "Unknown tool". One known pairing to be aware
   of: the `fulfillments` and `assets` domains are both covered by the
   **Subscriptions** permission.

So: grant MCP plus the modules the user actually intends to work with. The
tools visible in the catalog reflect the token's module permissions — a
smaller-than-expected catalog usually means a narrower-than-expected token.

Token scoping also decides *which side* of a transaction you act as: a
vendor-account token cannot perform provider-side actions and vice versa.
Mint the token in the account that does the work.

## Configure the client

### Claude Code

Add to `~/.mcp.json` (or the project's `.mcp.json`):

```json
{
  "mcpServers": {
    "connect": {
      "type": "http",
      "url": "https://api.connect.cloudblue.com/public/v1/mcp",
      "headers": {
        "Authorization": "ApiKey ${CONNECT_API_KEY}"
      }
    }
  }
}
```

`.mcp.json` expands environment variables, so keep the secret out of the
file (project configs get committed): export
`CONNECT_API_KEY="SU-XXXX-XXXX-XXXX:<secret>"` in the shell profile
instead of pasting the token inline.

Restart Claude Code, then check with `/mcp` — `connect` should appear in
the server list.

### Claude Desktop

The Developer config file only accepts local stdio servers — the HTTP
entry above will not work there. Use **Settings → Connectors → Add custom
connector** instead: paste the endpoint URL and add a request header
`Authorization: ApiKey SU-XXXX-XXXX-XXXX:<secret>`.

### Any other MCP client

Anything speaking standard MCP HTTP transport works: JSON-RPC 2.0
(`initialize`, `tools/list`, `tools/call`) POSTed to the endpoint with the
`Authorization: ApiKey <token>` header.

## Verify

Ask the agent to list the Connect tools. A healthy setup returns a catalog
whose domains match the token's module permissions. If the user's token
carries every module, expect on the order of 100 tools.

## Diagnose

Work top-down; each symptom has one dominant cause.

| Symptom | Cause | Fix |
|---|---|---|
| `401 Unauthorized` on everything | Token invalid, expired, or the header is malformed | Re-check the `ApiKey SU-…:<secret>` header; mint a fresh token if needed |
| `403` on **every** tool | Token lacks the **MCP** permission | Re-mint with MCP granted |
| `MCG_001` "Unknown tool" on a call | Typo in the tool name, **or** the token lacks the owning module's permission — unpermitted tools are hidden from `tools/list`, so both cases return the exact same error | Run `tools/list`: if the domain's other tools are present, fix the name; if the whole domain is absent, add the module to the token (fulfillments + assets → Subscriptions) |
| `403` on one specific action | The token's account is on the wrong side of the transaction (e.g. vendor token calling a provider-only action) | Use a token from the account that owns the action |
| `tools/list` is empty | Token carries MCP but no module permissions, or the environment's MCP deployment is incomplete | Check the token's modules first; if they look right, contact the CloudBlue administrator |
| `tools/list` is empty but the token shows **"All modules"** | The blanket "All" grant (`MD-0000`) is excluded from the permission set the gateway sees — a token holding only "All" resolves to zero modules, silently, with an HTTP 200 | Re-mint the token selecting each needed module **by name**; never rely on the "All" option for MCP |
| `404` | Wrong URL — usually a stale per-module path | Use `https://api.connect.cloudblue.com/public/v1/mcp` |
| Whole chains feel slow | Each tool call is one REST round trip (~50–200 ms); multi-step workflows take seconds | Expected; not a fault |

## Non-goals

What the tools do, and how to sequence them, is out of scope — that is the
job of the domain skills (usage conversion, pricing, products, …). This
skill ends when `tools/list` returns the catalog the token should see.
