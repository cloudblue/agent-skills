# Workflow: build a Connect product to publishable state

The detailed playbook behind the five phases in [`SKILL.md`](SKILL.md). Every
phase from 1 onward **writes to the tenant**. Announce each write before you
make it, and never batch a write in with a question.

Prerequisite: the MCP client reaches the Connect endpoint and the token
carries the MCP permission plus the Products module permission, in a **vendor**
account. See the `connect-mcp-setup` skill (`core` plugin) if any call returns
`401`/`403`.

## Step 0 — Gather inputs (read-only)

Ask for everything missing in **one** round.

| Input | Needed for | Notes |
|---|---|---|
| Product name + short description | Phase 1 | Partner-facing; the human's words, not yours |
| Existing product id | Phase 1 | If extending rather than creating. `PRD-…` |
| Item list | Phase 2 | Per item: display name, **MPN**, **unit**, **billing period** |
| Whether items are quantity-based or usage-reported | Phase 2 | Drives the unit choice |
| What the buyer must supply at purchase | Phase 3 | → Ordering parameters |
| What the vendor returns after provisioning | Phase 3 | → Fulfillment parameters |
| Anything that varies per marketplace / reseller | Phase 3 | → Configuration parameters |
| Activation message wording | Phase 4 | Or explicit permission to draft it for review |
| Whether to publish | Phase 5 | Never assume yes |

If you are extending an existing product, read it first — product, items,
parameters and templates — using the domain's `list`/`get` tools before
changing anything. Two failure modes this prevents: creating a duplicate MPN,
and adding a parameter whose id already exists.

## Step 1 — Product shell (mutating)

```
products_manage(...)          # create when no id is passed
```

`products_manage` is the one create/update tool for the product itself: omit
the product id to create, pass it to update. Read its description for the
exact argument names — do not guess field names from other domains.

Output: the new `PRD-…` id. Everything after this takes it as an argument.

Report the id to the human immediately. If a later phase fails, that id is
what they need to resume.

## Step 2 — Items (mutating)

Use the `products` **item** family — a `manage`-style tool for create/update
plus list/get tools for reading. Find them by name in the catalog and read the
descriptions; the item tools take the product id plus the item payload.

Three fields carry all the risk:

- **MPN** — the vendor's own part number. It is the join key that later
  matches usage records and price points to this item. It must be unique
  within the product. Never invent one: if the human has not given it, ask.
- **Unit** — what one unit of quantity means (seats, licenses, GB, users, …).
  The unit also expresses whether the item is counted (reservation-style,
  quantity set at ordering) or metered (usage-reported after the fact).
  Confirm which model the human intends before choosing.
- **Billing period** — monthly, yearly, multi-year, one-time. Wrong here and
  every subscription bills on the wrong cadence.

Treat unit and billing period as **effectively frozen** once the version is
published and subscriptions exist. The corrective action later is a new item
plus deprecating the old one, not an edit. Say this to the human while they
still have the choice.

Create every item before moving on: Phase 3 may need to scope a configuration
parameter to a specific item, and Phase 4's templates may reference item names.

## Step 3 — Parameters (mutating)

The phase taxonomy and the decision procedure are in
[`SKILL.md`](SKILL.md#the-parameter-phase-taxonomy). Read that first — the
choice matters more than the call.

Use the `products` **parameter** family (one `manage`-style create/update tool
plus list/get). Per parameter you will supply, at minimum: the owning product,
the **phase**, a stable **id** in lower_snake_case, a buyer-facing title, a
type, and the required/hidden flags. Read the tool description for the exact
field names and the set of valid types — the type list is server-side truth
and drifts.

Work phase by phase, and echo the plan to the human as a grouped list before
creating anything:

```
Ordering (asked of the buyer at purchase):
  domain_name       Domain name             text     required
  admin_email       Administrator email     email    required
  region            Region                  choice   required

Fulfillment (returned by the vendor after provisioning):
  tenant_id         Tenant ID               text
  console_url       Console URL             text

Configuration (per marketplace / item, set once by the vendor):
  api_endpoint      Provisioning endpoint   text     scoped per marketplace
```

Then create them. This echo is cheap and it is where humans catch a
misclassified parameter — which is exactly the mistake that is expensive
later.

Checks before you create:

- No two parameters share an id.
- Nothing required is also hidden.
- Every value the vendor might have to ask the buyer to *correct* exists as an
  **ordering** parameter. If it only exists as a fulfillment parameter, the
  vendor has no way to send the request back for it.
- Choice/dropdown parameters have their allowed values listed, and those
  values are what the vendor's provisioning actually accepts.

## Step 4 — Templates (mutating)

Use the `products` **template** family. Templates are the partner-facing
messages Connect renders around a fulfillment request — most importantly the
**activation** message the buyer sees when their request is approved, which is
how provisioned data (the fulfillment parameters from Phase 3) reaches them.
Read the template tool's description for the available template types and
scopes rather than assuming; the set is server-side truth.

Two rules:

- **Templates interpolate parameter values.** A placeholder naming a
  parameter that does not exist renders as nothing, silently. Cross-check
  every placeholder in the body against the parameter ids you created in
  Phase 3.
- **The wording is the human's.** Draft if invited, but show the rendered
  body for approval before creating the template. This text goes to the
  vendor's customers.

At minimum a product needs an activation template before approved
subscriptions can tell the buyer anything useful. If the human has not
supplied one, flag it in the pre-publish checklist rather than publishing
without it.

## Pre-publish checklist

Run this as reads against the tenant, not from memory of what you created.
Report each line with its actual value.

1. **Product** exists and its name/description are the human's final wording.
2. **Items** — every intended item is present; MPNs are unique and match the
   vendor's SKU list exactly; each has the intended unit and billing period.
3. **Parameters** — the created set matches the grouped plan from Phase 3,
   phase by phase; no required+hidden combination; ids are stable.
4. **Templates** — at least one activation template; every placeholder in
   every template resolves to a real parameter id.
5. **Nothing pending** — no item, parameter or template the human mentioned
   is still uncreated.
6. **Downstream dependencies named, not created** — pricing and listing are
   separate plugins; state that they come *after* publication so the human
   knows publishing is not the last step of going live.

Anything that fails, fix before publishing. Publishing is not a way to find
out whether the product is complete.

## Step 5 — Publish the version (mutating, gated, irreversible)

```
products_publish_version(...)
```

**Do not call this without explicit confirmation in the current
conversation.** Present the checklist result plus a one-line statement of
consequence — "this freezes version N of PRD-…; further changes need a new
version" — and wait.

The publish tool **re-publishes an existing numbered version** — it does not
create one. Cutting a *new* version from the current draft master (the common
case when extending an already-published product) answers `404` on the target
version number; see the failure table for the path.

After publishing, verify with `stats.versions` (and the item's own `status`),
not the product's top-level `changes_description`/`public`/`staging` fields —
those reflect the *next* draft master and reset immediately, which reads as if
the publish never happened.

What changes after publication:

- The published version is **immutable**. Edits to items, parameters and
  templates go into a *new* version; they do not retroactively alter the
  published one.
- The product becomes usable by the downstream flows: price lists can be
  built against its items (`pricing` plugin) and listing requests can be
  raised for it (`listings` plugin).
- Existing subscriptions keep the version they were created under. Publishing
  a new version does not migrate them.

If the human wants changes *after* publishing, the answer is a new version —
not an attempt to edit the frozen one. Explain that rather than looking for a
tool that would undo it.

## When something fails

| Symptom | Likely cause | Next step |
|---|---|---|
| `403` on every `products_*` call | Token lacks the MCP permission or the Products module permission | `connect-mcp-setup` (`core` plugin); not a product problem |
| `403` on writes but reads work | Token's account is not the vendor that owns the product | Use a token minted in the vendor account |
| Duplicate / conflict error on an item | The MPN already exists in this product | List the existing items; confirm with the human whether this is the same SKU before creating a variant |
| Duplicate error on a parameter | The parameter id is already taken | Read the existing parameter; reuse it if it means the same thing, otherwise pick a new id with the human |
| Item or parameter rejected on a published product | The version is frozen | A new version is required; do not retry the same call |
| Publish rejected as incomplete | Something in the checklist is genuinely missing | Read the error, fix that specific gap, re-run the checklist. Do not loop on publish |
| `404` on publish for version N | Version N does not exist yet — the publish tool only re-publishes existing versions | A new version must be created-and-published in one step; if no create-version tool exists in the catalog, that is a documented MCP gap and the REST `POST /products/{id}/versions` (with `changes_description`, `public`) is the only path — say so instead of retrying |
| Activation message renders blank fields | Template placeholder does not match a real parameter id | Compare the template body against the parameter list; fix the template |
| A request for prices, marketplaces or listings | Out of scope | Name the owning plugin and hand over — do not improvise with `products` tools |
