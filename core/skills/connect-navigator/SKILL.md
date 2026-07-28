---
name: connect-navigator
description: Use in any session that works with the CloudBlue Connect MCP catalog, to locate the right tool family before probing — which of the nine domains owns a concept, what a VerboseID prefix like PRD-, PL-, LST-, AS- or CA- refers to, and the filter/pagination conventions shared by the list tools. Triggers on questions like "which Connect tool do I use for X", "where do subscriptions live in Connect", "what is a PL- id", "what does PRD- mean", "how do I filter Connect lists", or whenever the agent is about to search the Connect tool catalog for the right call.
version: 0.1.0
license: Apache-2.0
metadata:
  hermes:
    tags: [CloudBlue, Connect, MCP, Navigation, Catalog]
    category: productivity
    related_skills: [connect-mcp-setup]
---

# Connect Navigator

The Connect MCP endpoint exposes one flat catalog of ~100 tools across nine
domains. This skill is the map: it tells you **where to look** — which
domain owns a concept, what an ID prefix means, how the list tools behave —
so you pick the right tool family on the first try instead of probing.

It never tells you **what to do**: workflows (how to build a product,
activate a price list, triage a request) belong to the domain skills. The
tool catalog itself is the source of truth for exact tool names and
parameters — read the tool descriptions once this skill has pointed you at
the right family.

## The nine domains

| Domain | Owns |
|---|---|
| `pricing` | price lists, versions, price points, adjustments |
| `fulfillments` | fulfillment requests: creation + lifecycle transitions |
| `products` | products, items, parameters, templates |
| `listings` | listing requests (vendor ↔ distributor publication) |
| `usage` | usage files and records (pay-per-use reporting) |
| `helpdesk` | support cases |
| `tier_accounts` | tier accounts and tier account requests |
| `marketplaces` | marketplaces |
| `assets` | subscription read access |

Tool names in most domains carry the domain prefix
(`pricing_get_price_list`, `products_publish_version`); the `usage` domain
is the exception — its tools are unprefixed (`get_conversion_guide`,
`manage_usage_file`).

## Concept → domain

Includes the aliases users actually say.

| You hear | Domain | Note |
|---|---|---|
| product, item, SKU, MPN, parameter, template | `products` | |
| price list, price point, rate card, price version | `pricing` | |
| listing, "publish to a marketplace", listing request | `listings` | |
| marketplace | `marketplaces` | read/select; listings do the publishing |
| subscription, asset | `assets` | read-only; *changing* one goes through `fulfillments` |
| purchase / change / cancel / suspend / renew order, fulfillment request, "pending request" | `fulfillments` | |
| tier account, T1 / T2, customer hierarchy, tier account request | `tier_accounts` | T1 is closest to the end customer |
| usage, consumption, billing report upload, usage file | `usage` | |
| case, ticket, support request | `helpdesk` | |

**Both sides of one transaction:** `fulfillments` serves the vendor
processing inbound requests *and* the distributor/reseller creating
outbound ones. `listings` likewise — the vendor submits, the distributor
approves. Which actions succeed depends on the account behind the token,
not on separate tool sets.

## What has no tools

Connect concepts with **no MCP tools** — don't probe the catalog for them;
they live only in the UI/REST API: billing, reports, extensions (EaaS),
accounts, contracts, offers, packs, leads, notifications. If the user's
goal centers on one of these, say so early instead of searching.

## VerboseID prefixes

Every Connect object ID starts with a type prefix — recognizing one tells
you the domain before anyone explains.

| Prefix | Object | Domain |
|---|---|---|
| `PRD-` | product | `products` |
| `PL-` | price list | `pricing` |
| `LST-` | listing | `listings` |
| `MP-` | marketplace | `marketplaces` |
| `AS-` | subscription (asset) | `assets` |
| `PR-` | fulfillment request | `fulfillments` |
| `TA-` / `TAR-` | tier account / tier account request | `tier_accounts` |
| `UF-` | usage file | `usage` |
| `CA-` | helpdesk case | `helpdesk` |
| `VA-` / `PA-` | vendor / provider (distributor or reseller) account | — (identity, no tools) |
| `CRD-` | distribution contract | — (no tools; asked for by `usage` flows) |

## Shared conventions

The tools follow one server-side standard across domains:

- **Pagination:** `limit` (default 10, max 100) and `offset` on every
  `*_list_*` tool.
- **Filters are flat parameters**, not query languages: equality filters
  named after the field (`status`, `product_id`), substring as
  `<field>_contains`, ranges as `<field>_min` / `<field>_max` or
  `created_after` / `created_before`. No RQL strings.
- **List returns are minimal** — typically id + name. Fetch the domain's
  `get` tool for full detail before reasoning about an object; don't
  assume a list row carries the fields you need.
- **Create/update is one `manage` tool** per resource, distinguished by
  whether you pass an existing id.
- **`403` means permissions, not a bug** — the token lacks the MCP
  permission or the owning module's. Connection and token problems are the
  `connect-mcp-setup` skill's territory (`core` plugin).

## Non-goals

No workflows, no sequencing, no parameter schemas. This skill ends when
you know which domain and tool family to read; the tool descriptions and
the domain skills take it from there.
