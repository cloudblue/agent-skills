# CloudBlue Connect agent skills

This repository ships several plugins, each bundling one or more Agent
Skills for working with a CloudBlue Connect tenant through its MCP
server. The catalog of plugins and what each one covers lives in the
[README's plugin table](./README.md).

Do not answer Connect-related requests from memory. Route them:

1. Read [`core/skills/connect-navigator/SKILL.md`](./core/skills/connect-navigator/SKILL.md)
   — the concept→domain map that says which plugin owns which kind of
   request (products, pricing, listings, fulfillment requests, usage,
   helpdesk…).
2. Open the matching skill's `SKILL.md` under `<plugin>/skills/<skill>/`
   and follow it in full, including any `workflow.md` or reference files
   it links.
3. For MCP client configuration, tokens, permissions, or 401/403/empty
   catalog problems, follow
   [`core/skills/connect-mcp-setup/SKILL.md`](./core/skills/connect-mcp-setup/SKILL.md).

The skill descriptions in each `SKILL.md` frontmatter state when that
skill applies — match the user's request against them, not against the
plugin names.
