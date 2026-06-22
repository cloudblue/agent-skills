# agent-skills

A curated collection of Claude Code **plugins** for interacting with
CloudBlue Connect MCP servers. Each plugin is a self-contained folder at
the repo root, carrying its own `.claude-plugin/plugin.json` and one or
more skills under `skills/`. The repo-level
`.claude-plugin/marketplace.json` is the catalog Claude Code reads when
you register the marketplace.

## Plugins in this repo

| Plugin | Purpose |
|---|---|
| [`usage`](usage/) | Convert vendor billing reports (AWS CUR, Microsoft NCE incl. Azure consumption, Adobe VIP) into CloudBlue Connect Usage Files and submit them through the Usage MCP server. Bundles the `connect-usage-converter` skill. |

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

### Cross-platform (Claude Code, Cursor, Cline, Copilot, …)

The community [`skills`][skills-cli] CLI installs into whichever AI agent
you have configured:

```bash
npx skills add cloudblue/agent-skills
```

This pulls all skills in this repo. To install a specific one:

```bash
npx skills add cloudblue/agent-skills --plugin usage
```

### Development install (symlink)

For local iteration on the skills themselves:

```bash
git clone https://github.com/cloudblue/agent-skills ~/code/agent-skills
ln -s ~/code/agent-skills/usage/skills/connect-usage-converter \
      ~/.claude/skills/connect-usage-converter
```

## Configuration prerequisites

Every plugin in this repo talks to a Connect MCP endpoint. Before a
plugin can do anything useful, your agent's MCP client needs to know how
to reach Connect and how to authenticate. See each plugin's skill
`setup.md` for details (worked example lives in
[`usage/skills/connect-usage-converter/setup.md`](usage/skills/connect-usage-converter/setup.md)).

The bare minimum is a `~/.mcp.json` (Claude Code) or equivalent entry
pointing at the MCP endpoint with an `ApiKey` header.

## Repository layout

```
agent-skills/
├── .claude-plugin/
│   └── marketplace.json                       ← marketplace catalog (no version)
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
[skills-cli]: https://github.com/skills-org/skills
