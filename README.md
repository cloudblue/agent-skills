# agent-skills

A curated collection of Claude Code **plugins** for interacting with
the CloudBlue Connect MCP server. Each plugin is a self-contained folder at
the repo root, carrying its own `.claude-plugin/plugin.json` and one or
more skills under `skills/`. The repo-level
`.claude-plugin/marketplace.json` is the catalog Claude Code reads when
you register the marketplace.

## Plugins in this repo

| Plugin | Purpose |
|---|---|
| [`core`](core/) | Foundation skills for the Connect MCP server. `connect-mcp-setup`: configure any MCP client against the single Connect endpoint, mint a token with the right permissions, diagnose 401/403/empty-catalog problems. `connect-navigator`: locate the right tool family — concept→domain map, VerboseID prefixes, list-tool conventions. |
| [`fulfillments`](fulfillments/) | Vendor-side triage of inbound fulfillment requests (which lifecycle transition, and why) and distributor/reseller-side subscription operations (inspect, then change / cancel / suspend / resume / renew / adjust / transfer). Skills: `connect-request-triage`, `connect-subscription-ops`. |
| [`helpdesk`](helpdesk/) | Triage helpdesk cases: read the case and its attachments, pick the correct transition (inquire, pend, resolve, close), draft the partner-facing reply. Drafting is autonomous; sending waits for confirmation. Skill: `connect-helpdesk-triage`. |
| [`listings`](listings/) | Drive the listing request state machine (submit, deploy, complete, refine, cancel, assign, unassign), pick the target marketplace, and diagnose a stuck listing by naming which side has to act next. Skill: `connect-listing-manager`. |
| [`pricing`](pricing/) | Drive the price list lifecycle: find a list, open a draft version, update price points, activate or schedule it, plus bulk import of a vendor rate card (XLSX/CSV) into per-point updates. Skill: `connect-pricelist-manager`. |
| [`products`](products/) | Build a product end to end through the products tools — shell, items, the ordering / fulfillment / configuration parameter phases, templates, version publication — and orchestrate a full launch across products, pricing, marketplaces and listings. Skills: `connect-product-builder`, `connect-product-launch`. |
| [`usage`](usage/) | Convert vendor billing reports (AWS CUR, Microsoft NCE incl. Azure consumption, Adobe VIP) into CloudBlue Connect Usage Files and submit them through the Connect MCP server. Bundles the `connect-usage-converter` skill. |

More skills land here as the Connect MCP ecosystem grows.

## Install

### Claude Code (recommended)

Register the marketplace, then install the skill you want:

```
/plugin marketplace add cloudblue/agent-skills
/plugin install usage@cloudblue-agent-skills
```

Updates flow through `/plugin update`. To see what's available before
installing, run `/plugin marketplace browse cloudblue-agent-skills`.

### Codex

Register the marketplace, then add the plugin:

```bash
codex plugin marketplace add cloudblue/agent-skills --ref master
codex plugin add usage@cloudblue-agent-skills
```

Type `$connect-usage-converter` to invoke the skill explicitly; Codex can
also invoke it implicitly when a task matches. Verify with
`codex plugin list`.

### Other agents

Cursor, Gemini CLI, Antigravity, GitHub Copilot, Zed, Pi, Hermes,
OpenCode, Amp, and any other Agent Skills harness are covered in
[INSTALL.md](./INSTALL.md). The quick cross-platform route is the
community [`skills`][skills-cli] CLI:

```bash
npx skills add cloudblue/agent-skills
```

### Development install (symlink)

For local iteration on the skills themselves:

```bash
git clone https://github.com/cloudblue/agent-skills ~/code/agent-skills
ln -s ~/code/agent-skills/usage/skills/connect-usage-converter \
      ~/.claude/skills/connect-usage-converter
```

## Configuration prerequisites

Every plugin in this repo reaches Connect through one MCP endpoint. The
[`core`](core/) plugin's `connect-mcp-setup` skill owns that setup for all
of them — the endpoint, minting a token with the right permissions, the
client config, and the 401/403/empty-catalog diagnosis. Install it first:

```
/plugin install core@cloudblue-agent-skills
```

The bare minimum is a `~/.mcp.json` (Claude Code) or equivalent entry
pointing at the MCP endpoint with an `ApiKey` header.

## Repository layout

```
agent-skills/
├── .claude-plugin/
│   └── marketplace.json                       ← Claude Code marketplace catalog (no version)
├── .agents/plugins/
│   └── marketplace.json                       ← Codex marketplace catalog
├── gemini-extension.json                      ← Gemini CLI extension manifest
├── GEMINI.md                                  ← Gemini context file (imports the skill)
├── INSTALL.md                                 ← per-harness install instructions
├── <plugin-name>/                             ← one folder per plugin
│   ├── .claude-plugin/
│   │   └── plugin.json                        ← plugin metadata + version
│   └── skills/
│       └── <skill-name>/                      ← skill folder
│           ├── SKILL.md                       ← entry point
│           └── …                              ← supporting files
└── README.md
```

Per-plugin `plugin.json#version` means plugins update independently.
The marketplace catalog doesn't carry a version of its own — it's just a
phone book pointing at each plugin's own metadata. This matches the
Claude Code plugin spec and the structure used by
[`hashicorp/agent-skills`][hashicorp-skills].

## Contributing

Plugins should follow the [Claude Code plugin convention][plugin-spec].
Open a PR adding:

1. A new top-level folder `<plugin-name>/` with a
   `.claude-plugin/plugin.json` (must include `name`, `version`,
   `description`).
2. One or more skills under `<plugin-name>/skills/<skill-name>/`, each
   with a `SKILL.md` (`name` / `description` frontmatter + body).
3. An entry in `.claude-plugin/marketplace.json#plugins[]` pointing at
   the plugin folder (`"source": "./<plugin-name>"`).
4. A row in the **Plugins in this repo** table above.

[plugin-spec]: https://github.com/anthropics/skills
[hashicorp-skills]: https://github.com/hashicorp/agent-skills
[skills-cli]: https://www.skills.sh/
