# Install

The plugin in this repo (`usage`, bundling the `connect-usage-converter`
skill) works in any agent that reads Claude Code plugins or the open
Agent Skills format. Pick your harness below.

Whatever the harness, the skill needs an MCP client configured to reach
your Connect tenant — see
[`usage/skills/connect-usage-converter/setup.md`](usage/skills/connect-usage-converter/setup.md).

<details>
<summary><strong>Claude Code</strong></summary>

### Install

```bash
claude plugin marketplace add cloudblue/agent-skills
claude plugin install usage@cloudblue-agent-skills
```

The skill activates automatically on matching requests ("convert this
NCE CSV", "upload our AWS bill to Connect").

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
claude plugin uninstall usage
claude plugin marketplace remove cloudblue-agent-skills
```

</details>

<details>
<summary><strong>Codex</strong></summary>

### Install

```bash
codex plugin marketplace add cloudblue/agent-skills --ref master
codex plugin add usage@cloudblue-agent-skills
```

Type `$connect-usage-converter` to invoke explicitly; Codex can also
invoke it implicitly on matching tasks.

### Verify

```bash
codex plugin list
```

### Update

```bash
codex plugin marketplace upgrade cloudblue-agent-skills
codex plugin remove usage
codex plugin add usage@cloudblue-agent-skills
```

### Uninstall

```bash
codex plugin remove usage
codex plugin marketplace remove cloudblue-agent-skills
```

</details>

<details>
<summary><strong>Cursor</strong></summary>

Install with the community [`skills`](https://www.skills.sh/) CLI:

```bash
npx skills add cloudblue/agent-skills -a cursor        # this workspace
npx skills add cloudblue/agent-skills -a cursor -g     # all projects
```

New agent chat, type `/connect-usage-converter`.

### Verify / Update / Uninstall

```bash
npx skills list
npx skills update connect-usage-converter
npx skills remove connect-usage-converter
```

</details>

<details>
<summary><strong>Gemini CLI</strong></summary>

### Install (extension)

```bash
gemini extensions install https://github.com/cloudblue/agent-skills
```

The extension loads `GEMINI.md`, which imports the full skill. `git`
must be installed. (There is no standalone custom-command route: the
skill spans multiple files — mappings, scripts, examples — so it can't
be inlined into a single `.toml`.)

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

Point `agy` at the plugin folder, not the repo root — it expects
`skills/` at the plugin root:

```bash
agy plugin install https://github.com/cloudblue/agent-skills/tree/master/usage
```

### Verify

```bash
agy plugin list
```

### Update

```bash
agy plugin uninstall usage
agy plugin install https://github.com/cloudblue/agent-skills/tree/master/usage
```

### Uninstall

```bash
agy plugin uninstall usage
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

Without the CLI, copy the skill folder into any directory Copilot scans
(`~/.copilot/skills/`, `~/.claude/skills/`, or `~/.agents/skills/`):

```bash
git clone https://github.com/cloudblue/agent-skills
mkdir -p ~/.copilot/skills
cp -R agent-skills/usage/skills/connect-usage-converter ~/.copilot/skills/
```

### Verify / Update / Uninstall

Type `/` in the chat input and confirm `connect-usage-converter`
appears. Or `npx skills list` / `update` / `remove` as above.

</details>

<details>
<summary><strong>Zed</strong></summary>

Zed's Agent reads Agent Skills natively. This skill spans multiple
files (mappings, scripts, examples), so install by copying the folder —
the Skills manager's "Create skill from URL" only imports a single
`SKILL.md` and would miss the supporting files.

### Install

```bash
git clone https://github.com/cloudblue/agent-skills
cp -R agent-skills/usage/skills/connect-usage-converter ~/.config/zed/skills/
```

Then type `/connect-usage-converter` in the Agent Panel.

### Verify

Open the Skills manager in the Agent Panel and confirm
`connect-usage-converter` is listed.

### Update / Uninstall

Re-copy the folder after `git pull`, or delete
`~/.config/zed/skills/connect-usage-converter`.

</details>

<details>
<summary><strong>Pi</strong></summary>

Pi implements the Agent Skills standard; skills are invoked as
`/skill:<name>`.

### Install

```bash
npx skills add cloudblue/agent-skills -a pi -y
```

Or copy the folder into a directory Pi scans (`~/.pi/agent/skills/`,
`~/.agents/skills/`, project `.pi/skills/` or `.agents/skills/`):

```bash
git clone https://github.com/cloudblue/agent-skills
mkdir -p ~/.pi/agent/skills
cp -R agent-skills/usage/skills/connect-usage-converter ~/.pi/agent/skills/
```

Enable skill slash commands in Pi's `settings.json`:

```json
{ "enableSkillCommands": true }
```

Start a new session and type `/skill:connect-usage-converter`.

### Verify / Update / Uninstall

```bash
npx skills list
npx skills update connect-usage-converter
npx skills remove connect-usage-converter
```

</details>

<details>
<summary><strong>Hermes</strong></summary>

### Install

Copy the skill folder into Hermes' skills directory:

```bash
git clone https://github.com/cloudblue/agent-skills
mkdir -p ~/.hermes/skills
cp -R agent-skills/usage/skills/connect-usage-converter ~/.hermes/skills/
```

Type `/connect-usage-converter`.

The registry route
(`hermes skills install cloudblue/agent-skills/usage/skills/connect-usage-converter`)
works once skills.sh indexes this repo; until then it errors with
"could not fetch". Taps don't apply here — `hermes skills tap` only
scans a top-level `skills/` directory, and this repo nests skills under
`usage/skills/`.

### Verify / Update / Uninstall

```bash
hermes skills list
```

Update by re-copying the folder after `git pull`; remove with
`hermes skills uninstall connect-usage-converter` or by deleting the
folder.

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

Without the CLI, copy the skill folder into whatever path your agent
scans (`.agents/skills/` for OpenCode):

```bash
git clone https://github.com/cloudblue/agent-skills
cp -R agent-skills/usage/skills/connect-usage-converter ~/.agents/skills/
```

### Verify / Update / Uninstall

```bash
npx skills list
npx skills update connect-usage-converter
npx skills remove connect-usage-converter
```

</details>

## Troubleshooting

**Skill not in autocomplete.** Restart the agent — skill/plugin indexes
are read at session start.

**`claude plugin marketplace add` fails.** Use the `owner/repo` form. A
local path must point at the repo root, not `.claude-plugin/`.

**Skill missing after `npx skills add`.** Start a new agent chat and
confirm the folder landed where your agent scans, with the frontmatter
`name` matching the folder name (`connect-usage-converter`).

**MCP errors on first use.** The skill converses with the Usage MCP
server on your Connect tenant; configure the endpoint and `ApiKey`
first — see
[`setup.md`](usage/skills/connect-usage-converter/setup.md).
