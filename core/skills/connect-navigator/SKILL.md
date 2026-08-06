---
name: connect-navigator
description: Use in any session that works with the CloudBlue Connect MCP catalog — which of the nine domains owns a concept, what a VerboseID prefix like PRD-, PL- or AS- refers to, the filter and pagination conventions the list tools share, and the free/announce/gated rungs every Connect skill sorts its mutations onto. Triggers on "which Connect tool do I use for X", "what does PRD- mean", "how do I filter Connect lists", "does this Connect call need confirmation", or whenever another skill defers to the shared conventions.
version: 0.1.0
license: Apache-2.0
metadata:
  hermes:
    tags: [CloudBlue, Connect, MCP, Navigation, Catalog]
    category: productivity
    related_skills:
      [
        connect-mcp-setup,
        connect-product-builder,
        connect-pricelist-manager,
        connect-listing-manager,
        connect-request-triage,
        connect-subscription-ops,
        connect-helpdesk-triage,
        connect-usage-converter,
        connect-product-launch,
      ]
---

# Connect Navigator

The Connect MCP endpoint exposes one flat catalog of ~100 tools across nine domains. This skill is the map: it tells you **where to look** — which domain owns a concept, what an ID prefix means, how the list tools behave — so you pick the right tool family on the first try instead of probing.

It never tells you **what to do**: workflows (how to build a product, activate a price list, triage a request) belong to the domain skills. This skill ends when you know which domain and tool family to read.

It also holds the conventions every domain skill defers to: how tool names are resolved, how the list tools behave, and what makes a mutation
**gated**. See [Shared conventions](#shared-conventions) and [Mutations](#mutations-free-announce-gated).

## The nine domains

| Domain | Owns |
|---|---|
| `pricing` | price lists, versions, price points, adjustments |
| `fulfillments` | fulfillment requests: creation + lifecycle transitions |
| `products` | products, items, parameters, templates |
| `listings` | listing requests (vendor → distributor publication) |
| `usage` | usage files and records (pay-per-use reporting) |
| `helpdesk` | support cases |
| `tier_accounts` | tier accounts and tier account requests |
| `marketplaces` | marketplaces |
| `assets` | subscription read access |

Tool names carry the domain prefix in every domain (`pricing_get_price_list`, `products_publish_version`, `usage_get_conversion_guide`) — with one exception: the `assets` domain's tools are prefixed `subscriptions_*`, not `assets_*` (the domain keeps the platform's module name; the tools speak the user's word).

## Concept → domain

Includes the aliases users actually say.

| You hear | Domain | Note |
|---|---|---|
| product, item, SKU, MPN, parameter, template | `products` | |
| price list, price point, rate card, price version | `pricing` | |
| listing, "publish to a marketplace", listing request | `listings` | |
| marketplace | `marketplaces` | read/select; listings do the publishing |
| subscription, asset | `assets` | read-only, tools prefixed `subscriptions_*`; *changing* one goes through `fulfillments` |
| purchase / change / cancel / suspend / renew order, fulfillment request, "pending request" | `fulfillments` | |
| tier account, T1 / T2, customer hierarchy, tier account request | `tier_accounts` | T1 is closest to the end customer |
| usage, consumption, billing report upload, usage file | `usage` | |
| case, ticket, support request | `helpdesk` | |

**Both sides of one transaction:** `fulfillments` serves the vendor processing inbound requests *and* the distributor/reseller creating outbound ones. `listings` likewise — the vendor submits, the distributor approves. Which actions succeed depends on the account behind the token, not on separate tool sets.

## Tier vocabulary

`tier_accounts` is the smallest domain and the one whose words collide most.

- **The end customer is a tier account too.** A subscription carries a small hierarchy of tier accounts, all `TA-` objects: the **customer** (the end customer the subscription serves) at the base, **T1** directly above it (typically the reseller serving the customer), and **T2** one level above T1 (a reseller selling through T1). The distributor or provider operating the marketplace is **T0** and is the only actor in the chain that is *not* a tier account. How many reseller levels a channel uses is a setup decision — many use T1 only, so "the tier account" in conversation almost always means T1.
- **A tier account is not a Connect account.** `TA-` objects describe the reseller or customer entity a subscription was sold to — names, contacts, external ids carried over from the partner's own systems. Accounts that carry logins and permissions are `VA-`/`PA-` and have no tools.
- **`TA-` vs `TAR-`.** `TA-` is the tier account. `TAR-` is a tier account *request* — a proposed change to a tier account's data that the receiving side either accepts or ignores. Both live in `tier_accounts`, they are different objects, and the prefixes are one character apart.
- **Tier account data is versioned.** The account carries a current version with earlier ones kept as history, so "this tier account changed" is a version question. Fetch the account before trusting a value quoted from a list row or from another domain's response.
- **Tier accounts mostly arrive, they are not authored.** A T1/T2 account normally enters Connect with the fulfillment request that sold the subscription, which is why most work in this domain is read-and-verify. The request traffic itself belongs to `fulfillments`.
- **Tier *config* is a different thing.** Tier configuration parameters — the per-tier values a vendor collects from each tier — are product parameters and live in `products`. If the user says "tier config" they mean parameter design, not the account record.

Only two actions in this domain change anything: accepting or ignoring a tier account request. Both settle a counterparty's proposal and neither is reversible, so confirm with the user before either.

## What has no tools

Connect concepts with **no MCP tools** — don't probe the catalog for them; they live only in the UI/REST API: billing, reports, extensions (EaaS), accounts, contracts, offers, packs, leads, notifications. If the user's goal centers on one of these, say so early instead of searching.

## VerboseID prefixes

Every Connect object ID starts with a type prefix — recognizing one tells you the domain before anyone explains.

| Prefix | Object | Domain |
|---|---|---|
| `PRD-` | product | `products` |
| `PL-` | price list | `pricing` |
| `LST-` | listing | `listings` |
| `MP-` | marketplace | `marketplaces` |
| `AS-` | subscription (asset) | `assets` |
| `PR-` | fulfillment request | `fulfillments` |
| `TA-` | tier account | `tier_accounts` |
| `TAR-` | tier account *request* — a different object, one character away | `tier_accounts` |
| `UF-` | usage file | `usage` |
| `CA-` | helpdesk case | `helpdesk` |
| `VA-` / `PA-` | vendor / provider (distributor or reseller) account | — (identity, no tools) |
| `CRD-` | distribution contract | — (no tools; asked for by `usage` flows) |

## Shared conventions

The tools follow one server-side standard across domains:

- **Tool names and parameter schemas come from the catalog, never from a skill.** The domain skills name *verbs* (`submit`, `approve`, `activate`) and *families* (the pricing adjustment family) because a name copied into a skill goes stale and a verb does not. Read the descriptions of the family you need once per session and match each verb to its tool. A verb with no tool in your catalog is UI-only — say so, and use the documented path instead. A guessed name fails as an unknown tool, which reads like a broken connection and costs the user a debugging session.
- **Pagination:** `limit` (default 10, max 100) and `offset` on every `*_list_*` tool.
- **Filters are flat parameters**, not query languages: equality filters named after the field (`status`, `product_id`), substring as `<field>_contains`, ranges as `<field>_min` / `<field>_max` or `created_after` / `created_before`. No RQL strings.
- **List returns are minimal** — typically id + name. Fetch the domain's `get` tool for full detail before reasoning about an object; don't assume a list row carries the fields you need.
- **Create/update is usually one `manage` tool** per resource, distinguished by whether you pass an existing id — but not in every domain: pricing splits them (`pricing_create_price_list` / `pricing_update_price_list`, same for versions), and so do the products domain's templates and versions. Match the verb to the catalog, don't assume the pattern. Where a resource is split, the two halves are usually not interchangeable: the create tool often accepts fields the update tool cannot write, because the API's own create and update serializers differ.
- **`403` means permissions, not a bug.** Every `403`, and every token or connection problem, is the `connect-mcp-setup` skill's territory (`core` plugin) — it owns the permission model. A domain skill names the modules its own work needs and hands the diagnosis over.

## Mutations: free, announce, gated

Each domain skill sorts its own actions onto these three rungs. The rungs mean the same thing in every domain, so they are defined here once.

| Rung | What sits on it | What you do |
|---|---|---|
| **free** | Reads — every `*_list_*` and `*_get_*` call | Just do it. Never ask permission to read |
| **announce** | Own-side mutations nobody outside your account can see: a draft, an unpublished version, a queue assignment. Reversible and invisible | Do it, then say what you did |
| **gated** | Every **outward-facing** mutation: the counterparty sees it, or it moves money, entitlement or service | Stop. State the call and its effect, then wait for a yes |

**Outward-facing** is the test, not reversibility. A `submit` you could cancel a minute later has still reached the other party, and a draft you can never delete has still reached nobody. When a rung is unclear, ask who can see the result.

A **gate** means: name the exact call and the object it hits, state what changes for the counterparty, then wait for the user to say yes *in this conversation*. One yes covers the one call you described and does not carry forward to the next.

An instruction that names the mutation is itself that yes — "approve PR-1234", "add five seats" — so a gate met up front is met, and re-asking is friction. What is never a yes is the instruction that merely set the goal: "get the product listed" authorises the reads and the draft, not the `submit`. The exception is a mutation that destroys or moves live service, which each domain skill marks: those get restated and confirmed even when the user ordered them by name.
