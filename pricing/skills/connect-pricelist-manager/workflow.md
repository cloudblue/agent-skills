# Workflow: Price List Version → Live Prices

The detailed playbook behind [`SKILL.md`](SKILL.md). Each step names the tool *family* that does the work and the state you must be in before it succeeds. Exact tool names and parameters come from the catalog — read the pricing tool descriptions once before you start.

Pre-requisite: the MCP client is configured and the token carries **MCP + Pricing** (the `connect-mcp-setup` skill in the `core` plugin).

## Step 0 — Gather inputs

| Input | Source | Notes |
|---|---|---|
| Price list id (`PL-…`) | User, or found in step 1 | If the user names a marketplace and product instead, find the list. |
| Intent | User | One of: set specific prices, apply a uniform change, import a rate card. These take different paths (steps 4a/4b/4c). |
| Rate card file | User attaches or names a path | XLSX or CSV. Only for the import path. |
| Effective date | User | Needed only if the version is to be *scheduled* rather than activated now. |
| Currency of the source prices | Read from the file / asked | Must equal the price list's currency. Connect does not convert. |

Ask for anything missing **before** the first tool call. In particular do not guess an effective date: "next month" is not a date.

## Step 1 — Find and read the price list

Use the pricing price-list *list* tool with flat filters (`marketplace_id`, `product_id`, `status`, plus `limit`/`offset`) when you only have a marketplace and product. List responses are minimal — id and name — so follow up with:

```
pricing_get_price_list(price_list_id="PL-1234")
```

From the full record, note three things and repeat them back to the user:

- the **marketplace** the list serves,
- the **currency**,
- which version is currently **active**.

If the currency does not match the source prices, stop and ask. Converting is a commercial decision, not a rounding step (see the skill's non-goals).

## Step 2 — Establish the editable version

```
pricing_list_versions(price_list_id="PL-1234")
```

Read the states. What you do next depends on what you find:

| Found | Do |
|---|---|
| A **draft** version | Reuse it. Warn the user it already contains someone's pending changes and summarize them before adding more. |
| A **scheduled** version (effective in the future) | Do not edit it silently — a scheduled version is a promise already made. Ask whether to amend it or supersede it with a new one. |
| Only **active** / superseded versions | Create a new version. It starts as a copy of the active prices. |

Creating the version is a **mutation** — it creates an object — but a safe one: a draft is invisible to partners and charges nobody. Use the version side of the pricing `manage`/create family; per Connect convention, omitting an existing id means "create".

> **Never attempt to update points on an active version.** It is the single most common failure in this domain. If an update is refused, check the version state before you check anything else.

## Step 3 — Read one price point

Before writing anything, list the points in the draft and fetch **one** in full. That single record tells you:

- what the price attributes are actually called (cost vs. sale price vs. MSRP, and whether tiered fields exist),
- how the item is identified (item id, MPN, unit, billing period),
- how precision is expressed.

Everything you write in step 5 uses those names. Do not carry attribute names over from a previous session, another tenant, or this document — they are product- and tenant-shaped.

Dump the point list to a local JSON file if you plan to use the helper script in step 4c; it needs the points to match against.

## Step 4 — Prepare the changes

Three paths. Pick one; they are not combinable in a single pass.

### 4a — Specific prices named by the user

Resolve each named item to a point id from step 3. Build the list of (point, attribute, old value, new value) tuples. Anything the user named that does not resolve is reported, not guessed at.

### 4b — A uniform change ("+5% on everything")

Do **not** loop. The pricing domain has an adjustment family for exactly this: one call expressing a percentage or absolute change over the version. Read those tool descriptions and use them. Looping 400 point updates to express one policy is both slower and harder for the user to audit.

Compute and show the resulting range (min/max new price) before applying — percentage changes on an unfamiliar list are where fat-finger errors hide.

An adjustment is **relative**, so unlike a per-point update it is not idempotent: retrying a timed-out `+4%` blindly applies `+8.16%`. If the call fails ambiguously (timeout, no response body), re-read a few draft points and compare against the values from step 3 to see whether it landed before you retry.

### 4c — Import from a vendor rate card

1. Identify the shape: one row per SKU ([`mappings/flat-rate-card.md`](mappings/flat-rate-card.md)) or several rows per SKU with volume/tier breaks ([`mappings/tiered-rate-card.md`](mappings/tiered-rate-card.md)).
2. Write the column mapping: which column is the vendor SKU (matched to the Connect item **MPN**), which columns are prices, and which point attribute each price column targets. The attribute names come from step 3.
3. Run the helper:

```bash
python scripts/build_price_point_updates.py \
    --rate-card rate-card.csv \
    --mapping mapping.json \
    --points points.json \
    --output updates.json \
    --report report.txt
```

`mapping.json` describes the columns, `points.json` is the dump from step 3, `updates.json` is the per-point change list (old value, new value, percentage), and the report names what did not match and what did not change. The script's docstring documents the mapping file shape; a runnable example of all three files lives in [`examples/inputs/`](examples/inputs/) — [`vendor-rate-card.csv`](examples/inputs/vendor-rate-card.csv), [`column-mapping.json`](examples/inputs/column-mapping.json), [`price-points-dump.json`](examples/inputs/price-points-dump.json) — and the output it produces is [`examples/outputs/price-point-updates-sample.json`](examples/outputs/price-point-updates-sample.json). Point ids in those samples are deliberately written as `SYNTHETIC-POINT-ID-n`: treat a real point id as an opaque string from the catalog, never a pattern to construct.

4. Read the report before applying anything:

- **Unmatched SKUs** — the vendor sells something this price list has no item for. Report them to the user; creating the item is `connect-product-builder`'s job (`catalog` plugin), not yours.
- **Unchanged rows** — dropped from the output. A rate card is usually mostly unchanged; this is what keeps the call count sane.
- **Suspicious deltas** — order-of-magnitude jumps, sign flips, zeros. Surface each one; do not apply them silently.

## Step 5 — Apply to the draft

*Mutation: changes the draft's prices. Not gated — nothing is effective yet — but every change is reported.*

For per-point work:

```
pricing_update_price_point(<point identity>, <attribute>=<new value>)
```

One call per point. Before starting a loop, count the calls and act on the count:

| Points to update | Action |
|---|---|
| ≤ 50 | Loop. Report progress and a final tally. |
| 50–200 | Tell the user the call count first and get a go-ahead. |
| > 200 | **Stop.** Do not start the loop. |

Over ~200, offer instead: narrow to the SKUs that actually changed (step 4c already computed this), express the change as one adjustment if it is uniform, or use the Connect UI's bulk price import, which exists for exactly this. A server-side bulk tool has been requested — if one appears in the catalog, prefer it over any of the above.

If a call fails mid-loop, stop and report where you stopped. The draft is now partially updated; that is recoverable (it is not live) but the user must know which points landed.

## Step 6 — Summarize the diff

Before the gate, give the human one compact summary:

```
PL-1234 (marketplace MP-1234, USD) — draft version 4
  points updated:      37 of 412
  largest increase:    ACME-PRO-M  12.00 → 13.80  (+15.0%)
  largest decrease:    ACME-LITE-M  6.00 → 5.70   (-5.0%)
  unmatched SKUs:      2  (ACME-NEW-M, ACME-BETA-Y)  -> no item in this list
  unchanged, skipped:  375
```

This is what the user is actually confirming in step 7. A gate without a diff is a rubber stamp.

## Step 7 — Go live (gated)

**Both actions below change what partners are charged. Neither runs without explicit human confirmation in the current turn.**

### Activate now

```
pricing_activate_version(<version identity>)
```

The version becomes effective immediately and supersedes the previous active one. There is no un-publish: a mistake is corrected by rolling forward another version, which is why the confirmation is not optional.

### Schedule for a date

Use the scheduling counterpart in the same family, with the effective date the user named. Confirm the date back to them in full (`2026-09-01`, not "next month") before calling. A scheduled version stays editable-by- supersession until it takes effect.

### Cancel or delete a version (destructive, gated)

Only when the user asks for it by name. Cancelling a scheduled version withdraws a price change that was already promised downstream; deleting a draft throws away work that may not be yours. Never do either as cleanup after a failure — leave the draft and report it.

## Diagnosing a stuck price list

| Symptom | Likely cause | Next step |
|---|---|---|
| Point update refused / no effect | You are writing to an **active** version | List versions; find or create the draft (step 2) |
| `403` on every pricing tool | Token lacks the **Pricing** module permission (or MCP) | `connect-mcp-setup` skill, `core` plugin |
| `403` on one action only | The token's account is on the wrong side — price lists are owned by one party | Use a token from the owning account |
| Rate-card SKU matches no point | The item is not in this price list / agreement | Catalog gap — `connect-product-builder`, not a pricing fix |
| New prices live but partners see the old ones | A *scheduled* version was activated, or the change landed in a different draft | Re-read the versions and identify which one is active |
| Prices look off by ~100x | Currency minor units or a precision mismatch in the card | Re-check the point's precision from step 3 before rewriting |
| Uniform change took hundreds of calls | Used per-point updates where an adjustment belonged | Step 4b |
