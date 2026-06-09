# MCP Client Setup

Before this skill can do anything useful, your AI agent's MCP client needs
to know how to reach the Connect Usage MCP endpoint and how to authenticate.

## What you need

1. **An API token** scoped to the account doing the work — vendor account
   for upload/submit flows, provider account for accept/close/reconcile.
   Create it in the Connect UI → Account → Tokens, and grant the relevant
   product/usage scopes.
2. **An MCP-capable AI agent.** Claude Code, Claude Desktop, or any client
   that speaks the MCP protocol over HTTP.

The Connect endpoint is fixed at `https://api.connect.cloudblue.com`.

## Claude Code (CLI)

Add an entry to `~/.mcp.json` (or your project's `.mcp.json`):

```json
{
  "mcpServers": {
    "connect-usage": {
      "type": "http",
      "url": "https://api.connect.cloudblue.com/public/v1/mcp/usage/",
      "headers": {
        "Authorization": "ApiKey SU-XXXX-XXXX-XXXX:<your-secret>"
      }
    }
  }
}
```

Restart Claude Code. Verify the connection with:

```
/mcp
```

You should see `connect-usage` in the list, and a `ping` tool that returns
`{"ok": true}`.

## Claude Desktop

Open Claude Desktop's settings, go to **Developer → Edit Config**, and
add the same `mcpServers` entry under the existing JSON. Restart Claude
Desktop.

## Other MCP clients

Anything that follows the standard MCP HTTP transport works. The endpoint
expects:

- `POST` to `/public/v1/mcp/usage/`
- JSON-RPC 2.0 payload with `tools/list`, `tools/call`, `initialize` methods
- `Authorization: ApiKey <token>` header

## Verifying the setup

Once configured, ask your agent:

> "Ping the Connect usage MCP server."

The agent should call the `ping` tool and report `{ok: true}`. If it
errors with 401, the token isn't valid. If it errors with 404, the URL is
wrong or your environment hasn't been provisioned with the MCP Ingress
path yet — contact your CloudBlue administrator.

## Troubleshooting

- **`tools/list` returns empty** → the MCP endpoint is reachable but no
  tools registered. Contact CloudBlue; the deployment is incomplete.
- **`401 Unauthorized`** → token invalid, expired, or wrong scope. Mint a
  new one with the right account context.
- **`403 Forbidden` on a specific tool** → the token's account doesn't
  have the right role for that action. Vendor tokens can't call
  `accept_usage_file`; provider tokens can't call `delete_usage_file`.
- **Slow responses** → MCP tools loop back to REST internally; each call
  costs one round trip (~50–200 ms). Expect 5–10 seconds for a full
  validate + create + upload + submit chain.
