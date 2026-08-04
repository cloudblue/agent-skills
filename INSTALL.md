# Install

This repo ships several plugins, each bundling one or more skills — the
[README's plugin table](README.md) is the catalog. The instructions
below use `<plugin>` and `<skill>` placeholders; substitute any row from
that table (the examples use the `core` plugin and its
`connect-mcp-setup` skill). Everything works in any agent that reads
Claude Code plugins or the open Agent Skills format. Pick your harness
below.

Whatever the harness, the skills need an MCP client configured to reach
your Connect tenant — that setup (endpoint, token, permissions) is
itself owned by a skill:
[`core/skills/connect-mcp-setup`](core/skills/connect-mcp-setup/SKILL.md).

<details>
<summary><strong>Claude Code</strong></summary>

### Install

```bash
claude plugin marketplace add cloudblue/agent-skills
claude plugin install <plugin>@cloudblue-agent-skills   # e.g. core, usage
```

Skills activate automatically on matching requests ("convert this NCE
CSV", "why does my token see an empty catalog").

### Verify

```bash
claude plugin list
```

### Update

```bash
claude plugin marketplace update cloudblue-agent-skills
```

### Uninstall

```bash
claude plugin uninstall <plugin>
claude plugin marketplace remove cloudblue-agent-skills
```

</details>

<details>
<summary><strong>Codex</strong></summary>

### Install

```bash
codex plugin marketplace add cloudblue/agent-skills --ref master
codex plugin add <plugin>@cloudblue-agent-skills
```

Type `$<skill>` (e.g. `$connect-mcp-setup`) to invoke explicitly; Codex
can also invoke skills implicitly on matching tasks.

### Verify

```bash
codex plugin list
```

### Update

```bash
codex plugin marketplace upgrade cloudblue-agent-skills
codex plugin remove <plugin>
codex plugin add <plugin>@cloudblue-agent-skills
```

### Uninstall

```bash
codex plugin remove <plugin>
codex plugin marketplace remove cloudblue-agent-skills
```

</details>

<details>
<summary><strong>Cursor</strong></summary>

Install with the community [`skills`](https://www.skills.sh/) CLI (it
picks up every skill in the repo):

```bash
npx skills add cloudblue/agent-skills -a cursor        # this workspace
npx skills add cloudblue/agent-skills -a cursor -g     # all projects
```

New agent chat, type `/<skill>` (e.g. `/connect-mcp-setup`).

### Verify / Update / Uninstall

```bash
npx skills list
npx skills update <skill>
npx skills remove <skill>
```

</details>

<details>
<summary><strong>Gemini CLI</strong></summary>

### Install (extension)

```bash
gemini extensions install https://github.com/cloudblue/agent-skills
```

The extension loads `GEMINI.md`, which routes each request to the right
plugin's skill via the README catalog and `connect-navigator`. `git`
must be installed. (There is no standalone custom-command route: the
skills span multiple files — workflows, mappings, scripts — so they
can't be inlined into a single `.toml`.)

### Verify

```bash
gemini extensions list
```

### Update

```bash
gemini extensions update cloudblue-agent-skills
```

### Uninstall

```bash
gemini extensions uninstall cloudblue-agent-skills
```

</details>

<details>
<summary><strong>Antigravity (<code>agy</code>)</strong></summary>

The `agy` CLI installs separately from the desktop app
(`brew install --cask antigravity-cli`, or the
[official installer](https://antigravity.google/docs/cli/install)).

### Install

Point `agy` at a plugin folder, not the repo root — it expects
`skills/` at the plugin root:

```bash
agy plugin install https://github.com/cloudblue/agent-skills/tree/master/<plugin>
```

### Verify

```bash
agy plugin list
```

### Update

```bash
agy plugin uninstall <plugin>
agy plugin install https://github.com/cloudblue/agent-skills/tree/master/<plugin>
```

### Uninstall

```bash
agy plugin uninstall <plugin>
```

</details>

<details>
<summary><strong>GitHub Copilot (VS Code and Copilot CLI)</strong></summary>

Copilot reads Agent Skills natively: the same `SKILL.md`, no conversion.

### Install

```bash
npx skills add cloudblue/agent-skills -a github-copilot        # this project
npx skills add cloudblue/agent-skills -a github-copilot -g     # all projects
```

Without the CLI, copy skill folders into any directory Copilot scans
(`~/.copilot/skills/`, `~/.claude/skills/`, or `~/.agents/skills/`):

```bash
git clone https://github.com/cloudblue/agent-skills
mkdir -p ~/.copilot/skills
cp -R agent-skills/<plugin>/skills/<skill> ~/.copilot/skills/
```

### Verify / Update / Uninstall

Type `/` in the chat input and confirm the skill appears. Or
`npx skills list` / `update` / `remove` as above.

</details>

<details>
<summary><strong>Zed</strong></summary>

Zed's Agent reads Agent Skills natively. The skills span multiple files
(workflows, mappings, scripts), so install by copying folders — the
Skills manager's "Create skill from URL" only imports a single
`SKILL.md` and would miss the supporting files.

### Install

```bash
git clone https://github.com/cloudblue/agent-skills
cp -R agent-skills/<plugin>/skills/<skill> ~/.config/zed/skills/
```

Then type `/<skill>` in the Agent Panel.

### Verify

Open the Skills manager in the Agent Panel and confirm the skill is
listed.

### Update / Uninstall

Re-copy the folder after `git pull`, or delete
`~/.config/zed/skills/<skill>`.

</details>

<details>
<summary><strong>Pi</strong></summary>

Pi implements the Agent Skills standard; skills are invoked as
`/skill:<name>`.

### Install

```bash
npx skills add cloudblue/agent-skills -a pi -y
```

Or copy skill folders into a directory Pi scans (`~/.pi/agent/skills/`,
`~/.agents/skills/`, project `.pi/skills/` or `.agents/skills/`):

```bash
git clone https://github.com/cloudblue/agent-skills
mkdir -p ~/.pi/agent/skills
cp -R agent-skills/<plugin>/skills/<skill> ~/.pi/agent/skills/
```

Enable skill slash commands in Pi's `settings.json`:

```json
{ "enableSkillCommands": true }
```

Start a new session and type `/skill:<skill>`.

### Verify / Update / Uninstall

```bash
npx skills list
npx skills update <skill>
npx skills remove <skill>
```

</details>

<details>
<summary><strong>Hermes</strong></summary>

### Install

Copy skill folders into Hermes' skills directory:

```bash
git clone https://github.com/cloudblue/agent-skills
mkdir -p ~/.hermes/skills
cp -R agent-skills/<plugin>/skills/<skill> ~/.hermes/skills/
```

Type `/<skill>`.

The registry route
(`hermes skills install cloudblue/agent-skills/<plugin>/skills/<skill>`)
works once skills.sh indexes this repo; until then it errors with
"could not fetch". Taps don't apply here — `hermes skills tap` only
scans a top-level `skills/` directory, and this repo nests skills under
`<plugin>/skills/`.

### Verify / Update / Uninstall

```bash
hermes skills list
```

Update by re-copying the folder after `git pull`; remove with
`hermes skills uninstall <skill>` or by deleting the folder.

</details>

<details>
<summary><strong>OpenCode, Amp, and any other agent-skills harness</strong></summary>

Works with any harness that reads Agent Skills. Swap `-a <agent>` for
yours.

### Install

```bash
npx skills add cloudblue/agent-skills                  # this workspace
npx skills add cloudblue/agent-skills -g               # all projects
npx skills add cloudblue/agent-skills -a opencode -y   # one agent only
```

Without the CLI, copy skill folders into whatever path your agent scans
(`.agents/skills/` for OpenCode):

```bash
git clone https://github.com/cloudblue/agent-skills
cp -R agent-skills/<plugin>/skills/<skill> ~/.agents/skills/
```

### Verify / Update / Uninstall

```bash
npx skills list
npx skills update <skill>
npx skills remove <skill>
```

</details>

## Troubleshooting

**Skill not in autocomplete.** Restart the agent — skill/plugin indexes
are read at session start.

**`claude plugin marketplace add` fails.** Use the `owner/repo` form. A
local path must point at the repo root, not `.claude-plugin/`.

**Skill missing after `npx skills add`.** Start a new agent chat and
confirm the folder landed where your agent scans, with the frontmatter
`name` matching the folder name.

**MCP errors on first use.** The skills converse with the Connect MCP
server on your tenant; configure the endpoint and `ApiKey` first —
[`connect-mcp-setup`](core/skills/connect-mcp-setup/SKILL.md) owns that
setup and its diagnosis.
