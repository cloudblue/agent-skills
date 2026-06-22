#!/usr/bin/env python3
"""Assemble a CloudBlue Connect Usage File XLSX from JSON inputs.

The MCP tool `upload_usage_file` expects a properly-shaped workbook with
two sheets — `records` (mandatory) and `categories` (optional). Writing
that workbook by hand from an LLM is fragile; this script does it
deterministically.

Usage:
    python build_usage_xlsx.py \\
        --records records.json \\
        [--categories categories.json] \\
        --output usage.xlsx

records.json is a list of dicts; each dict's keys are the Connect column
names (record_id, item_search_criteria, item_search_value, quantity, ...).
Missing optional columns are emitted as empty cells; required columns
must be present (see RECORD_HEADERS_REQUIRED below).

Any dict keys that start with `v.` are treated as vendor custom usage
parameters (e.g. Microsoft NCE rows carry `v.invoice_number`,
`v.customer_id`, etc.). They appear as additional columns in the records
sheet, in the order they were first encountered across the input rows.

categories.json (optional) is a list of {category_id, category_name,
category_description} dicts.

Dependencies: openpyxl (`pip install openpyxl`).
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

try:
    from openpyxl import Workbook
except ImportError:
    sys.stderr.write(
        "openpyxl is required. Install with: pip install openpyxl\n",
    )
    sys.exit(2)


# Column order matches Connect's FIXED_HEADERS. Keep in sync with the
# response of describe_product_usage_schema(product_id).
RECORD_HEADERS = [
    "record_id",
    "record_note",
    "item_search_criteria",
    "item_search_value",
    "quantity",
    "start_time_utc",
    "end_time_utc",
    "asset_search_criteria",
    "asset_search_value",
    "category_id",
    "amount",
    "tier",
    "item_name",
    "item_unit",
    "item_mpn",
    "item_precision",
]

RECORD_HEADERS_REQUIRED = {
    "record_id",
    "item_search_criteria",
    "item_search_value",
    "quantity",
    "start_time_utc",
    "end_time_utc",
    "asset_search_criteria",
    "asset_search_value",
}

CATEGORY_HEADERS = [
    "category_id",
    "category_name",
    "category_description",
]


def build(records, categories=None):
    # Collect vendor-custom `v.*` parameter columns in first-seen order.
    custom_headers = []
    seen_custom = set()
    for row in records or []:
        for k in row.keys():
            if k.startswith("v.") and k not in seen_custom:
                custom_headers.append(k)
                seen_custom.add(k)

    headers = RECORD_HEADERS + custom_headers

    wb = Workbook()
    records_sheet = wb.active
    records_sheet.title = "records"
    records_sheet.append(headers)
    for i, row in enumerate(records or [], start=1):
        missing = RECORD_HEADERS_REQUIRED - row.keys()
        if missing:
            raise ValueError(
                f"records[{i - 1}] missing required column(s): {sorted(missing)}",
            )
        records_sheet.append([row.get(h, "") for h in headers])

    categories_sheet = wb.create_sheet("categories")
    categories_sheet.append(CATEGORY_HEADERS)
    for row in categories or []:
        categories_sheet.append([row.get(h, "") for h in CATEGORY_HEADERS])

    return wb


def main():
    parser = argparse.ArgumentParser(
        description="Build a Connect Usage File XLSX from JSON inputs.",
    )
    parser.add_argument(
        "--records",
        required=True,
        type=Path,
        help="Path to JSON file with a list of record dicts.",
    )
    parser.add_argument(
        "--categories",
        type=Path,
        help="Optional path to JSON file with a list of category dicts.",
    )
    parser.add_argument(
        "--output",
        required=True,
        type=Path,
        help="Output XLSX path.",
    )
    args = parser.parse_args()

    records = json.loads(args.records.read_text(encoding="utf-8"))
    if not isinstance(records, list):
        sys.stderr.write("records.json must contain a JSON list\n")
        sys.exit(1)

    categories = None
    if args.categories:
        categories = json.loads(args.categories.read_text(encoding="utf-8"))
        if not isinstance(categories, list):
            sys.stderr.write("categories.json must contain a JSON list\n")
            sys.exit(1)

    try:
        wb = build(records, categories)
    except ValueError as exc:
        sys.stderr.write(f"Build failed: {exc}\n")
        sys.exit(1)

    wb.save(args.output)
    print(f"Wrote {len(records)} record(s) → {args.output}")


if __name__ == "__main__":
    main()
