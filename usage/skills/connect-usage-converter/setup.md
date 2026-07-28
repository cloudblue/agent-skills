# MCP Client Setup

Full setup — minting a token, permissions, client configuration, and
connection troubleshooting — lives in the **`connect-mcp-setup`** skill
(`core` plugin in this same marketplace). Install it with:

```
/plugin install core@cloudblue-agent-skills
```

The short version: all of Connect is one MCP endpoint. Add to
`~/.mcp.json` (or the project's `.mcp.json`):

```json
{
  "mcpServers": {
    "connect": {
      "type": "http",
      "url": "https://api.connect.cloudblue.com/public/v1/mcp",
      "headers": {
        "Authorization": "ApiKey SU-XXXX-XXXX-XXXX:<your-secret>"
      }
    }
  }
}
```

There are no per-module URLs — older configs pointing at
`/public/v1/mcp/usage/` are stale and must use the single endpoint above.

Usage-specific note: the token's account decides which side of the flow
you can act on. Upload/validate/submit needs a **vendor**-account token;
accept/close/reconcile needs a **provider**-account token. The token must
carry the **MCP** permission plus the **Usage** module permission.
