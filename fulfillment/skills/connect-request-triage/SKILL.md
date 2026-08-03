---
name: connect-request-triage
description: Use on the vendor side of CloudBlue Connect fulfillment, when an inbound fulfillment request (PR-…) needs a decision — pick the correct lifecycle transition (approve, inquire, pend, fail, schedule, revoke) and justify it, triage a pending queue, or work out what an `inquiring` request is actually waiting for. Triggers on "should I approve or fail PR-1234", "triage our fulfillment queue", "which parameter is this order waiting on", or "why hasn't this subscription activated".
version: 0.1.0
license: Apache-2.0
metadata:
  hermes:
    tags: [CloudBlue, Connect, Fulfillment, Subscriptions, Triage, MCP]
    category: productivity
    related_skills: [connect-subscription-ops, connect-navigator, connect-mcp-setup]
---

# Connect Request Triage

You are working the **inbound** side of Connect fulfillment: requests arrive
in your queue and you decide what happens to each one. This is the vendor's
seat. The opposite side — creating outbound changes against a subscription
you own as distributor or reseller — is the `connect-subscription-ops`
skill in this same plugin.

**Autonomy.** Reading a request, diagnosing it and recommending a transition
is **free** — do all of it without asking. Every transition itself is
**outward-facing**: the customer sees the result and it is commercially
binding, so every transition is **gated** (`connect-navigator`'s rungs). You
present the recommendation and wait. The one exception is a user who has
already named the transition ("approve PR-1234") — then read the request
first, confirm the evidence supports what they asked for, say so, and proceed.

## Before you start

Reading the *product's* parameter definitions means the `products` domain and
the **Products** module permission, which is a different plugin. If the token
doesn't carry it, report the parameter's meaning as unknown rather than
guessing at it.

## Tool names: match on the verb

This skill is written in **verbs** — see `connect-navigator`, Shared
conventions. Read each transition tool's description **before** the first
call in a session: the required arguments differ per transition (a reason
string, a list of parameters, an effective date), and getting one wrong is a
failed mutation against a live request.

## Read the request before you judge it

1. **Get the request.** Never triage from a list row — list returns are
   minimal (id, status, type). Fetch the request itself.
2. **Note four things:** its **type** (purchase / change / cancel /
   suspend / resume / adjustment / …), its **status**, the **subscription**
   (`AS-…`) and product it affects, and its **parameters**.
3. **Read the subscription** (`assets`, read-only) when the request's own
   payload doesn't explain it — current items and quantities, current
   parameter values, current status.
4. Only then choose.

## Who has to act next

Status answers "is this even mine?" before any transition is considered.

| Status | Waiting on | Your move |
|---|---|---|
| `pending` | **you** | choose a transition (table below) |
| `inquiring` | the customer / orderer | nothing — or `pend` to pull it back into your queue |
| `draft` | the side that created it | not yours; created via API and not yet promoted (see `connect-subscription-ops`) |
| `tiers_setup` | tier account resolution | wait; not a fulfillment decision (`tier_accounts` domain) |
| `scheduled` | the clock | nothing, unless the effect must be withdrawn → `revoke` |
| `revoking` | the platform | wait |
| `approved` / `failed` / `revoked` | nobody | terminal; a new request is the only way forward |

Statuses are the product's, not this skill's. If a request shows a status
that isn't in this table, read the request payload and the transition tool
descriptions rather than forcing it into a row.

## Choosing the transition

For a `pending` request, the evidence picks the verb:

| Evidence | Transition | What it means |
|---|---|---|
| Parameters complete, the entitlement can be delivered | `approve` | fulfils the order — this is what activates or updates the subscription. Commercially binding |
| A required ordering parameter is missing, empty, or holds an invalid value | `inquire` | hands the request back to the customer to fix. Name **every** parameter you are asking about, each with a reason the customer can act on |
| You want an `inquiring` request back in your own queue | `pend` | returns it to `pending`; the customer stops being blocked |
| Delivery is impossible **and will not become possible** — unsupported region, duplicate order, a hard vendor-side rejection | `fail` | terminal and irreversible. The customer must re-order. Always the last option, never a way to clear a queue |
| The change or cancellation should take effect on a future date (typically end of billing period) | `schedule` | the request holds until the date; billing follows the schedule |
| A `scheduled` request must not take effect after all | `revoke` | withdraws the pending effect |

Two more the catalog exposes and this skill does not route for you:

- **`confirm`** promotes a `draft` request into the fulfilling side's
  queue. It is **not** a synonym for `approve` — it does not fulfil
  anything, and it normally belongs to whoever created the request
  (`connect-subscription-ops`). Read its tool description before using it.
- The domain carries a small number of transitions beyond the ones named
  here (assignment and scheduling companions). Enumerate them from the
  catalog when a request doesn't fit any row above.

**Never approve to make a stuck request go away.** Approving delivers the
order: it activates entitlements and starts billing. If you cannot say what
the customer receives, you cannot approve.

**Prefer `inquire` over `fail` whenever the blocker is data.** `fail` is for
"this can never work", not "this is missing something".

## Justify, then wait

Every recommendation you present contains all six of these. If you cannot
fill one in, you are not ready to recommend:

1. The request — id, type, current status, how long it has been there.
2. What it affects — subscription `AS-…`, product, items and quantities.
3. The evidence — the specific parameter, item, quantity, or account fact
   that decides it. Quote the value you read; don't paraphrase.
4. The transition you recommend.
5. **Why not the alternatives** — explicitly why not `approve` and why not
   `fail`, since those are the two irreversible ones.
6. What the customer sees next, and who is then blocked.

Then state the mutation and stop:

> This will call the `fulfillments` **inquire** transition on PR-1234-5678,
> flagging the `domain_name` ordering parameter. The request leaves our
> queue and the customer is notified they must supply a value. Confirm and
> I'll do it.

One confirmation can cover a set, but the set has to be enumerated. If ten
requests need the same transition, present all ten with their evidence and ask
once, naming every request that the yes covers. An eleventh found afterwards
gets its own ask.

## Resolving `inquiring`

The question is always "which parameter, and what does a good value look
like". Work it in this order:

1. **Get the request** and read its parameters. The one being asked for
   shows an empty value, or carries the error/justification text set by
   whoever inquired. That text is the answer most of the time — surface it
   verbatim.
2. **If nothing is flagged**, compare the request's parameters against the
   product's parameter definitions (`products` domain) and report which
   required ones are unset.
3. **Check the phase.** Only **ordering** parameters are the customer's to
   fill. **Fulfillment** parameters are the vendor's own output — if the
   blocker is a fulfillment parameter, inquiring was the wrong transition
   and the fix is on your side. **Configuration** parameters aren't part of
   a request at all.
4. **Report** the parameter's name and title, its phase, its constraints,
   and an example of a valid value.

You cannot fill an ordering parameter on the customer's behalf — that is
the counterparty's action, and waiting on it is a legitimate resting state
for a request. Say so plainly instead of looking for a transition that
makes the wait disappear.

**How the answer actually arrives.** The customer fills the request's
activation form (the `params_form_url` on the inquiring request — the
storefront re-sends it), not any vendor API. There is no MCP tool that
writes parameter values into a request, and the REST update is only
accepted for products with the *inquiring validation* capability — without
it the API answers `REQ_001` ("Only pending, draft or inquiring
Fulfillments with enabled validation capability can be updated"). If the
user relays a value in chat, the honest move is to say which channel it
must go through, not to write it for them.

**Reading the diagnosis may need the REST request object.** The
subscription-side parameter read can omit `value_error` and the
constraints; the request's own REST representation carries them. If the
flagged text isn't visible through the tools, say which parameter is
empty-and-required instead of guessing at the error text.

## When triage says the problem isn't the request

| Symptom | Actual cause | Where it lives |
|---|---|---|
| Request has been `inquiring` for days with nobody reacting | the inquire named no parameter, so the customer has nothing to act on | `pend` it, then re-inquire with specifics |
| `approve` is refused or the subscription doesn't activate | the product's fulfillment side is incomplete — activation template or fulfillment parameters | `products` domain (`catalog` plugin) |
| Reads work, every transition returns `403` | token account is on the wrong side of the transaction | `connect-mcp-setup` (`core` plugin) |
| Stuck in `tiers_setup` | tier account data incomplete | `tier_accounts` domain — see `connect-navigator`, Tier vocabulary |
| Queue full of near-identical `pending` purchases | upstream commerce is retrying; triaging them one by one is the wrong fix | escalate, don't approve the duplicates |

## Non-goals

- **Creating requests.** Change, cancel, suspend, resume, renew,
  adjustment and transfer are outbound actions — `connect-subscription-ops`.
- **Product content.** Parameter and template design belongs to the
  `products` domain, not here. This skill reads them to explain a blocker.
- **Commercial policy.** Whether a customer *should* get an exception, a
  refund, or a manual approval is the human's call. You supply the
  evidence and the consequence; you don't decide the business outcome.
- **Support cases.** A partner conversation about a request is `helpdesk`.
