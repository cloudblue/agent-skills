# Diagnosing a stuck listing

The ordered ladder behind the "Diagnose a stuck listing" section of
[`SKILL.md`](SKILL.md#diagnose-a-stuck-listing). The question is almost never
"what is broken", it is "whose turn is it". Work in this order and stop at the
first answer.

1. **Is there a request at all?** List the requests for the product and
   marketplace. No request means nothing was ever asked for — the most common
   cause of "we submitted weeks ago" is a draft nobody submitted. **Caveat:**
   an unsubmitted draft is only listable from the vendor side; on a
   distributor token an empty list does not prove nothing exists. If the
   vendor claims they created something, verify from their side (or by exact
   id) before concluding the request was never made.
2. **Read the state.** Fetch the request and read `status`. The state machine
   table in [`SKILL.md`](SKILL.md#the-state-machine) names the owning side. Say
   the side out loud: *"this is with the distributor; it has been in
   `reviewing` since the 3rd."*
3. **`draft` is ambiguous — resolve it.** A never-submitted draft and a request
   the distributor bounced back with `refine` look identical by status. Check
   the request's history / status log and any refine note. If it was refined,
   the vendor has an unread instruction and that is the whole answer.
4. **`reviewing` — is it assigned?** Unassigned means it is in a queue nobody
   owns; assigned means chase the assignee. Different escalation, so say which.
5. **`deploying` — the distributor's provisioning is unfinished.** Nothing the
   vendor can do. Only `complete` moves it, and only from the other side.
6. **`completed` but the product still isn't purchasable — it is not a listing
   problem.** Stop working the listing and look at: no active price list in the
   marketplace currency (`pricing` plugin), product version not published
   (`catalog` plugin), or no contract/agreement covering the pair. Say which one
   you suspect and hand off.
7. **A transition returned `403` — you are probably on the wrong side.** Before
   anyone re-mints a token, check the account: vendors cannot `deploy` or
   `complete`, distributors cannot `submit`. Only if the side is right is it a
   permission problem (`connect-mcp-setup`).
