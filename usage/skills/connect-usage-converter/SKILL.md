---
name: connect-usage-converter
description: Use when the user wants to convert a vendor billing or usage report (AWS Cost & Usage Report, Microsoft NCE / Azure billing data, Adobe VIP invoice, or any other tabular usage source) into a CloudBlue Connect Usage File and submit it through the Connect MCP server. Triggers on "upload our AWS bill to Connect", "convert this NCE CSV", "create a Connect usage report from this spreadsheet", or "validate this usage file before submission".
version: 0.1.0
license: Apache-2.0
metadata:
  hermes:
    tags: [CloudBlue, Connect, Usage, Billing, MCP]
    category: productivity
    related_skills: [connect-navigator, connect-mcp-setup]
---

# Connect Usage Converter

You are converting a vendor billing/usage source (CSV, XLSX, JSON) into a CloudBlue Connect **Usage File** and submitting it through the Connect MCP endpoint. This is the **vendor** leg: schema introspection, mapping, dry-run validation, draft creation, upload, submission. Acceptance and reconciliation are the provider's actions from the provider's account.

This skill bundles the workflow, vendor-format mappings, example inputs, a canonical "good" output, and one Python helper for assembling the final XLSX. The authoritative cookbooks live on the MCP server and are fetched at runtime via the guide tools — the local mapping files here are quick references, not the source of truth.

The `usage` domain's tools carry the `usage_` prefix like every other domain (`usage_get_file`, `usage_manage_file`). Read their descriptions once per session for the exact arguments; the catalog is the source of truth for those, per `connect-navigator`.

## Autonomy

The rungs are `connect-navigator`'s (free / announce / gated). Where this skill's actions sit:

| Action | Rung |
|---|---|
| Fetch guides, cookbooks, schemas and templates; list or get usage files and records | **free** |
| Dry-run validate a payload you assembled | **free** — nothing is stored |
| Create the draft usage file; upload the workbook into it | **announce** — the draft is yours alone until it is submitted |
| **Submit** the usage file | **gated** |

Submitting is **outward-facing**: the provider sees the file, and the records it accepts drive what the customer is billed. Before submitting, state the usage file id, the product and contract, the billing period, the row count, and the total amount per currency — then wait for a yes. "Convert this AWS bill" authorises everything up to the upload; it does not authorise the submit.

A rejection is not a rollback. The provider has already seen the file and the fix is another submission, which is why the gate is the only cheap place to catch a bad file.

## The required order

```
1. source + target      vendor format; product_id, contract_id, period
2. authoritative guides  the general conversion guide + the vendor cookbook
3. target schema         the column set this product expects
4. map rows              vendor rows → Connect rows
5. dry-run validate      column shape, before anything is stored
6. build the workbook    `records` sheet, optional `categories` sheet
7. draft → upload        ANNOUNCE
8. submit                GATED — outward-facing
```

The worked calls, their arguments and the response envelopes are in [`workflow.md`](workflow.md), which owns the call order. What this list owns is why the edges exist:

- **Guides before mapping.** The server-side cookbooks are more current than the local `mappings/`. A mapping built from the local copy alone is a mapping you may have to redo.
- **Schema before mapping.** The expected column set is per product, so it is read from the product, never assumed from another vendor's file.
- **Dry-run before upload.** Validation of the payload is cheap and catches column-shape mistakes before they cost a full upload cycle.
- **Everything before submit.** Step 8 is the one step that reaches the provider. Anything you skipped surfaces there, on their side.

## Where to look next

- [`setup.md`](setup.md) — reaching the Connect tenant. Read once, before the first use of this skill.
- [`workflow.md`](workflow.md) — the detailed playbook behind the phases above, with worked tool-call examples and the provider-side steps that follow.
- [`mappings/aws-cur.md`](mappings/aws-cur.md), [`mappings/microsoft-nce.md`](mappings/microsoft-nce.md) (covers both seat licences like M365 / Exchange **and** Azure consumption — one unified mapping), [`mappings/adobe-invoice.md`](mappings/adobe-invoice.md) — quick-reference field-mapping tables. These three are the first-class vendors; any other tabular source is still supported via the general conversion guide.
- [`examples/inputs/`](examples/inputs/) — synthetic sample reports per vendor, to ground your understanding of source shape.
- [`examples/outputs/connect-usage-sample.xlsx`](examples/outputs/connect-usage-sample.xlsx) — a canonical "good" Connect Usage File: the target shape.
- [`scripts/build_usage_xlsx.py`](scripts/build_usage_xlsx.py) — assembles the records/categories sheets from a JSON row list.

## Key principles

- **Pre-tax, single-currency.** Connect models neither tax nor FX. Pick the pre-tax amount column in the invoice currency every time; split files by currency if the source mixes them.
- **Positive rows only.** Cancellations, credits and refunds belong in the *reconciliation* channel, not the primary submission. A negative row in a submission is a row the provider will reject.
- **Per-row time window.** `start_time_utc` / `end_time_utc` describe the consumption window of that one record. The usage file's `period_from`/`period_to` is the *envelope* — the billing month.
- **Item lookup is always by MPN.** The vendor's product/SKU code (or a composite identity like NCE's `{product_id}:{sku_id}:{availability_id}`) maps to the Connect item's MPN.
- **Asset lookup varies by vendor.** AWS and Adobe rows use parameter-based lookup (`parameter.account_id` / `parameter.subscription_id`). NCE rows need a pre-step: resolve each row's `customer_id` (the Microsoft tenant id) to a Connect `asset_id` by matching assets on `parameter.customer_id`, then write `asset_search_criteria = "asset.id"` with the resolved id, and drop the rows that do not resolve. The exact parameter name is the partner's choice — ask if uncertain.
- **Unresolved rows are the interesting output.** Report the rows you dropped and why, prominently. A silently short file bills the customer for less than they used, and nothing downstream notices.
- **Filter per the vendor's rules before validating.** AWS: one file per `line_item_usage_account_id`, drop `Tax` / `Credit` / `Refund`. NCE: apply the RI/SP margin gross-up on `amount`. Adobe: drop `CANCELLATION`. The cookbook is authoritative for each.
