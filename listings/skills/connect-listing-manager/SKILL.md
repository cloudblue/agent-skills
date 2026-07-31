---
name: connect-listing-manager
description: Use when publishing a CloudBlue Connect product onto a distributor's marketplace, moving a listing request through its lifecycle, or working out why a listing is stuck and who has to act next. Triggers on "list our product on the Contoso marketplace", "the listing request has been in reviewing for two weeks", "approve this listing request", "send the listing request back to the vendor", or "unlist a product from a marketplace".
version: 0.1.0
license: Apache-2.0
metadata:
  hermes:
    tags: [CloudBlue, Connect, Listings, Marketplaces, MCP]
    category: productivity
    related_skills: [connect-navigator, connect-mcp-setup]
---

# Connect Listing Manager

A **listing** is a product made available on one distributor marketplace. It
gets there through a **listing request**, and the request is a two-party
state machine: the vendor asks, the distributor answers. Neither side can
finish it alone.

That is what this skill is for. Two jobs:

1. **Drive the machine** — pick the marketplace, open the request, and move
   it through `submit` → `deploy` → `complete`, or sideways through
   `refine` / `cancel` / `assign` / `unassign`.
2. **Diagnose a stuck one** — given a listing that isn't live, name the
   state it is actually in and **which side must act next**. This is the
   half people get wrong, because "nothing is happening" almost always
   means "it is the other party's turn and nobody told them".

## Before you call anything

**Verbs, not tool names.** The `listings` domain has 12 tools and
`marketplaces` has 4. This skill names the *transition verbs* (`submit`,
`deploy`, `complete`, `refine`, `cancel`, `assign`, `unassign`) and the
*families* (`listings_*`, `marketplaces_*`); the names come from the catalog,
per `connect-navigator`, Shared conventions.

**Check which side you are on first.** The same tools are served to both
parties; the account behind the token decides which calls succeed. A vendor
token cannot `deploy`, a distributor token has nothing to `submit`. Work out
the side before planning, not after a `403`. Connection and permission
problems themselves belong to `connect-mcp-setup` (`core` plugin); domain
and ID-prefix questions to `connect-navigator`.

**Two objects, don't conflate them.** The listing (`LST-…`) is the durable
publication record; the listing request is the change ticket that creates,
modifies or removes it. "The listing is in reviewing" is never true — a
*request* is. Read the request's own id off the object rather than assuming
its prefix.

## Choose the marketplace

A listing request targets exactly one marketplace (`MP-…`), so this decision
comes first and it is read-only — do it without asking permission.

Use the `marketplaces_*` family: list to find the candidates the token can
see, then fetch the one you intend to use for its detail (currency, owner,
hub). What to check before committing to it:

| Check | Why it matters |
|---|---|
| Currency | The product needs an active price list in **that** marketplace's currency. Mismatch is the most common late failure. |
| Owner account | The distributor that owns the marketplace is the party that will review your request. It must be one you hold a distribution contract with. |
| Existing listing | If the product is already listed there, you want an update or unlisting request, not a new one. Check before creating. |

If the user names a marketplace in prose ("publish to Contoso"), resolve it
to an `MP-` id and **echo back the resolved name plus currency** before
going further. Listing to the wrong marketplace is cheap to do and
embarrassing to undo.

## The state machine

```
                   ┌──────── refine ────────┐
                   ▼                        │
  (create) ──► draft ──► submit ──► reviewing ──► deploy ──► deploying
                                        │                        │
                                        │                     complete
                                        │                        ▼
                                        │                    completed
                                        │
                                        └──── cancel ──►   canceled
```

| State | Ball is with | Legitimate next move |
|---|---|---|
| `draft` | **vendor** | edit the request, then `submit` |
| `reviewing` | **distributor** | `assign` for ownership, then `deploy` or `refine` |
| `deploying` | **distributor** | finish the provisioning work, then `complete` |
| `completed` | nobody | terminal — the listing is live |
| `canceled` | nobody | terminal — open a new request |

`refine` is the only backward edge: it returns the request to the vendor for
changes. `cancel` is reachable from any non-terminal state by either side and
is terminal — there is no un-cancel.

State names above are the shape of the lifecycle, not a schema. Trust the
`status` value the `get` tool returns over this table if they disagree, and
say so.

## Transitions and their gates

Every verb below **mutates**. The rungs are `connect-navigator`'s and the
column is not advisory.

| Verb | Side | Effect | Rung |
|---|---|---|---|
| create / edit draft | vendor | Own-side, reversible, invisible to the counterparty | **announce** — confirm the marketplace and product first |
| `submit` | vendor | **Outward-facing.** Hands the request to the distributor; you lose unilateral control | **gated** — never as the tail of a longer plan |
| `assign` / `unassign` | distributor | Internal queue ownership. No effect on the vendor | **announce** — the one mutation here that never reaches the other side |
| `deploy` | distributor | **Outward-facing.** Accepts the request and commits to publishing | **gated** |
| `complete` | distributor | **Outward-facing and effectively irreversible.** The listing goes live and becomes buyable | **gated** — restate what goes live in which marketplace before asking |
| `refine` | distributor | **Outward-facing.** Sends the request back to the vendor | **gated** — the reason must be concrete enough for the vendor to act on. Draft the note, show it, then send |
| `cancel` | either | **Terminal.** Kills the request | **gated** — check whether `refine` (fixable) is what they actually meant |

## Vendor path

1. Confirm the product and marketplace. The product must already exist and
   have a published version, and it needs an active price list in the
   marketplace currency. Neither is this skill's job (see Non-goals) — but
   check them before submitting, because the failure surfaces here.
2. Look for an existing listing for that product/marketplace pair.
3. Create or update the draft request.
4. Show the user the assembled request. **Stop.**
5. On confirmation, `submit`. Then one read to confirm the new state,
   report it, and stop — see below.

## Distributor path

1. List the requests in `reviewing`. Fetch the ones you care about; list
   rows carry little more than an id.
2. `assign` for ownership if the queue works that way.
3. Decide: is the request complete and correct?
   - Not correct → draft a concrete `refine` reason, confirm, send. The ball
     goes back to the vendor.
   - Correct → confirm, `deploy`.
4. Do the provisioning work the marketplace requires while the request sits
   in `deploying`. Some of it is UI-only; say so rather than hunting for a
   tool.
5. Confirm, `complete`. The listing is live.

## Waiting is a valid end state

Once you have made an outward-facing transition, **the workflow is not
"in progress" — it is finished for your side.** Do this:

- One read after the transition to confirm the state changed.
- Report the new state and name the party who now owns it.
- Stop.

A listing request is answered on human timescales — hours to days — so the next
tool call belongs to the next conversation: when the user comes back, one `get`
answers them. Escalation here is a message to the counterparty, not another
call. A second `submit` against a request already with the distributor either
errors or creates a duplicate.

## Diagnose a stuck listing

The question is almost never "what is broken", it is "whose turn is it".
**Work the ladder in [`diagnose.md`](diagnose.md) in order and stop at the
first answer** — it covers the seven states a stuck listing can be in, starting
with the most common by far (a draft nobody submitted).

Report the diagnosis as: **state → owning side → the one action that
unblocks it → who has to take it.** Four facts. A diagnosis that doesn't
name a person or an account is not finished.

## Non-goals

- **Creating the product**, its items, parameters or templates — that is
  `connect-product-builder` (`catalog` plugin). This skill assumes a
  published product version exists.
- **Creating or activating price lists** — `connect-pricelist-manager`
  (`pricing` plugin). It checks that pricing is in place and complains if it
  isn't; it does not fix it.
- **Approving on the counterparty's behalf.** Approval is the other side's
  action and often the other side's account. When the workflow needs them,
  the skill's job is to say so and stop.
- **Contracts, agreements, offers and packs.** No MCP tools exist for them
  (`connect-navigator`); they are UI/REST work.
- **Marketplace creation or configuration.** The `marketplaces_*` tools here
  are used to select and inspect, not to build.
