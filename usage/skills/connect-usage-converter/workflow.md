# Workflow: Vendor Report → Connect Usage File

This is the detailed playbook the skill follows end-to-end. Each step
references the MCP tool that does the work, with a worked snippet.

Pre-requisite: the MCP client is configured per [`setup.md`](setup.md).

## Step 0 — Gather inputs from the user

You need:

| Input | Source | Notes |
|---|---|---|
| Source file | User attaches or names a path | CSV, XLSX, JSONL. Filename hints at vendor. |
| `vendor` slug | Inferred or asked | `aws-cur` / `microsoft-nce` / `adobe-invoice` / unknown |
| `product_id` | Asked | The Connect product representing the vendor (`PRD-…`). |
| `contract_id` | Asked | The partner's distribution contract (`CRD-…`). |
| `period_from` / `period_to` | Asked or derived from filename | ISO-8601 timestamps bounding the billing month. |
| `currency` | Read from source file | ISO-4217. If the source mixes currencies, plan to split into multiple Usage Files. |

If anything is missing, ask **before** calling any MCP tool — calls fail
loudly without these.

## Step 1 — Fetch the general guide

```
get_conversion_guide()
```

Returns markdown describing Connect's column model, period semantics,
asset/item lookup conventions, and the validate-then-submit cycle. Treat
this as authoritative.

## Step 2 — Fetch the vendor cookbook (if known)

```
get_vendor_cookbook(vendor="aws-cur")          # or microsoft-nce / adobe-invoice
```

Returns the per-vendor column-mapping rules. If the source vendor is
*unknown*, skip this step and fall back to the local `mappings/` quick
references plus the general guide for inference.

## Step 3 — Fetch the target schema

```
describe_product_usage_schema(product_id="PRD-DEMO")
```

Returns the exact column set for the records sheet, plus example row
shape. The required columns are stable across products in v1 (the
response is currently global; will become per-product in the future).

## Step 4 — Map source rows

Convert the source rows into Connect-record-shape dicts following the
cookbook + this skill's `mappings/<vendor>.md`. The result is a list of
dicts like:

```json
[
  {
    "record_id": "7d8f0e2a-4b3c-4e1f-9a2b-1c2d3e4f5a6b",
    "record_note": "aws-554027867388-AmazonEC2-2026051900-0001",
    "item_search_criteria": "item.mpn",
    "item_search_value": "AmazonEC2",
    "quantity": 1,
    "start_time_utc": "2026-05-01 00:00:00",
    "end_time_utc": "2026-05-31 23:59:59",
    "asset_search_criteria": "parameter.account_id",
    "asset_search_value": "554027867388",
    "category_id": "AWS.Amazon Elastic Compute Cloud",
    "amount": 11.7162,
    "tier": 0,
    "item_name": "Amazon Elastic Compute Cloud",
    "item_unit": "Unit",
    "item_mpn": "AmazonEC2",
    "item_precision": "Decimal(8)"
  },
  ...
]
```

(Per-vendor field set varies; the above shows AWS. NCE rows (covering both
seat licenses and Azure consumption under the unified mapping) use
`asset.id` lookup, the triple-based item identity, and include the `v.*`
custom-parameter columns described in the NCE cookbook. Adobe rows use
the existing pre-registered-item pattern.)

Apply vendor-specific filtering and splitting:

- **AWS:** one Usage File per `line_item_usage_account_id`. Drop `Tax`,
  `Credit`, `Refund` rows.
- **NCE (incl. Azure):** resolve `customer_id` → Connect `asset_id`
  *before* emitting records (lookup by `parameter.customer_id` on
  registered assets). Drop rows whose customer doesn't resolve. Apply
  the RI / Savings Plan margin gross-up
  `amount = subtotal / (1 - partner_margin)`; multiply by exchange rate
  if billing currency differs from marketplace currency. Clip
  `start_time_utc` / `end_time_utc` to the file's billing-month bounds.
- **Adobe:** drop `CANCELLATION` rows. Use `Ext Price` (pre-tax invoice
  currency), not `Line Total Amount` or `Extended Price Local`.

## Step 5 — Dry-run validate

```
validate_usage_payload(product_id="PRD-DEMO", rows=<list-of-dicts>)
```

The endpoint accepts at most 1000 rows per call and rejects larger
payloads with HTTP 400. If your source has more than 1000 rows, validate a
representative sample (e.g. the first 1000) — the dry-run only verifies
column shape, so a sample is sufficient to catch header mistakes before
paying for a real upload. The request body is also capped at 5 MB and the
413 gate can fire *before* the row-count gate when individual rows carry
unusually large values (e.g. a single multi-MB string field) — if you see
413, trim per-row content before retrying rather than reducing row count.

The endpoint validates **column shape only** — missing headers, unknown
headers, vendor-required columns. Row-level errors (duplicate ids, unknown
items) only surface during the real upload.

Response:

```json
{
  "valid_count": 1,
  "invalid_count": 0,
  "errors": [],
  "totals": {"rows": 1}
}
```

If `invalid_count > 0`, fix the column issues reported in `errors[]` and
re-run. Don't proceed until this returns `invalid_count = 0`.

## Step 6 — Build the XLSX

Two options, depending on whether your agent can execute Python locally:

### Option A — Python helper

```bash
python scripts/build_usage_xlsx.py \
    --records records.json \
    --categories categories.json \
    --output usage.xlsx
```

`records.json` is the list from Step 4. `categories.json` is optional (an
empty list `[]` is fine). The script writes `records` and `categories`
sheets with the Connect-mandated column layout.

### Option B — Direct binary handling

If your agent has its own XLSX library, generate the file directly. The
records sheet must have these headers in order:

```
record_id, record_note, item_search_criteria, item_search_value, quantity,
start_time_utc, end_time_utc, asset_search_criteria, asset_search_value,
category_id, amount, tier, item_name, item_unit, item_mpn, item_precision
```

The categories sheet (if used) has:

```
category_id, category_name, category_description
```

## Step 7 — Create the draft

```
manage_usage_file(
    name="AWS CUR 2026-05",
    product_id="PRD-DEMO",
    contract_id="CRD-DEMO",
    period_from="2026-05-01T00:00:00Z",
    period_to="2026-05-31T23:59:59Z",
    currency="USD",
    external_id="CUR-554027867388-2026-05",   # optional traceability
    note="Vendor: AWS, account 554027867388"  # optional free text
)
```

Response includes the new `usage_file_id` (`UF-…`). Hold onto it for the
rest of the chain.

## Step 8 — Upload

Base64-encode the XLSX bytes:

```python
import base64
with open("usage.xlsx", "rb") as f:
    b64 = base64.b64encode(f.read()).decode()
```

Then:

```
upload_usage_file(
    usage_file_id="UF-2026-05-XXXX-YYYY",
    file_base64=b64,
    filename="aws-cur-2026-05.xlsx"
)
```

All uploads must be passed inline as base64-encoded content via
`file_base64`. The server enforces a 50 MB decoded-byte cap; a real Connect
Usage File is typically well under 5 MB, so this is generous headroom. If
you ever hit the cap, the file likely has unnecessary sheets or embedded
content that can be stripped before encoding.

## Step 9 — Poll for status

```
get_usage_file(usage_file_id="UF-…")
```

Look at `status`. Possible terminal-for-this-step outcomes:

- `uploaded` → file passed processing, ready to submit. Proceed to step 10.
- `invalid` → row-level errors surfaced. Go to step 9a.

`processing` is transient (polling step). `ready` means the file is still
in draft and the upload didn't take.

### Step 9a — Inspect and fix validation errors

```
get_usage_file_validation_errors(usage_file_id="UF-…", limit=50)
```

The response shape is
`{total, limit, offset, truncated, items: [{column?, code, message, raw_value?}]}`.
The endpoint caps each per-row error source at ~1000 entries; if the file
has more failing rows than that, `truncated: true` signals that the returned
list is a representative sample rather than exhaustive. Don't try to fix
every row in that case — fix the dominant *patterns* and re-upload.

Surface the errors to the user in a readable summary. Common patterns:

- Duplicate `record_id` → check your synthesis logic (positional index
  collisions).
- Unknown item — check that the vendor product code matches a Connect item
  MPN. If the partner hasn't registered the item yet, either skip the row
  or fill `item_name` / `item_mpn` / `item_unit` / `item_precision` for
  dynamic creation.
- Asset lookup failed → the asset's provisioning parameter doesn't carry
  the expected vendor identifier. Confirm the `asset_search_criteria`
  parameter name is right.

Fix in the source rows, rebuild the XLSX, re-upload (Step 8). Repeat until
`status = uploaded`.

## Step 10 — Submit

```
submit_usage_file(usage_file_id="UF-…")
```

Transitions the file to `pending` — the provider sees it now and can
accept or reject. The vendor leg of the workflow is complete.

## Step 11 (provider side, separate session) — Accept / reject

Out of scope for the vendor agent. The provider's agent uses:

- `accept_usage_file(usage_file_id, acceptance_note)` — moves to
  `accepted`, triggers record processing.
- `reject_usage_file(usage_file_id, rejection_note)` — moves to
  `rejected`, surfaces the reason to the vendor for fix-and-resubmit.
- `upload_reconciliation_file(...)` then `close_usage_file(...)` — closes
  the billing cycle.

## Error handling shortcuts

When something goes wrong, the MCP tool returns a structured response with
`success: false` and a `message`. Common cases:

| Symptom | Likely cause | Next step |
|---|---|---|
| `success: false, message: "Usage File … not found"` | Wrong ID, or tenant mismatch | Confirm the ID and the MCP environment |
| `success: false, message: "Access denied …"` | Token's account doesn't match the resource | Switch to a token with the right scope |
| `success: false, message: "Bad request … missing field"` | A required parameter wasn't passed | Re-check the cookbook + this workflow |
| `success: false, message: "Error validating payload: …"` | Network or transport-level issue | Retry once; if persistent, escalate |

## Response envelope reference

Different MCP tools return different response shapes. Knowing which envelope
to expect from which call saves the agent from guess-and-parse loops.

### Write / transition tools

`manage_usage_file`, `upload_usage_file`, `submit_usage_file`,
`accept_usage_file`, `reject_usage_file`, `close_usage_file`,
`delete_usage_file`, `reprocess_usage_file`, `upload_reconciliation_file`,
`close_usage_record`.

```json
{
  "success": true,
  "message": "Usage File created",
  "id": "UF-2026-05-1234-5678"
}
```

On failure: `{"success": false, "message": "<reason>"}` (no `id`).

### List tools

`list_usage_files`, `list_usage_records`.

```json
{
  "limit": 10,
  "offset": 0,
  "total": 42,
  "items": [
    {"id": "UF-…", "name": "May 2026"},
    {"id": "UF-…", "name": "June 2026"}
  ]
}
```

Only `id` and `name` are surfaced per item; call the matching `get_*` tool
to fetch full details.

### Get tools

`get_usage_file`, `get_usage_record`, `get_product_usage_template`,
`describe_product_usage_schema`.

These return the **raw API response** (full resource JSON), not an envelope.
Shape depends on the resource — inspect the response keys directly. On
failure they fall back to `{"success": false, "message": "<reason>"}`.

### Validation-errors tool

`get_usage_file_validation_errors`.

```json
{
  "total": 14,
  "limit": 50,
  "offset": 0,
  "truncated": false,
  "items": [
    {
      "column": "item_search_value",
      "code": "USG_011",
      "message": "Unknown MPN",
      "raw_value": "AmazonEKS"
    }
  ]
}
```

`truncated: true` means at least one underlying error source hit the
1000-per-source cap; treat the returned `items` as a representative sample
and re-upload after fixing the dominant failure patterns.

### Conversion-preflight tool

`validate_usage_payload`.

```json
{
  "valid_count": 1,
  "invalid_count": 0,
  "errors": [],
  "totals": {"rows": 1}
}
```

`errors[]` lists column-shape problems (missing required headers, unknown
headers). `invalid_count == 0` means safe to proceed to draft creation.

### Guide tools

`get_conversion_guide`, `get_vendor_cookbook`.

```json
{
  "content_type": "text/markdown",
  "vendor": "aws-cur",
  "body": "# AWS Cost & Usage Report → Connect Usage\n\n..."
}
```

`vendor` is present only on `get_vendor_cookbook`. On failure both fall back
to the standard `{"success": false, "message": "<reason>"}` envelope.
