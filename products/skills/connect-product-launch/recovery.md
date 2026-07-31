# Recovering a failed launch

What each stage leaves behind, and what to do with it. Read this when a stage
fails after an earlier one already mutated — the rule it serves
(**roll-forward only**) is in
[`SKILL.md`](SKILL.md#when-a-stage-fails).

| Stage output | Reversible? | If a later stage fails |
|---|---|---|
| Product shell, items, parameters, templates (unpublished) | Yes, and invisible to everyone | Leave it. It is the resume point |
| **Published product version** | **No.** No un-publish exists | Leave it. A published version nobody listed harms nothing, and no delete or teardown tool is the answer here |
| Draft price list version and its points | Yes — affects nobody until activated | Leave it, and reuse it on resume. One draft per list |
| **Active price list version** | **No.** Correcting it means another version | Leave it active. Reaching for the version delete or price-list terminate tools as cleanup is a destructive act the user never asked for |
| **Draft listing request** | **Yes — the one genuinely disposable output** | Abandon it, or cancel it if the user asks. It is invisible to the distributor |
| **Submitted listing request** | Not by you alone | It is with the distributor. `cancel` is terminal, outward-facing, and needs its own confirmation — it is a message to the counterparty, not a rollback |

Two consequences to hold onto:

- **A blocker at stage 2 or 3 never sends you back to editing the published
  version.** The published version is frozen; a fix there is a *new* version,
  which is a new launch decision for the human, not a repair you perform.
- **Re-running a launch reuses what exists.** Read for the existing product,
  the existing draft price version and the existing listing request before
  creating anything. Duplicate products and second drafts are the signature
  damage of an orchestration skill retried blindly.
