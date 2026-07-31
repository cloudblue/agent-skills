#!/usr/bin/env python3
"""G1 checks skillsaw has no rule for.

Run from the repo root: python3 scripts/lint_skills.py
skillsaw (see .skillsaw.yaml) does the rest of G1.
"""

import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
# The description is what the harness matches on: it must carry at least one
# trigger signal or the skill is unreachable.
TRIGGER = re.compile(r"use when|use in|use it|use this|trigger", re.IGNORECASE)
# skillsaw's content-banned-references only scans SKILL.md, but the defect this
# ban exists for — a stale per-module MCP path — shipped in a sibling setup.md.
MODULE_PATH = re.compile(r"public/v1/mcp/[A-Za-z]")
# One convention for eval fixtures: the key names a file that exists, or it is
# absent (a comment records the state the G3 mock will have to serve). A
# dangling path is the failure this catches.
FIXTURES = re.compile(r"^fixtures:\s*(\S+)\s*$", re.MULTILINE)
# An eval's `name` is its filename: the G3 runner reports by one and humans
# grep by the other, and 3 of 21 had already drifted apart.
EVAL_NAME = re.compile(r"^name:\s*(\S+)\s*$", re.MULTILINE)


def frontmatter(text: str) -> dict:
    m = re.match(r"---\n(.*?)\n---\n", text, re.DOTALL)
    if not m:
        return {}
    fields = {}
    folding = None
    for line in m.group(1).splitlines():
        km = re.match(r"^([a-z_]+):\s*(.*)$", line)
        if km:
            key, value = km.group(1), km.group(2).strip()
            # `description: >-` folds the value onto the following indented
            # lines; keeping the marker as the value would make the trigger
            # check fail with a wrong diagnosis.
            folding = key if value in (">", ">-", ">+", "|", "|-", "|+") else None
            fields[key] = "" if folding else value
        elif folding and line.startswith((" ", "\t")):
            fields[folding] = (fields[folding] + " " + line.strip()).strip()
    return fields


def self_test() -> int:
    folded = (
        "---\nname: connect-thing\ndescription: >-\n  Use when the user asks\n"
        "  for a thing.\nversion: 1.0.0\nlicense: MIT\nallowed-tools:\n  - Read\n---\nbody\n"
    )
    fm = frontmatter(folded)
    assert fm["name"] == "connect-thing", fm
    assert fm["description"] == "Use when the user asks for a thing.", fm
    assert TRIGGER.search(fm["description"]), fm
    assert frontmatter("---\nname: a\ndescription: Use when x\n---\n") == {
        "name": "a",
        "description": "Use when x",
    }
    assert MODULE_PATH.search("https://x/public/v1/mcp/usage/")
    assert not MODULE_PATH.search("`/public/v1/mcp/<module>/` is stale")
    print("lint_skills self-test: ok")
    return 0


def main() -> int:
    if "--self-test" in sys.argv:
        return self_test()
    errors = []
    skill_files = sorted(
        p for p in REPO.glob("*/skills/*/SKILL.md") if not p.relative_to(REPO).parts[0].startswith(".")
    )
    if not skill_files:
        errors.append("no */skills/*/SKILL.md files found — wrong cwd?")
    for path in skill_files:
        rel = path.relative_to(REPO)
        fm = frontmatter(path.read_text(encoding="utf-8"))
        desc = fm.get("description", "")
        for field in ("name", "description", "version", "license"):
            if not fm.get(field):
                errors.append(f"{rel}: frontmatter missing `{field}`")
        if fm.get("name") and fm["name"] != path.parent.name:
            errors.append(f"{rel}: name `{fm['name']}` != directory `{path.parent.name}`")
        if desc and not TRIGGER.search(desc):
            errors.append(f"{rel}: description has no trigger phrase (no 'Use when…'/'Triggers on…')")

    docs = sorted(
        p for p in REPO.glob("*/skills/**/*.md") if not p.relative_to(REPO).parts[0].startswith(".")
    )
    for path in docs:
        for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
            if MODULE_PATH.search(line):
                errors.append(
                    f"{path.relative_to(REPO)}:{line_no}: per-module MCP path — the single "
                    f"endpoint is /public/v1/mcp (use `<module>` when writing about the "
                    f"stale form)"
                )

    # Contributing rule #4: the front page documents every registered plugin.
    marketplace = json.loads(
        (REPO / ".claude-plugin" / "marketplace.json").read_text(encoding="utf-8")
    )
    readme = (REPO / "README.md").read_text(encoding="utf-8")
    for plugin in marketplace["plugins"]:
        if f"[`{plugin['name']}`]" not in readme:
            errors.append(
                f"README.md: no row for the `{plugin['name']}` plugin "
                f"(see Contributing rule #4)"
            )

    evals = sorted(REPO.glob("*/skills/*/evals/*.yaml"))
    for path in evals:
        text = path.read_text(encoding="utf-8")
        name = EVAL_NAME.search(text)
        if not name:
            errors.append(f"{path.relative_to(REPO)}: eval has no `name`")
        elif name.group(1) != path.stem:
            errors.append(
                f"{path.relative_to(REPO)}: name `{name.group(1)}` != filename "
                f"`{path.stem}`"
            )
        for ref in FIXTURES.findall(text):
            if not (path.parent / ref).exists():
                errors.append(
                    f"{path.relative_to(REPO)}: `fixtures: {ref}` does not exist — name a "
                    f"real file or drop the key until the G3 mock defines the format"
                )

    for e in errors:
        print(f"ERROR {e}")
    print(
        f"lint_skills: {len(skill_files)} skills, {len(docs)} markdown files and "
        f"{len(evals)} evals checked, {len(errors)} errors"
    )
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
