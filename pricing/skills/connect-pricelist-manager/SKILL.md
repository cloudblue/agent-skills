---
name: connect-pricelist-manager
description: Use when the user works on CloudBlue Connect price lists through the Connect MCP server — changing prices, opening a new price list version, importing a vendor rate card, or putting new prices live. Triggers on "raise our Microsoft prices by 5%", "import this vendor rate card into Connect", "activate the draft price list", "schedule the new prices for the first of next month", "why can't I edit this price list", "what changed between these two price list versions", or "cancel the scheduled price version".
version: 0.1.0
license: Apache-2.0
metadata:
  hermes:
    tags: [CloudBlue, Connect, Pricing, PriceList, MCP]
    category: productivity
    related_skills: [connect-navigator, connect-mcp-setup]
---

# Connect Price List Manager

You are driving the CloudBlue Connect **price list lifecycle** through the
pricing tools on the Connect MCP endpoint: locate the list, open a version
you are allowed to edit, set price points (by hand or from a vendor rate
card), then put the version live — immediately or on a future date.

Two things make this a skill rather than a tool description:

1. **Prices are never edited in place.** The object you can change is a
   *draft version*, not the price list and not the active version. Most
   "why does this fail" moments in pricing are an attempt to write to an
   active version.
2. **Going live is a mutation with consequences.** `activate` and
   `schedule` change what partners are charged. They are gated: you prepare
   everything, then a human confirms. See [Autonomy](#autonomy).

This work needs a token carrying the **Pricing** module permission. Any `403`
belongs to **`connect-mcp-setup`** (`core` plugin), which owns the permission
model and the client setup.

If the user only wants to *read* prices ("what do we charge for X?"), call
the pricing list/get tools directly — you do not need this skill.

## Tool families, not signatures

The `pricing` domain carries ~20 tools; this skill routes you to the family
and the *order*. Exact names and parameter schemas come from the catalog —
see `connect-navigator`, Shared conventions.

| What you need | Family | Notes |
|---|---|---|
| Find a price list | the pricing `*_list_*` tool for price lists | Flat filters (`marketplace_id`, `product_id`, `status`), `limit`/`offset`. Returns id + name only. |
| Full detail of one list | `pricing_get_price_list` | Gives the list's marketplace, currency, and which version is active. |
| Versions of a list | `pricing_list_versions` | The state machine lives here: processing / draft / scheduled / active / obsolete / expired. |
| Create or edit a list, or open a new version | the pricing `manage` / version-create family | Connect exposes one `manage` tool per resource: passing an existing id updates, omitting it creates. |
| Price points in a version | the pricing price-point list/get family | One point per item in scope. Read **one** point before writing many — its keys are the schema. |
| Change one point | `pricing_update_price_point` | Per point, per call. See [Batch size](#batch-size). |
| Uniform change across a version | the pricing adjustment family | A percentage/absolute change across many points is *one* adjustment, not N point updates. Prefer it. |
| Put a version live | `pricing_activate_version` and its scheduling counterpart | **Gated.** Confirm with the human first. |
| Undo a not-yet-effective version | the cancel / delete family for versions | **Gated and destructive.** Confirm first, never as cleanup on your own initiative. |

## The lifecycle in one pass

Detail, with worked call order and the failure modes, is in
[`workflow.md`](workflow.md).

1. **Identify the list.** `PL-…` from the user, or find it by marketplace +
   product. Read it and note its **currency** and its active version.
2. **Establish the editable version.** If a draft already exists, reuse it —
   do not open a second one. If none exists, create a new version (it starts
   from the current active prices). *Mutation: creates an object. Safe — a
   draft affects nobody until activated.* **Caveat:** `status: draft` alone
   does not identify the working copy — a version that was bypassed (a
   sibling created from it was activated directly) stays `draft` forever, so
   a list can carry several. The editable draft is the newest one whose
   `base` is the currently active version; check `base.id` and creation
   order, not just status.
3. **Read one price point** from that version to learn the attribute names
   (cost vs. sale price, per-tier fields, unit/period). Do not assume.
4. **Prepare the changes** — from the user's instruction, or by mapping a
   vendor rate card (see [Bulk import](#bulk-import-from-a-vendor-rate-card)).
   Resolve every row to an existing point *before* calling anything.
5. **Apply.** Per-point updates via `pricing_update_price_point`, or one
   adjustment if the change is uniform. *Mutation: changes draft prices.
   Not gated — the draft is not effective yet — but report what you changed.*
6. **Summarize the diff for the human**: list id, version, points changed,
   largest increase and decrease, currency, and anything that did not
   resolve.
7. **Go live — gated.** Ask for explicit confirmation, then either activate
   now or schedule for the effective date the user names. *Mutation:
   changes what partners pay.* Never bundle this into step 5.

## Bulk import from a vendor rate card

The vendor sends an XLSX/CSV rate card; Connect wants price points. The
mapping is per-vendor and the local quick references are in
[`mappings/`](mappings/):

- [`mappings/flat-rate-card.md`](mappings/flat-rate-card.md) — one row per
  SKU, one price. The common case.
- [`mappings/tiered-rate-card.md`](mappings/tiered-rate-card.md) — several
  rows per SKU (volume breaks, tier levels, cost *and* MSRP columns).

Both reduce to the same rule: **the vendor's SKU/part number is matched to
the Connect item's MPN**, and the price columns are matched to the point
attributes you read in step 3. Rows that do not match an existing point are
*not* an error to route around — they mean the item is not in this price
list (see [Non-goals](#non-goals)).

Use [`scripts/build_price_point_updates.py`](scripts/build_price_point_updates.py)
to do the matching deterministically: it takes the rate card, a column
mapping, and the price points you dumped in step 3, and emits the exact
per-point update payloads plus a report of unmatched rows. A sample of its
output is in
[`examples/outputs/price-point-updates-sample.json`](examples/outputs/price-point-updates-sample.json);
sample inputs are in [`examples/inputs/`](examples/inputs/).

### Batch size

`pricing_update_price_point` is per point, per call. A real rate card is
hundreds to thousands of SKUs, and a loop of that many MCP calls is the
wrong mechanism: it is slow, it is not atomic, and a failure halfway leaves
the draft partially updated (recoverable — the draft is not live — but
confusing).

Rules of thumb:

- **Under ~50 points:** loop, and report progress.
- **50–200:** loop, but tell the user how many calls it will take and get
  a go-ahead before starting.
- **Over ~200:** stop and say so. Offer the alternatives: narrow the scope
  to the SKUs that actually changed (usually a small fraction of the card),
  apply a single adjustment if the change is uniform, or upload the rate
  card through the Connect UI's bulk price import, which is built for this.
  A server-side bulk tool has been requested; when it appears in the
  catalog, use it and ignore this paragraph.

Diffing the card against the current points to update only what changed is
the single highest-value thing you can do here. The script reports it.

## Autonomy

The rungs are `connect-navigator`'s (free / announce / gated). Where pricing's
actions sit:

| Action | Rung |
|---|---|
| Find lists, read versions and points, diff a rate card | **free** |
| Create a draft version | **announce** — a draft is not effective and nobody outside sees it |
| Update price points in a draft, apply an adjustment | **announce** once the user has stated the intent; always report what changed |
| `activate` a version | **gated** |
| `schedule` a version | **gated** — confirm the version *and* the effective date |
| Cancel or delete a version, terminate a price list | **gated**, and destructive: only when the user asks for it by name |

Going live is **outward-facing** — it changes what partners are charged — so
what a pricing gate puts in front of the user is the diff summary from step 6
plus the effective date. "The user asked me to update prices" is not consent to
activate.

## Key principles

- **Never edit an active version.** If the tools refuse an update, check
  the version's state before checking anything else.
- **One draft at a time.** Two open drafts on one list is how the wrong
  prices go live. Reuse the existing draft.
- **Currency is the price list's, not the rate card's.** Connect does no FX
  conversion. If the card is in a different currency than the list, the
  conversion is the user's commercial decision — ask, do not compute a rate.
- **Read one point, then write many.** Attribute names (cost, sale price,
  tier fields) come from a real point in *this* version, never from memory.
- **Prices you did not resolve are the interesting output.** Report
  unmatched SKUs prominently; silently skipping them ships a half-priced
  list.
- **Activation is roll-forward only.** There is no un-publish. Correcting a
  bad activation means another version — which is exactly why the gate
  exists.

## Non-goals

- **Commercial policy.** What the price *should be* — margins, discount
  ladders, whether to pass a vendor increase through — is the user's
  decision. Compute what they ask for; flag anything that looks like a
  fat-finger (an order-of-magnitude jump, a negative price), then stop.
- **Product items.** Adding, renaming, or re-unitizing items, or changing
  item parameters, belongs to **`connect-product-builder`** (`catalog`
  plugin). A rate-card row with no matching price point is a catalog gap:
  report it, do not attempt to create the item.
- **Listing and marketplace publication.** Making the priced product
  purchasable is the `listings` plugin's job.
- **Usage and billing.** Reporting consumption against these prices is
  `connect-usage-converter` (`usage` plugin). Invoices are not in the MCP
  catalog at all.
- **Tool signatures.** Parameter names and shapes come from the catalog,
  not from this skill.
