#!/usr/bin/env python3
"""G2 — every tool name mentioned in a skill must exist in the live catalog.

The reference is tests/fixtures/catalog.json, dumped from one tools/list call
against a sandbox tenant:

    {"tools": [{"name": "pricing_get_price_list", ...}, ...]}

Valid prefixes are derived from the catalog itself; only identifiers under
those prefixes are checked, which keeps ordinary code identifiers in examples
from false-positiving.

Run from the repo root: python3 scripts/check_tool_names.py
"""

import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
FIXTURE = REPO / "tests" / "fixtures" / "catalog.json"
IDENT = re.compile(r"\b[a-z][a-z0-9]*(?:_[a-z0-9]+)+\b")
# Some tools are unprefixed (`get_usage_file`): their first segment is a verb,
# not a module namespace, and must not become a prefix — `get_` would flag
# every `get_*` identifier in every code example. Those are matched exactly.
VERBS = {
    "accept",
    "close",
    "create",
    "delete",
    "get",
    "list",
    "manage",
    "reconcile",
    "search",
    "submit",
    "update",
    "upload",
    "validate",
}


def unknown_in(text: str, catalog: set, prefixes: set) -> set:
    """Tool-shaped identifiers under a known namespace that aren't real tools.

    A bare domain word (`tier_accounts`, from `tier_accounts_*` tools) is a
    legitimate thing to write in prose, so an identifier that any catalog name
    extends is not a claim about a tool.
    """
    return {
        ident
        for ident in set(IDENT.findall(text))
        if ident not in catalog
        and any(ident.startswith(p) for p in prefixes)
        and not any(name.startswith(ident + "_") for name in catalog)
    }


def self_test() -> int:
    catalog = {
        "pricing_get_price_list",
        "tier_accounts_list",
        "tier_accounts_get_account",
        "get_usage_file",
    }
    prefixes = derive_prefixes(catalog)
    ok = "Call `pricing_get_price_list` for a `tier_accounts` scope, then get_usage_file."
    assert unknown_in(ok, catalog, prefixes) == set(), unknown_in(ok, catalog, prefixes)
    bad = "Call `pricing_bulk_update` to fix it."
    assert unknown_in(bad, catalog, prefixes) == {"pricing_bulk_update"}
    # An unprefixed tool's verb is not a namespace: `get_price` must not be flagged.
    assert unknown_in("get_price and some_local_var", catalog, prefixes) == set()
    print("check_tool_names self-test: ok")
    return 0


def derive_prefixes(catalog: set) -> set:
    return {seg + "_" for name in catalog if (seg := name.split("_")[0]) not in VERBS}


def main() -> int:
    if "--self-test" in sys.argv:
        return self_test()


    if not FIXTURE.exists():
        # An annotation, not just a log line: a green check that verified
        # nothing reads as coverage, and 15 evals defer their tool names here.
        print(
            "::warning::G2 skipped — no tests/fixtures/catalog.json, so tool names in "
            "skills and evals are UNVERIFIED"
        )
        print(
            "check_tool_names: SKIP — no catalog fixture.\n"
            f"Dump tools/list from a sandbox tenant to {FIXTURE.relative_to(REPO)} "
            "(needs a token carrying MCP plus every module permission)."
        )
        return 0

    data = json.loads(FIXTURE.read_text(encoding="utf-8"))
    catalog = {t["name"] for t in (data["tools"] if isinstance(data, dict) else data)}
    prefixes = derive_prefixes(catalog)

    unknown = {}
    for path in sorted(REPO.glob("*/skills/**/*")):
        if path.suffix not in {".md", ".yaml", ".yml"} or path.relative_to(REPO).parts[0].startswith("."):
            continue
        names = unknown_in(path.read_text(encoding="utf-8"), catalog, prefixes)
        if names:
            unknown[path.relative_to(REPO)] = names

    for rel, names in unknown.items():
        for name in sorted(names):
            print(f"ERROR {rel}: `{name}` is not in the tool catalog")
    print(f"check_tool_names: {len(catalog)} catalog tools, {sum(map(len, unknown.values()))} unknown names")
    return 1 if unknown else 0


if __name__ == "__main__":
    sys.exit(main())
