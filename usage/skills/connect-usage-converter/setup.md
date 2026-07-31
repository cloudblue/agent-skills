# MCP Client Setup

Setup and connection troubleshooting are the **`connect-mcp-setup`** skill's
job (`core` plugin in this same marketplace) — the single endpoint, minting the
token, the client config for Claude Code and Claude Desktop, and the
`401`/`403`/`404` diagnosis table all live there. Install it with:

```
/plugin install core@cloudblue-agent-skills
```

Two things that skill cannot know, because they are specific to usage
reporting:

- **The token needs the MCP permission plus the Usage module permission.**
- **The account decides which leg you can work.** Validate, upload and submit
  need a **vendor**-account token. Accept, reject, reconcile and close are the
  **provider**'s and will `403` from a vendor token — that is the wrong-side
  case, not a broken setup.
