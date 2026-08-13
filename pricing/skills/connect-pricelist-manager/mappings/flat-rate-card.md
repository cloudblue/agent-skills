# Flat Vendor Rate Card → Connect Price Points

> **Quick reference.** The authoritative target schema is a real price
> point read from the draft version you are editing (workflow step 3) — its
> keys are what you write. This file is for reasoning about the *source*
> side and the matching rule.

The common shape: one row per SKU, one price per row, sometimes a cost and
a suggested retail price side by side. Example:
[`../examples/inputs/vendor-rate-card.csv`](../examples/inputs/vendor-rate-card.csv).

```
Part Number,Product Name,Unit,Currency,Partner Cost,MSRP,Effective Date,Billing Period
ACME-PRO-M,Acme Pro,Seat,USD,12.00,18.00,2026-09-01,Monthly
```

## The matching rule

| Connect side | Vendor side |
|---|---|
| Price point identity | matched, never supplied — see below |
| item **MPN** | `Part Number` (the vendor's SKU / part number / offer id) |
| item unit and billing period | `Unit`, `Billing Period` — **verification only**, not written |
| cost attribute of the point | `Partner Cost` (what you pay the vendor) |
| sale/list attribute of the point | `MSRP`, if the user wants list prices moved too |
| version effective date | `Effective Date` — becomes the *schedule* date in workflow step 7, not a point field |
| price list currency | `Currency` — must **equal** the list's currency; never converted |

**Points are matched, not created.** Every price point already exists,
because it was generated from the items in the product/agreement behind
this price list. Your job is to update values on existing points. Resolve
`Part Number` → item MPN → the point in the draft version, then write.

`Unit` and `Billing Period` are the sanity check that the match is real: a
vendor row priced per *month* landing on a point billed per *year* is a
mapping bug, not a price change. Compare them; do not write them.

## Rows that must not become updates

- **SKU matches no point** — the item is not in this price list. Report it;
  adding items is `connect-product-builder`'s job (`products` plugin).
- **Price identical to the current point value** — drop it. Rate cards are
  mostly unchanged month over month, and dropping these is what keeps the
  call count workable.
- **Empty / non-numeric price cell** — often a footnote row, a subtotal, or
  "contact us". Report, never coerce to `0`.
- **Rows in a second currency** — a mixed-currency card targets more than
  one price list. Split by currency and handle one list at a time.
- **Negative prices** — not a pricing mechanism in Connect. Escalate to the
  user; usually a credit note that belongs nowhere near a price list.

## Columns that map to nothing

- `Product Name` — human label; the item's name in Connect is the catalog's,
  not the vendor's. Useful in your diff summary, not in any write.
- Discount / margin percentage columns — derived, and the derivation is the
  user's commercial policy. Use the absolute price columns.
- Tax, VAT, or gross-price columns — Connect price points are pre-tax. Pick
  the net column every time.
- Region / country columns — the price list is already scoped to one
  marketplace. If the card is multi-region, one region maps to this list;
  ask which.
