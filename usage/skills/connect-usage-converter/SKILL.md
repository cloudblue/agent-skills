---
name: connect-usage-converter
description: Use when the user wants to convert a vendor billing or usage report (AWS Cost & Usage Report, Microsoft NCE / Azure billing data, Adobe VIP invoice, or any other tabular usage source) into a CloudBlue Connect Usage File and submit it through the Usage MCP server. Triggers on requests like "upload our AWS bill to Connect", "convert this NCE CSV", "convert this Azure billing file", "submit Adobe usage", "create a Connect usage report from this spreadsheet", or "validate this usage file before submission".
version: 0.1.0
---

# Connect Usage Converter

You are converting a vendor billing/usage source (CSV, XLSX, JSON) into a
CloudBlue Connect **Usage File** and submitting it through the
**Usage MCP server**. The MCP server lives at the customer's Connect tenant
(see `setup.md` for client configuration); for the vendor flow this skill
covers schema introspection, dry-run validation, draft creation, upload,
and submission. Acceptance and reconciliation are the provider's actions
on the other side and are out of scope for the vendor agent.

This skill bundles the workflow, vendor-format mappings, example inputs, a
canonical "good" output, and one Python helper for assembling the final
XLSX. The authoritative cookbooks live on the MCP server and are fetched at
runtime via the `get_conversion_guide` and `get_vendor_cookbook` tools — the
local mapping files in this skill are quick references, not the source of
truth.

## When to use

Trigger on any of these intents:

- "Convert this AWS / Microsoft NCE / Azure / Adobe billing file to Connect"
- "Upload usage to Connect for product PRD-…"
- "Reconcile last month's NCE / Azure invoice with Connect"
- "Validate this usage spreadsheet before submission"
- "Fix the validation errors on Usage File UF-…"

If the user just wants to *read* existing usage data without converting,
that's covered by the MCP tools directly (`list_usage_files`,
`get_usage_file`, `list_usage_records`) — you don't need this skill.

## High-level workflow

1. **Confirm the source format.** Ask if not obvious from filenames. The
   first-class vendors are `aws-cur`, `microsoft-nce` (covers both seat
   licenses like M365 / Exchange **and** Azure consumption — one unified
   mapping), and `adobe-invoice`. Unknown sources are still supported
   via the general conversion guide.
2. **Confirm the target.** Need: `product_id` (the Connect product
   representing the vendor), `contract_id` (the distribution contract),
   and the billing `period_from` / `period_to`. Ask the user for any
   missing piece.
3. **Fetch authoritative guidance.** Call `get_conversion_guide()` always,
   and `get_vendor_cookbook(vendor)` for known vendors. Don't skip — the
   server-side content is more up-to-date than this skill's local copies.
4. **Fetch the target schema.** Call `describe_product_usage_schema(product_id)`
   to learn the exact column set the product expects.
5. **Map source rows to Connect rows** following the cookbook + local
   `mappings/<vendor>.md`. **For NCE (including Azure) this includes a
   mandatory pre-step:** resolve each row's `customer_id` (Microsoft
   tenant ID) → Connect `asset_id` by looking up assets whose
   `parameter.customer_id` matches; drop rows where the customer doesn't
   resolve. Filter / drop / split per the vendor's rules (e.g. AWS: one
   file per `line_item_usage_account_id`, drop `Tax`/`Credit`/`Refund`;
   NCE: apply RI/SP margin gross-up on `amount`; Adobe: drop
   `CANCELLATION`).
6. **Dry-run validate** with `validate_usage_payload(product_id, rows=…)`.
   This checks column shape only. Fix any header / required-column issues
   before going further.
7. **Build the XLSX.** Either populate the product template downloaded via
   `get_product_usage_template` (it already has the right sheet/header
   layout), or use `scripts/build_usage_xlsx.py` to assemble a fresh
   workbook from a JSON row list. Either way, the result is an XLSX with a
   `records` sheet and optional `categories` sheet.
8. **Create the draft.** Call `manage_usage_file(...)` with name, product,
   contract, period, currency.
9. **Upload.** Call `upload_usage_file(usage_file_id, file_base64=…)`.
10. **Poll status.** Call `get_usage_file(usage_file_id)`. Possible outcomes:
    - `uploaded` → ready to submit.
    - `invalid` → call `get_usage_file_validation_errors(usage_file_id)`,
      surface them to the user with context, fix, re-upload.
11. **Submit.** Call `submit_usage_file(usage_file_id)`. The vendor leg of
    the workflow ends here; provider acceptance is a separate user action.

## Where to look next

- [`setup.md`](setup.md) — how to configure your MCP client to reach the
  Connect tenant. Read **once**, before the first usage of the skill.
- [`workflow.md`](workflow.md) — the detailed playbook expanding step 1–11
  above, with worked tool-call examples.
- [`mappings/aws-cur.md`](mappings/aws-cur.md),
  [`mappings/microsoft-nce.md`](mappings/microsoft-nce.md),
  [`mappings/adobe-invoice.md`](mappings/adobe-invoice.md) — quick-reference
  field-mapping tables per vendor.
- [`examples/inputs/`](examples/inputs/) — synthetic sample reports for each
  vendor. Use these to ground your understanding of source shape.
- [`examples/outputs/connect-usage-sample.xlsx`](examples/outputs/connect-usage-sample.xlsx)
  — a canonical "good" Connect Usage File. Read this to ground your
  understanding of the target shape.
- [`scripts/build_usage_xlsx.py`](scripts/build_usage_xlsx.py) — Python
  helper for assembling the records/categories sheets from a JSON row list.

## Key principles

- **Pre-tax, single-currency.** Connect doesn't model tax or FX. Pick the
  pre-tax amount column in the invoice currency every time; split files by
  currency if the source mixes them.
- **No negative rows.** Cancellations, credits, refunds belong in the
  *reconciliation* channel (`upload_reconciliation_file`), not the primary
  submission.
- **Per-row time window.** `start_time_utc` / `end_time_utc` describe the
  exact consumption window for that one record. The Usage File's
  `period_from`/`period_to` is the *envelope* (the billing month).
- **Item lookup is always by MPN.** The vendor's product/SKU code (or a
  composite identity like NCE's `{product_id}:{sku_id}:{availability_id}`)
  is mapped to the Connect item's MPN.
- **Asset lookup varies by vendor.** AWS / Adobe rows use parameter-based
  lookup (`parameter.account_id` / `parameter.subscription_id`). NCE rows
  require a pre-step: the agent resolves `customer_id` → Connect
  `asset_id` first, then writes `asset_search_criteria = "asset.id"`
  with the resolved id. The exact parameter name is the partner's
  choice — ask if uncertain.
- **Always dry-run before uploading.** `validate_usage_payload` is cheap
  and catches column-shape mistakes before they cost a full upload cycle.
