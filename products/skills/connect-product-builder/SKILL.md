---
name: connect-product-builder
description: Use when a vendor is building or extending a product in CloudBlue Connect through the products MCP tools — creating the product, adding items with their MPN / unit / billing period, designing ordering, fulfillment and configuration parameters, writing activation templates, and publishing a product version. Triggers on "create a Connect product", "add items to PRD-1234", "which parameter phase should the tenant ID be", "create an activation template", "publish the product version", or "why can't I publish this product".
version: 0.1.0
license: Apache-2.0
metadata:
  hermes:
    tags: [CloudBlue, Connect, Products, Catalog, MCP]
    category: productivity
    related_skills: [connect-navigator, connect-mcp-setup]
---

# Connect Product Builder

You are building a vendor product in CloudBlue Connect end to end using the `products` domain of the Connect MCP catalog. The domain has ~13 tools and no single call builds a product: the work is a **five-phase sequence with real ordering constraints**, plus one taxonomy decision — which *phase* each parameter belongs to — that is where most people get stuck.

This skill owns the order and the taxonomy. It does not restate parameter schemas: read the tool descriptions in the live catalog for exact argument names before each call.

**This skill mutates the tenant.** Every phase below except the pre-flight read creates or updates real product data under the vendor account behind the token. Phase 5 (publish) is irreversible for that version and is gated on explicit human confirmation.

## Autonomy

Once the human has given you the product content — names, the item list, the parameters the buyer must supply — you run the whole sequence yourself, including recovering from validation errors. You never invent the content.

On `connect-navigator`'s rungs: phases 1–4 are **announce** work — they build product data nobody outside the vendor account can see, so do it and report it. Publishing is **gated**, because a published version is what the downstream domains build against.

**Decisions you never make alone:**

| Decision | Why it is the human's |
|---|---|
| Product name, description, category | Commercial and brand-facing |
| Which items exist, and their MPNs | The MPN is the vendor's own SKU identity; guessing it breaks usage reporting and price lists downstream |
| An item's unit and billing period | Determines whether the item is quantity-based or usage-reported, and it is effectively frozen once subscriptions exist |
| Which questions the buyer is asked at ordering time | Every ordering parameter is friction on the purchase form; the vendor decides what is worth asking |
| Whether a parameter is required | A required ordering parameter blocks purchase until answered |
| Template wording | Partner-facing copy |
| **Publishing a version** | Point of no return — see Phase 5 |

If any of these is missing, ask before calling a mutating tool. Ask for all of them in one round, not one at a time.

## The required order

```
1. product shell   → products_manage
2. items           → the products item family        (MPN, unit, period)
3. parameters      → the products parameter family   (phase taxonomy below)
4. templates       → the products template family
5. cut the version → products_create_version         (GATED, irreversible)
```

The order is not a style preference. Each edge exists because the next phase needs an id or a value the previous one produces:

- **Shell before everything** — items, parameters and templates are all created *under* a product id (`PRD-…`). There is nothing to attach them to first.
- **Items before parameters** — configuration-phase parameters can be scoped to a specific item, and item-scoped parameters cannot reference an item that does not exist yet.
- **Parameters before templates** — templates interpolate parameter values (the activation message shows the buyer the login URL your fulfillment parameter carries). A template written against a parameter id that does not exist renders empty at fulfillment time, and nothing warns you.
- **Everything before publish** — publishing freezes the version. Anything you forgot becomes work on a *new* version, not an edit to this one.

Only the tool names quoted above are used verbatim. The item, parameter, template and read families are resolved from the catalog — see `connect-navigator`, Shared conventions.

## The parameter phase taxonomy

This is the decision the skill exists for. Every product parameter belongs to exactly one phase, and the phase decides **who fills it, when, and whether it is per-subscription or per-marketplace**.

| Phase | Who fills it | When | Scope | Typical content |
|---|---|---|---|---|
| **Ordering** | The buyer (customer / reseller) | On the purchase or change form, before the request reaches the vendor | Per subscription | Domain name, admin email, region choice, seat count qualifier, accepted terms |
| **Fulfillment** | The vendor (you, or the vendor's system) while processing the request | After the request arrives, before it is approved | Per subscription | Provisioned tenant id, login URL, generated credentials, external system reference |
| **Configuration** | The vendor, in the product itself | At product setup time — not per order | Per marketplace, item and/or tier — **not** per subscription | Distributor-specific API endpoint, per-marketplace SKU mapping, regional service URL |

### Choosing the phase

Ask, in this order:

1. **Does the value differ per subscription?** No → **Configuration**. This is the phase people forget exists, and it is the right answer for anything that varies by marketplace or reseller rather than by buyer.
2. **Does the vendor need it from the buyer to provision?** Yes → **Ordering**. If you cannot fulfill without the answer, mark it required; if you can fulfill with a default, do not.
3. **Does the vendor produce it during provisioning?** Yes → **Fulfillment**.

### Consequences to state to the human before you create parameters

- **A parameter's phase is not something to change casually.** Treat the phase as fixed at creation: existing subscriptions carry values keyed on the parameter as originally defined. If a phase turns out wrong, expect to create a new parameter rather than repurpose the old one. Confirm the update semantics against the parameter tool's own description before promising an in-place change.
- **Ordering parameters are what makes an inquiry possible.** When a fulfillment request is later sent back to the buyer for correction (`inquire`, in the `fulfillments` plugin's territory), what the buyer is asked to fix is an *ordering* parameter. A product whose missing data lives only in fulfillment parameters gives the vendor no way to ask the buyer for it. If the human describes a "we need to go back to the customer" case, that data belongs in Ordering.
- **Fulfillment parameters are the vendor's answer channel.** They are what the activation template renders and what the buyer sees after approval.
- **The parameter id is a contract.** It is the key used in requests, subscriptions and usage reporting. Pick it once, in lower_snake_case, and do not churn it.
- **Required + hidden is a trap.** A required parameter the buyer cannot see cannot be answered. Check both flags together.

## Phase 5 — publish is gated

`products_create_version` is the point of no return. It cuts a version from the draft master *and* publishes it in the same call — there is no separate publish step to change your mind at. (`products_publish_version` is a different tool: it takes an existing version number and moves it between public / private / staging. It cannot create the version you are about to cut, and calling it for a version that does not exist yet answers `404`.)

Before calling it:

1. Run the pre-publish checklist in [`workflow.md`](workflow.md#pre-publish-checklist).
2. Summarize to the human, in one message: the product id, the item count with their MPNs and units, the parameter list grouped by phase, the templates, and what publishing means (this version becomes immutable; further changes require a new version).
3. **Wait for explicit confirmation.** Do not publish because the user said "build the product" — building and publishing are separate consents.

If the user has not asked to publish, stop after Phase 4 and report the product as ready-to-publish. That is a complete, successful outcome.

## Where to look next

- [`workflow.md`](workflow.md) — the per-phase playbook: what to gather, what each phase actually creates, the pre-publish checklist, what is immutable after publish, and the failure table.
- `connect-navigator` (`core` plugin) — which domain owns a noun, VerboseID prefixes, the shared list/filter/pagination conventions these tools follow, and the free/announce/gated rungs.
- `connect-mcp-setup` (`core` plugin) — any `403`. This work needs the **Products** module permission on a vendor account; diagnosing the token is that skill's job.

## Non-goals

- **No pricing.** Price lists, versions, price points and rate cards belong to the `pricing` plugin. An item's *existence* is this skill's job; what it costs is not. Do not let a request for "add the price" pull you into the pricing domain — hand it over.
- **No listings or marketplaces.** Publishing a product version is not publishing it to a marketplace. Listing requests, marketplace selection and the vendor → distributor approval flow belong to the `listings` plugin.
- **No fulfillment processing.** Designing the parameters is here; approving, inquiring or failing actual requests is the `fulfillments` plugin's.
- **No usage reporting.** Converting and submitting usage files is the `usage` plugin's. This skill only ensures items exist with the MPNs that usage rows will match on.
- **No product deletion or teardown.** If the user wants a product removed, say what it would take and let them do it deliberately; this skill does not reach for destructive tools.
