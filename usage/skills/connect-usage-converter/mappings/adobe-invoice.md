# Adobe VIP Invoice → Connect Usage File — Field Mapping

> **Quick reference.** The authoritative version lives on the Connect MCP server — call `get_vendor_cookbook(vendor="adobe-invoice")` for the up-to-date copy. Use this file for at-a-glance lookups while reasoning about a conversion.

Source: the `Line Items` sheet of the Adobe VIP XLSX. The `Summary` sheet
contributes a few invoice-level fields to the parent Usage File header.

| Connect destination | Adobe source (or derivation) |
|---|---|
| **Records sheet** | |
| `record_id` | derived: `{Order Number}-{Line Item}` |
| `record_note` | `Charge Type` + `Market Segment` (concatenated; optionally append `Billing Cycle` or `Order Reason`) |
| `item_search_criteria` | literal `"item.mpn"` |
| `item_search_value` | `SKU` |
| `quantity` | `Quantity` (integer) |
| `start_time_utc` | `Charge Start Date` + ` 00:00:00` (Adobe ships date-only) |
| `end_time_utc` | `Charge End Date` + ` 00:00:00` |
| `asset_search_criteria` | literal `"parameter.subscription_id"` |
| `asset_search_value` | `Subscription ID` |
| `amount` | `Ext Price` (pre-tax, invoice currency — **not** `Line Total Amount`, **not** `Extended Price Local`) |
| `item_name` | `Product Description` (only when the item is dynamic) |
| `category_id` | — (not filled in the Adobe flow) |
| `tier` | — (not filled) |
| `item_unit` | — (not filled) |
| `item_mpn` | — (not filled) |
| `item_precision` | — (not filled) |
| **Usage File header** (`manage_usage_file` parameters) | |
| `name` | caller's choice, e.g. `"Adobe VIP {Invoice Number}"` |
| `product_id` | caller-supplied (the Connect product representing Adobe VIP) |
| `contract_id` | caller-supplied (partner's distribution contract) |
| `period_from` | derived from `min(Charge Start Date)` across rows (or invoice month if simpler) |
| `period_to` | derived from `max(Charge End Date)` across rows (or invoice month) |
| `currency` | `Currency` (Line Items sheet) — **not** `Local Currency` |
| `external_id` | `Invoice Number` (from the Summary sheet) |
| `note` / `description` | optional; `Comments` is a reasonable source |

## Adobe columns that don't write to any Connect field

**Filter-only (not written, used to decide whether to include the row):**

- `Charge Type` — drop `CANCELLATION` rows (Adobe encodes cancellations as *positive* quantity/amount with this label; treat them via reconciliation instead). Keep `NEW` / `RENEWAL` / `COTERM`. Still copied into `record_note` for kept rows.

**Buyer / reseller / shipping metadata (irrelevant per-row):**

- All `Sold To *` columns (Company ID, Name, Address, City, State, Postal Code, Country).
- All `Bill To *` columns.
- All `Ship To *` columns.
- `Reseller ID`, `Reseller Name`, `Reseller State`, `Reseller Country`.

**Alternate columns we don't pick (we use the one above instead):**

- `Product Price` — per-unit price; Connect derives unit price from `amount / quantity` when needed.
- `Line Total Amount` — post-tax; Connect doesn't carry tax.
- `Tax (Y/N)`, `Tax Rate`, `Taxes`, `Tax Total`, `Tax Total` — tax columns Connect ignores.
- `Local Currency`, `Extended Price Local`, `Taxes Local Currency`, `Invoice Total Local`, `Exchange Rate`, `Exchange Date` — pre-applied FX conversions Connect doesn't want.
- `Extended Price` — duplicate of `Ext Price` in many exports.
- `Sub Total`, `Grand Total`, `Invoice Total Amount`, `Taxes 2` — invoice-level aggregates, not per-row.

**Context-only (not mapped per-row, could optionally append to `record_note` or file `note`):**

- `External Reference` — alternative order reference.
- `Order Date` — order placement timestamp (not the charge window).
- `Billing Cycle` (`ANNUAL` / `MONTHLY`) — context.
- `Order Reason` — context.
- `Comments` — free text; consider as the file `note`.

**Used only at the file-header level (from the Summary sheet):**

- `Invoice Date` — informational, can drive `period_from`/`period_to` if charge dates are missing.
