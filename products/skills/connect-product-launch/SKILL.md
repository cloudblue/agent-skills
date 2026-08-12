---
name: connect-product-launch
description: >-
  Use when a vendor wants a CloudBlue Connect product taken all the way to
  market in one run — product published, prices active, listing submitted —
  across the products, pricing, marketplaces and listings domains. It owns the
  seams between the three stage skills, not their contents: the order, the
  checkpoint before each handoff, and recovery when a stage fails after an
  earlier one already mutated. Triggers on "launch this product end to end",
  "we're going live next Monday, what's left", "why isn't the product we
  launched purchasable", or "resume the launch we started yesterday".
version: 0.1.0
license: Apache-2.0
metadata:
  hermes:
    tags: [CloudBlue, Connect, Products, Pricing, Listings, Launch, MCP]
    category: productivity
    related_skills: [connect-product-builder, connect-pricelist-manager, connect-listing-manager, connect-navigator, connect-mcp-setup]
---

# Connect Product Launch

Going live is three workflows in three domains, and each one already has a skill that owns it. This skill owns **only what happens between them**: the order, the checkpoint before each handoff, the human confirmations the chain inherits, and what is safe to leave behind when a stage fails.

| Stage | What it produces | Owning skill (do not re-derive its steps) |
|---|---|---|
| 1 | A product with a **published version** | `connect-product-builder` (`products` plugin) |
| 2 | A price list with an **active version** in the marketplace currency | `connect-pricelist-manager` (`pricing` plugin) |
| 3 | A **submitted listing request**, then the distributor's answer | `connect-listing-manager` (`listings` plugin) |

Inside a stage, follow that stage's skill. This skill never restates how to choose a parameter phase, map a rate card, or diagnose a stuck request — it tells you *when* the next stage may start and what must be true first.

**Nothing here grants permission.** Each stage skill gates its own outward mutations, and those gates survive being called from a launch: publishing a version, activating prices, and submitting a listing request each still need their own explicit human confirmation, in this conversation. See [Gates are inherited](#gates-are-inherited-never-granted).

## Pre-flight, in one round

The chain stalls if you gather inputs stage by stage. Ask once, for all three stages:

| Input | Consumed by | Why it is needed this early |
|---|---|---|
| Product content — name, items with **MPNs**, units, billing periods, the parameters the buyer must answer | Stage 1 | The stage-1 skill will not invent any of it |
| **Target marketplace(s)** | Stage 0 → 2 → 3 | Its *currency* constrains stage 2 |
| The prices, or the vendor rate card | Stage 2 | |
| Whether they intend to publish and go live *now*, or only to prepare | Gates | "Build it" is not "launch it" |
| An existing `PRD-…` if this is a re-run or a resumed launch | All | Prevents a duplicate product |

### Stage 0 — resolve the marketplace first (read-only)

Marketplace selection belongs to `connect-listing-manager`, but it must run **before** stage 2, not with stage 3. Use the `marketplaces_*` family to resolve the user's prose ("publish to Contoso") to an `MP-…` id and read its **currency** and **owner account**. Echo both back.

Reason: Connect does no FX conversion. A price list in the wrong currency is not fixable by editing prices — it is a different price list — and you will only find out at stage 3, after two irreversible mutations. Ten seconds of reading here is the cheapest checkpoint in the chain.

**Several marketplaces?** Stage 1 happens **once**. Stages 2 and 3 repeat per marketplace, each with its own currency, its own active price list, and its own listing request. Confirm the full list before stage 1, then run the pairs one at a time — never interleave two listings' confirmations.

## The chain, and why the edges exist

```
Stage 0  resolve marketplace + currency        read-only
   │
Stage 1  product → published version           GATE: publish
   │       ↳ connect-product-builder
   │  ── Checkpoint A ──
Stage 2  price list → active version           GATE: activate
   │       ↳ connect-pricelist-manager
   │  ── Checkpoint B ──
Stage 3  listing request → submit              GATE: submit
           ↳ connect-listing-manager
        ── Checkpoint C before the submit gate ──
   │
        distributor deploys and completes       COUNTERPARTY — you stop here
```

- **Published product before price list.** Price points key on the item's **MPN**. Items only exist under a product, and until the version is published the downstream domains have nothing stable to build against. A price list assembled against unpublished items is work you will redo.
- **Active price list before listing submission.** A listing that completes with no active price in the marketplace's currency is live and not purchasable — the worst outcome in the chain, because it looks finished. The stage-3 skill checks for pricing and complains; it does not fix it.
- **Listing last, and it does not end with you.** `submit` hands the request to the distributor. `deploy` and `complete` are the other side's calls, from the other side's account.

## The three checkpoints

A checkpoint is **reads against the tenant**, never your memory of what you just created. If a check cannot be answered by a read, it is not a checkpoint.

### Checkpoint A — before pricing starts

| Verify | How |
|---|---|
| The product version is **published**, not just built | Read the product back with the products domain's `get` family; do not infer it from a successful `products_publish_version` reply alone |
| Every item the user intends to sell exists, with its **final MPN** | List the items and compare against the user's SKU list, character for character |
| Units and billing periods are the ones the user confirmed | Same read — they are effectively frozen from here |
| The marketplace id and currency from stage 0 are still what you will price in | Restate them |

An MPN typo caught here costs a new item. Caught at stage 2 it costs a price list nobody can match; caught at stage 3 it costs a new product version.

### Checkpoint B — before the listing request

| Verify | How |
|---|---|
| A price list exists for this product **in the target marketplace** | `pricing_get_price_list` on the list you worked, and confirm its marketplace |
| Its **currency equals the marketplace currency** from stage 0 | Same read. Mismatch stops the launch — it is not a stage-3 problem |
| A version is **active right now** | `pricing_list_versions`. `scheduled` is the trap: a version effective on the 1st of next month is not active today |
| The active version carries a point for **every item** you are listing | Read the points. An item with no price is an item nobody can buy |

If the user deliberately wants prices to start later, that is a legitimate launch shape — but say it out loud: the listing will go live before the prices do, and name the date. Do not silently submit against a scheduled version.

### Checkpoint C — before the submit gate

Re-read A and B (they are cheap, and stage 2 may have taken days), then:

- **Is there already a listing or listing request for this product and marketplace pair?** If yes, this is an update or an unlisting, not a new request. Creating a second one is the classic launch-re-run failure.
- **Are you on the vendor side?** A distributor token has nothing to submit. Check the account before the `403`, per `connect-listing-manager`.

## Gates are inherited, never granted

An instruction to "launch this product" authorises the read-only work and the reversible drafts. It does **not** collapse three consents into one.

| Gate | Owning skill | What it still requires |
|---|---|---|
| Publish the version | `connect-product-builder` | Its pre-publish checklist, then an explicit yes |
| `pricing_activate_version` (or schedule it) | `connect-pricelist-manager` | The price diff summary, then an explicit yes — and for a schedule, the effective date too |
| `submit` the listing request | `connect-listing-manager` | The assembled request shown, then an explicit yes |

Rules that are this skill's, not theirs:

- **Never bundle two gates into one question.** "Publish and activate?" is one yes buying two irreversible mutations. Ask at the seam you have reached.
- **Never carry consent forward across a checkpoint.** A yes given before stage 1 does not cover a submit three checkpoints later, whatever the user said at the start. If the user pre-authorised the whole launch, still stop at each seam long enough to *report* the mutation you are about to make.
- **Never widen a stage's autonomy because you are orchestrating.** If the stage skill would ask, you ask.

## When a stage fails

The chain is **roll-forward only**. Two of the three stages leave outputs no tool can undo, so a failed launch is reported and resumed — never unwound. **Before touching anything a failed stage left behind, read [`recovery.md`](recovery.md)**: it says which of the six outputs are reversible and what to do with each, and every row that looks like cleanup is a row where cleanup is the wrong move.

Whatever the failure, the launch ends the same way — **report the state as a resume point**, in one message: the `PRD-…` and whether its version is published, the `PL-…` and its active version and currency, the listing request id and status with the marketplace, then the single next action and who owns it. Six facts. A failed launch reported without them cannot be resumed by anyone else.

## Autonomy

Checkpointed by design. The stages themselves are as autonomous as their own skills say; the seams are where you stop.

The rungs are `connect-navigator`'s (free / announce / gated).

| Action | Rung |
|---|---|
| Pre-flight gathering, stage 0 marketplace resolution, all three checkpoints | **free** |
| Everything inside a stage up to that stage's gate | **as the stage skill defines it** — no more |
| The three gates (publish, activate, submit) | **gated** — one confirmation each, at its own seam |
| Anything destructive (delete a version, terminate a price list, cancel a request) | **gated**, and only when the user asks for it by name — never as launch cleanup |
| Distributor `deploy` / `complete` | **counterparty** — report which side owns it, and stop there. If the operator explicitly confirms both accounts are theirs and directs the distributor leg, these become ordinary gates (see `connect-listing-manager`) |

## Non-goals

- **Everything inside a stage.** If you find yourself explaining how to pick a parameter phase, you have left this skill's territory.
- **Commercial decisions.** What the product is, what it costs, which marketplaces to enter. This skill sequences; the vendor decides.
- **Acting for the counterparty.** The distributor's `deploy` and `complete` are their calls from their account. When the chain needs them, say so and stop. A counterparty token being available is not permission — but an operator who explicitly confirms both accounts are theirs and names the transition gets the distributor leg as normal gated steps, not a refusal.
- **Undoing a launch.** There is no un-launch. Teardown is deliberate, destructive, human-driven work and it is not this skill's.
- **Contracts, agreements, offers and packs.** No MCP tools exist for them (see `connect-navigator`). If no distribution contract covers the vendor/distributor pair, the launch cannot complete and the fix is UI work — name it early rather than debugging stage 3.
- **Connection and permission problems.** Any `401`/`403` is `connect-mcp-setup` (`core` plugin), not a launch problem. What *is* worth knowing here: a launch spans four module permissions (Products, Pricing, Marketplaces, Listings), so a token that cleared stage 1 can still `403` at stage 2. Check the whole set during pre-flight rather than one stage at a time.
