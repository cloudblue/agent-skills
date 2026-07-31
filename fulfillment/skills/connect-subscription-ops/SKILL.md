---
name: connect-subscription-ops
description: Use to inspect or change an existing CloudBlue Connect subscription (asset, AS-…) from the distributor or reseller side — read its items, quantities and parameters, then issue the change / cancel / suspend / resume / renew / adjustment / transfer as a fulfillment request. Triggers on "cancel subscription AS-1234", "change the seat count on this Connect subscription", "suspend this customer for non-payment", "transfer a subscription to another account", or "what items and parameters does this subscription have".
version: 0.1.0
license: Apache-2.0
metadata:
  hermes:
    tags: [CloudBlue, Connect, Subscriptions, Fulfillment, Assets, MCP]
    category: productivity
    related_skills: [connect-request-triage, connect-navigator, connect-mcp-setup]
---

# Connect Subscription Ops

You are working the **outbound** side: a subscription exists, someone wants
it changed, and you own the account that can ask. This is the
distributor/reseller seat. Processing requests that arrive *at* you is the
`connect-request-triage` skill in this same plugin.

**The shape of every task here is the same:** `assets` is read-only.
Nothing about a subscription changes by writing to it — you read the
subscription, then **create a fulfillment request** that carries the change.
The request then has a lifecycle you do not control.

**Autonomy.** Reads are **free**. Every `create_*` is **outward-facing** — it
lands in the vendor's queue and changes what the customer is entitled to or
billed for — so all seven are **gated** (`connect-navigator`'s rungs). For
`change`, `resume`, `renew` and `adjustment` the user's order *is* the yes:
announce what you are doing, issue it, report the resulting `PR-…`, and don't
ask twice. **`cancel`, `suspend` and `transfer` are the exception**: they
remove or move a live customer's service, so restate exactly what will happen
and get one confirmation even when the user named the intent. Once confirmed,
proceed without re-asking.

## Before you start

The `assets` domain has three read tools; `fulfillments` carries seven
`create_*` request families, one per intent below. Match on the intent and take
the names from the catalog (see `connect-navigator`, Shared conventions). Read
the chosen tool's description before the first call — the arguments differ
sharply between a change (item quantities) and a transfer (target account), and
a malformed create is a bad request against a live subscription.

## 1. Identify the subscription

You need one `AS-…` id and you must be certain of it. If the user gave you
a customer name, a product name, or a marketplace instead, list
subscriptions with the flat filters the list tools take and **show the
candidates** rather than picking one. Acting on the wrong subscription is
the single most expensive mistake available in this skill.

If more than one subscription matches and the intent is destructive, stop
and ask which. Never disambiguate by guessing at "the most likely one".

## 2. Read it before you change it

Always, even when the user told you the current numbers. List rows are
minimal; fetch the subscription itself and read:

- **status** — an `active` subscription and a `suspended` one accept
  different intents (you cannot suspend what is already suspended, and
  resuming a *terminated* subscription is not a thing).
- **items** — MPN, unit, and the **current quantity of each**. This is what
  a change request is built from.
- **parameters** — current ordering and fulfillment values, in case the
  change touches one.
- whether a request is **already in flight** against it. A subscription
  with a `pending` or `scheduled` request usually cannot take another;
  surface the existing `PR-…` instead of stacking a second.

## 3. Pick the request family

| The user wants | Family | Notes |
|---|---|---|
| more/fewer seats, a different item mix, a parameter value updated | **change** | carries the **target** state, not a delta — see below |
| the subscription ended | **cancel** | terminal. Entitlement lost, billing stops. `resume` does not undo it |
| service paused, to be restored later | **suspend** | reversible via `resume`. Use this for non-payment, not `cancel` |
| a suspended subscription back in service | **resume** | only valid from `suspended` |
| the term extended | **renew** | term-based commitments only; check the tool description for whether it takes a period |
| a correction to quantity or billing that is not a customer order | **adjustment** | read the tool description before reaching for it — it is not a general substitute for `change` |
| the subscription moved to a different account or marketplace | **transfer** | the most precondition-heavy of the seven. Confirm the target with the user and read the tool description in full |

### A change request is absolute, not incremental

"Add five seats" means: read the current quantity, add five, and send the
**resulting total**. Sending `5` when the customer has 20 and wanted 25 is
a downgrade to 5 — a silent, billable, service-affecting mistake that looks
exactly like success. This is why step 2 is not optional.

State the arithmetic when you announce the change: "currently 20, you asked
for +5, so the request sets 25."

### Cancel and suspend are not interchangeable

Users say "cancel" for both. Before issuing either, resolve which they
actually mean by the *outcome* they described:

- "they'll pay next week", "pause it", "hold it" → **suspend**
- "they're leaving", "close the account", "end it" → **cancel**

If the words don't settle it, ask. Getting this wrong either destroys a
customer's service and data or keeps billing someone who left.

## 4. Announce, then issue

Every `create_*` call mutates. Before the call, state in one block: the
subscription id and the customer it belongs to, the intent, the concrete
before → after (quantities, dates, target account), and the effect on
entitlement and billing.

For `change`, `resume`, `renew` and `adjustment`, announcing is enough —
the user already ordered it, so say what you're doing and do it.

For `cancel`, `suspend` and `transfer`, that block is a **question**, asked
once:

> AS-1234-5678-9012 (Acme Corp, 20 × M365-E3). Cancelling ends the
> subscription: the entitlement is withdrawn and billing stops. This cannot
> be reversed with `resume` — restoring service would need a new purchase.
> Confirm?

Also flag, before issuing, anything you noticed in step 2 that the user
probably didn't: a scheduled renewal about to fire, an in-flight request, a
suspended status that changes what the intent will do.

## 5. Report the request, then hand off

A `create_*` call returns a **fulfillment request** (`PR-…`), not a changed
subscription. Nothing has happened to the subscription yet. Always report:

- the `PR-…` id and its **status**,
- who is now blocked — normally the vendor's fulfillment side, which is
  where `connect-request-triage` picks it up,
- whether the effect is immediate or scheduled.

Two statuses need action from you specifically:

- **`draft`** — the request was created but is not yet in the fulfilling
  side's queue. It needs the promoting transition (the `fulfillments`
  domain exposes `confirm` among its transitions); read that tool's
  description and say clearly that the change is *not yet submitted* until
  it is called.
- **`inquiring`** — the vendor is asking your side for a parameter value.
  That is yours to answer, and the parameter is named in the request.

Do not claim the change is done because the create succeeded. The honest
report is "requested, PR-1234-5678, pending vendor fulfilment".

## When it doesn't work

| Symptom | Likely cause |
|---|---|
| `create_*` refused, subscription looks fine | a request is already in flight; find and resolve it first |
| Reads fine, every create returns `403` | token's account is on the wrong side of the transaction (`connect-mcp-setup`) |
| Request created, then went straight to `failed` | the vendor's fulfillment side rejected it — read the request's reason, don't re-issue blindly |
| Request sits in `pending` for days | the vendor has not triaged it; that is `connect-request-triage`'s side, not a defect here |
| Change accepted but quantities are wrong | an incremental value was sent where an absolute total was required — see step 3 |

## Non-goals

- **Processing inbound requests.** Choosing and justifying `approve` /
  `inquire` / `fail` on a request that arrived at you is
  `connect-request-triage`.
- **Pricing.** What the change costs is the `pricing` domain. This skill
  does not quote, discount, or explain a price.
- **Product content.** Which items and parameters exist is the `products`
  domain. You read them; you don't define them.
- **The commercial decision.** Whether to cancel, discount, or suspend a
  customer is the human's. You execute a decision already made and make its
  consequences explicit first.
