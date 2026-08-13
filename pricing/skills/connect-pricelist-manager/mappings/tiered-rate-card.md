# Tiered Vendor Rate Card → Connect Price Points

> **Quick reference.** The authoritative target schema is a real price
> point read from the draft version you are editing (workflow step 3). If
> the points you read carry no tier fields, this price list does not model
> tiers — see [Collapsing to one price](#collapsing-to-one-price) before
> importing anything.

The harder shape: **several rows per SKU**, differing by volume break, by
sales tier, or both. Example:
[`../examples/inputs/vendor-rate-card-tiered.csv`](../examples/inputs/vendor-rate-card-tiered.csv).

```
Part Number,Tier,Min Quantity,Max Quantity,Currency,Partner Cost,MSRP
ACME-PRO-M,T1,1,49,USD,12.00,18.00
ACME-PRO-M,T1,50,249,USD,11.40,17.10
ACME-PRO-M,T2,1,49,USD,11.00,16.50
```

Two different axes hide in one file, and they map differently:

| Vendor axis | Meaning | Connect side |
|---|---|---|
| `Min Quantity` / `Max Quantity` | volume break — the price depends on how many units are bought | Only importable if the point carries volume/quantity-break fields. Otherwise see below. |
| `Tier` (`T1` / `T2`, or "reseller" / "customer") | *who* is buying — position in the sales hierarchy | Maps to the point's tier-level attributes, if the list models them. `T1` is closest to the end customer. |

## Before you map anything

1. Read one point (workflow step 3) and establish **which of the two axes
   this price list actually models**. Many lists model neither and carry a
   single cost plus a single sale price.
2. Confirm with the user which axis their card is expressing. `T1`/`T2` in a
   vendor file and `T1`/`T2` in Connect are not automatically the same
   thing — vendor tier labels are the vendor's naming, and mapping them is
   a decision, not a lookup.
3. Only then build the column mapping.

Getting this wrong writes a volume-break price into a tier field, which
looks plausible and charges the wrong partners the wrong amount. It is the
one mapping error in this domain that a diff summary will not make obvious.

## Collapsing to one price

If the price list models a single price per item and the card is tiered, the
extra rows cannot be imported. Pick one row per SKU, and make the human pick
the rule:

- the **first/base band** (`Min Quantity = 1`) — the usual choice;
- the band matching the partner's actual committed volume;
- the tier the price list is for (a T2-facing list takes the T2 rows).

State the rule you used in the diff summary. Never average bands, and never
silently take the lowest price — that is a commercial decision wearing the
costume of a default.

## Rows that must not become updates

Everything in
[`flat-rate-card.md`](flat-rate-card.md#rows-that-must-not-become-updates)
applies, plus:

- **Overlapping or gapped bands** (`1–49` then `60–249`) — the card is
  malformed. Report it; do not interpolate.
- **Open-ended top band** with an empty `Max Quantity` — fine, but confirm
  the point's field expects unbounded rather than a sentinel value.
- **Duplicate rows for the same SKU + tier + band** with different prices —
  ambiguous. Report both; do not take the last one seen.
- **A tier present in the card but not in the price list** — report; do not
  fold it into the nearest tier.
