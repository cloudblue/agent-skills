# Microsoft NCE → Connect Usage File — Field Mapping

> **Quick reference.** The authoritative version lives on the Connect MCP server — call `get_vendor_cookbook(vendor="microsoft-nce")` for the up-to-date copy. Use this file for at-a-glance lookups while reasoning about a conversion.
>
> NCE is the unified Microsoft CSP / Partner Center billing format. It covers **both** seat-based licenses (M365, Exchange Online) **and** Azure consumption (including Reservation Instances and Savings Plans). The mapping is uniform regardless of row type — RI / Savings Plan rows only differ in that they trigger a margin gross-up on `amount` (see edge cases).

NCE records use **`asset.id` lookup** (the agent must resolve `customer_id` → Connect `asset_id` before emitting records) and a **structured item identity** `{product_id}:{sku_id}:{availability_id}` shared across `category_id`, `item_search_value`, and `item_mpn`. All records are emitted as **dynamic items**.

> **Column-name case:** the source-column references below use `lowercase_with_underscore`. The actual Partner Center exports often use `CamelCase` (`CustomerId`, `ProductId`, `Subtotal`, `ChargeStartDate`, …). Treat header matching as case-insensitive after stripping underscores.

| Connect destination | NCE source (or derivation) |
|---|---|
| **Records sheet** | |
| `asset_search_criteria` | literal `"asset.id"` |
| `asset_search_value` | resolved Connect `asset_id` (lookup: `parameter.customer_id == row.customer_id`) |
| `item_search_criteria` | literal `"item.mpn"` |
| `item_search_value` | `{product_id}:{sku_id}:{availability_id}` |
| `quantity` | literal `1` |
| `amount` | `subtotal / (1 - partner_margin)` — multiply by exchange rate if billing-currency ≠ marketplace-currency. `partner_margin = 0` unless the row is RI / Savings Plan. |
| `start_time_utc` | `charge_start_date`, **clipped** to the file's `period_from` if earlier |
| `end_time_utc` | `charge_end_date`, **clipped** to the file's `period_to` if later |
| `category_id` | `{product_id}:{sku_id}:{availability_id}` |
| `item_name` | `{product_id}:{sku_id}:{availability_id} {sku_name}` |
| `item_unit` | literal `"unit"` |
| `item_mpn` | `{product_id}:{sku_id}:{availability_id}` |
| `record_note` | `# {reservation_order_id} {sku_name} - from {charge_start_date} through {charge_end_date}` |
| `tier` | not used in the NCE flow |
| `item_precision` | not used in the NCE flow |
| **Record-level custom parameters** (additional `v.*` columns) | |
| `v.invoice_number` | `invoice_number` |
| `v.reseller_mpn` | `reseller_mpn_id` |
| `v.customer_id` | `customer_id` |
| `v.partner_margin` | partner-configured margin for RI / Savings Plan rows, else `0` |
| `v.ri_margin` | usually `0` |
| `v.from_exchange_rate` | exchange rate applied when billing-currency ≠ marketplace-currency, else `1` |
| `v.to_exchange_rate` | marketplace currency rate (target) |
| **Categories sheet** | |
| `category_id` | `{product_id}:{sku_id}:{availability_id}` (one row per distinct triple in records) |
| `category_name` | `sku_name` |
| `category_description` | optional — e.g. `"Microsoft {sku_name}"` |
| **Usage File header** (`manage_usage_file` parameters) | |
| `name` | caller's choice, e.g. `"Microsoft NCE {invoice_number}"` |
| `product_id` | caller-supplied (the Connect product representing NCE) |
| `contract_id` | caller-supplied (partner's distribution contract) |
| `period_from` | start of the billing month |
| `period_to` | end of the billing month |
| `currency` | the marketplace currency (NOT the billing currency, if they differ) |
| `external_id` | optional — `invoice_number` for traceability |

## Pre-step — asset correlation

Before emitting any record, look up the Connect asset whose
`customer_id` parameter matches the row's `customer_id` (Microsoft tenant
ID). The result is the Connect `asset_id` used as `asset_search_value`.
Cache the lookup across rows — many NCE rows share one customer.

If a customer doesn't resolve, **drop the row** and surface the unresolved
`customer_id` to the operator.

## Detecting RI / Savings Plan rows

Use both `term_and_billing_cycle` and `subscription_description` — look for
"Reservation" / "Savings Plan" markers or a non-empty `reservation_order_id`.
For these rows:
- Set `v.partner_margin` to the partner-configured margin (read from product config).
- The `amount` gross-up formula `subtotal / (1 - partner_margin)` then reflects the partner's commercial markup.

## NCE columns that don't write to any Connect field

- `tax`, `taxtotal`, `total` — tax handling is the provider's billing system's concern.
- `unitprice`, `effectiveunitprice` — Connect derives unit price from `amount / quantity` when needed; quantity is always `1` here.
- `subscription_description`, `term_and_billing_cycle` — used as RI/SP *filters* only, not written.
- `tier1mpnid` / `tier2mpnid` etc. — partner-program metadata not surfaced on records.
- `microsoft_domain` — kept on the Connect asset registry (not on the record).
