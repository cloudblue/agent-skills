---
name: connect-helpdesk-triage
description: Use when working a CloudBlue Connect helpdesk case (a `CA-` id) — reading what the partner actually asked, choosing the next lifecycle state (inquire, pend, resolve, close), handling attachments, and drafting the reply that goes out with it. Triggers on "triage case CA-1234", "which helpdesk cases need our attention", "draft a reply to this partner ticket", "the partner never answered our question", "can I close CA-1234", or "open a case about this failing subscription".
version: 0.1.0
license: Apache-2.0
metadata:
  hermes:
    tags: [CloudBlue, Connect, MCP, Helpdesk, Support, Triage]
    category: productivity
    related_skills: [connect-navigator, connect-mcp-setup]
---

# Connect Helpdesk Triage

You are working a Connect helpdesk case (`CA-…`) on the support side: figure
out what the partner is actually blocked on, decide which lifecycle state
the case should be in next, and write the message that goes out with the
transition.

Two halves, on two of `connect-navigator`'s rungs:

- **Reading, diagnosing and drafting is free — do it all, unasked.** Pull the
  case, read the whole thread and the attachments, look up the objects it
  refers to, and produce a finished reply plus a recommended transition.
- **Everything the partner can see is gated.** Posting a comment, attaching a
  file and every state transition are **outward-facing** — they leave your
  organization. Present the exact text and the exact target state, then wait.
  A send is its own step, never folded into the reads.

## Tool names in this skill

Helpdesk tools carry the `helpdesk_` prefix and follow the shared conventions
in `connect-navigator`, verbs over signatures included: the `helpdesk_*` names
below are convention-derived, so match each verb to its tool from the catalog.

## Read before you decide

Never draft from the case subject alone. Subjects are written in thirty
seconds by someone who is annoyed; the facts are in the thread and the
attachments.

1. **Get the case** — the single-case read in the helpdesk family, not a
   list row. Note: status, the requesting account, the product/subscription
   it points at, and how many round trips it has already had.
2. **Read the whole conversation**, oldest first. What you are looking for:
   what changed on the partner's side, whether your side already asked
   something and got no answer, and whether the ask drifted (the case now
   about a different problem than the subject says — very common after
   three replies). **If the catalog has no conversation/messages tool** (some
   deployments expose only the case read and attachments), say so and triage
   on the description plus the state-change history — and make the drafted
   reply explicit that the thread itself was not readable, instead of
   implying it was.
3. **Read the attachments** before answering, not after. Screenshots and
   logs are usually the only place the real error string appears, and a
   reply that ignores an attached log reads as if nobody looked.
4. **Resolve the referenced object.** A case that names a `PR-`, `AS-`,
   `LST-` or `PL-` id is often answerable only by looking at that object —
   see `connect-navigator` for the owning domain. If your token lacks that
   module's permission the lookup returns `403`; that is a permission gap,
   not evidence about the case, and it must be stated as unknown rather
   than guessed around.

Stop and reconsider scope if the case turns out to be a change request, a
commercial negotiation, or a platform outage. Those leave the helpdesk
lifecycle; say so instead of forcing a resolution.

## Choosing the next state

The four transitions differ by **who owes the next action**, and that is
the only question worth asking. Get it wrong and the case stalls silently:
a case pended when it should have inquired waits forever on a partner who
was never asked anything.

| Next state | Use when | Who owes the next move | The reply must |
|---|---|---|---|
| `inquire` | You cannot proceed without something only the partner has | Partner | Name exactly what you need, and why it unblocks them |
| `pend` | You have everything; the work is on your side or a third party's | You | Say what is in progress and what the next update will be — no question |
| `resolve` | The partner's problem is addressed and verifiable | Partner (to confirm or come back) | State what was done and how they can verify it |
| `close` | Nothing is pending on either side | Nobody — terminal | Usually nothing new; if closing after silence, say why |

The table names target states; the platform's state machine constrains the
path. **`inquiring` cannot go straight to `resolved`** — the case must pass
through `pending` first (the partner answered → `pend` → `resolve`). A
rejected transition answers `VAL_001 "The action is not allowed for current
status"`; treat that as "insert the missing hop", and announce the hop — it
is outward-facing like any other transition.

Rules that follow from the table:

- **One ask per `inquire`.** Three questions in one message get one answer,
  and the case burns another round trip. If you genuinely need three
  things, ask for the one that gates the others.
- **`pend` is not a parking space.** It means work is happening elsewhere.
  If nothing is happening, the honest state is `inquire` (you need
  something) or `resolve` (you don't).
- **`resolve` before `close`.** Resolve says "we believe this is fixed",
  which gives the partner a chance to disagree. Closing straight from an
  active case takes that away.
- **Silence is not resolution.** A partner who never answered an `inquire`
  gets a closing note that says the case is being closed for lack of
  information and can be reopened — never a `resolve` claiming a fix that
  was never confirmed.
- **Reopening is the partner's move.** If they replied after a resolve, the
  case is live again; don't re-resolve without addressing the new message.

## Creating a case

Only when the problem needs someone outside your reach — usually a
platform-side issue you can see but not fix. Before creating, search
existing cases for the same object and symptom; a duplicate case splits the
conversation and both halves get worse answers.

A case worth opening carries: what was attempted, the object ids involved,
the exact error text, when it started, and what has already been ruled out.
Attach the evidence rather than pasting a wall of log into the body.

Creating a case is **outward-facing** — the counterparty sees it immediately —
so it is **gated** like any other outbound step.

## Drafting the reply

This is the part that is judgment, and it is the part you do in full
without being asked. Draft for the person reading it, not for the case
record.

Shape it as: acknowledge the specific problem in their words → state what
you found → state the one thing that happens next (their action or yours).
Three short paragraphs beats one long one.

- **Answer the drifted ask, not the subject line.** If the thread moved on,
  address where it actually is and note the original question's status in
  one clause.
- **Mirror the partner's language** — both the human language they wrote in
  and their vocabulary for the objects. If they say "order", don't correct
  them to "fulfillment request" mid-answer.
- **No internal detail leaves the case.** Internal service names, ticket
  ids from your tracker, engineers' names, and anything about another
  partner's data stay out. This applies to attachments too: check a
  screenshot or export for other accounts' data before it goes outbound.
- **Say what you established, and name what is still open.** "It looks like
  maybe the sync failed" invites another round trip. If you don't know yet,
  `pend` and say you are checking.
- **No commitments you cannot make.** Response times, deadlines, credits,
  and escalation promises are policy, not drafting (see Non-goals). Write
  the technical content and leave the commitment to the human sending it.
- **Every claim traceable.** Each factual statement should trace to the
  thread, an attachment, or a tool result you actually read. Mark anything
  else as unverified in the draft so the reviewer sees it.

Present the draft as: the target state, the reply text verbatim, any
attachment you propose to add, and the one-line reason for that transition.
That is what the human is approving.

## Sending, once approved

Announce each mutation before you make it, and make only the ones that were
approved:

1. Post the comment / add the attachment (the partner-visible message).
2. Apply the transition — `inquire` / `pend` / `resolve` / `close`.

In that order: message first, then state. A case that flips to `inquire`
with no question in the thread is a partner staring at a status change and
wondering what is wanted. If the send succeeds and the transition fails,
say so plainly — the partner has already seen the message, so the fix is
the transition, not a second message.

## Non-goals

- **SLA policy decisions.** Whether a case is breaching, what priority it
  deserves, when to escalate, and what to promise a partner about timing
  are the support organization's calls. This skill can report what the case
  data says; it does not set or interpret the policy.
- **Fixing what the case is about.** Actually changing a request, a
  subscription, a listing or a price list belongs to those domains'
  skills — this skill answers the case and hands off.
- **Bulk queue management.** No mass transitions or mass closes; each case
  gets read.
