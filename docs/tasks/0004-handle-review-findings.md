Title: Review findings are handled, not accumulated
Milestone: none — repository mechanism

# 0004 — Review findings are handled, not accumulated

Task 0002's pull request came back with three findings from the
cross-vendor review gate, and all three sat there until a human read the
pull request and asked for them to be addressed. That is the wrong
shape: a review whose findings nobody acts on is a review that costs
money and buys a list. The operator's standing preference, recorded in
the resident profile, is that findings arrive already judged — each one
fixed on the branch or answered with reasoning, before the human opens
the pull request.

This task installs that automation in this repository. It is repository
mechanism, not milestone work, so it belongs to no milestone.

## The change

One file: `.github/workflows/handle-review-findings.yml`, an unmodified
copy of the canonical workflow the resident profile keeps as
`templates/handle-review-findings.yml`. It triggers when a pull-request
comment carries the gate's marker —
`<!-- chevaline-gate: cross-vendor-review -->`, invisible in rendered
markdown — and runs an agent that reads the findings, fixes the valid
ones on the branch, declines the rest with stated reasoning, and posts a
single dispositions comment.

**The copy stays unmodified.** A repository that edits its own copy has
forked the default without saying so. Improvements go to the template in
the profile and are copied outward; if this repository ever needs
different behaviour, that difference is worth a brief of its own.

## Why the trigger is a comment rather than a review

Second opinions reach this repository as a plain pull-request comment
posted by the gate script, which runs locally — as the harness's
post-pull-request hook on unattended work, or by hand on a
hand-opened pull request. They do not arrive as a forge-native review
from a hosted reviewer, so there are no inline review threads to reply
to and nothing fires a `pull_request_review` event.

That has one consequence worth stating plainly, because it is a real
loss rather than an implementation detail: the receipt for a finding
cannot sit on the line the finding concerns. Every disposition lands in
one comment instead. It is the price of a gate that works on any
repository regardless of what a vendor's hosted reviewer supports, and
if the gate ever learns to post inline review comments, this workflow
should follow it there.

## Three rules in the file that must not be tidied away

**Marker-matching, not prose-matching.** The trigger tests for the
marker rather than the comment's heading, so the gate's wording can
change without silently switching the automation off — a failure mode
that looks exactly like "no findings this week".

**A concurrency group of one comment, which never cancels.** GitHub
evaluates a workflow's concurrency group *before* the job's `if:`
condition, so a group keyed by the pull request catches every unrelated
comment on it. The predecessor of this workflow in a sibling repository
did that with cancellation enabled, and that repository's own review
comments cancelled the handler mid-flight every time: across sixty runs,
twenty-nine cancelled, thirty skipped, one failed, none completed. It
had never once worked and nothing reported that it had not. Disabling
cancellation is necessary but not sufficient, because GitHub keeps at
most one *pending* run per group and a newer run evicts the waiting one
— so an ordinary comment could still discard a queued handler. Keying
the group by the triggering comment makes it a group nothing else can
join.

**An effective-permission check, not `author_association`.** On a public
organization repository `MEMBER` includes organization members with no
access to this repository, and `COLLABORATOR` can be read-only or
triage. Either could paste the marker into an open pull request and
spend the account's tokens on a write-enabled agent. The workflow
queries the collaborator permission API and requires write, maintain or
admin.

The second and third of those came from the gate's own review of the
first version of this workflow, on this pull request.

## Prerequisites this task cannot satisfy

The workflow needs a `CLAUDE_CODE_OAUTH_TOKEN` secret, and this
repository has no Actions secrets at all. Setting it requires the
operator's own credentials, so it is a human step, and an
organization-level secret is the better shape than a per-repository copy
because every repository under the organization needs the same one. The
workflow fails loudly rather than silently when the secret is absent,
which is the correct direction: an unhandled review is visible, a
silently skipped run is not.

A second secret, `REVIEW_BOT_TOKEN`, is optional but worth having.
Pushes made with the default workflow credential do not start a pull
request's checks, so a fix the handler pushes would leave a reader
looking at a green tick belonging to the previous commit. With the
secret, checkout and the agent both use a credential whose pushes emit
events and the checks simply run. Without it the workflow still works,
and the agent is instructed to state in its comment that the checks did
not re-run, naming the unchecked commit.

## Non-goals

- **No `@claude` mention responder.** Answering a human's mention on an
  issue or a review comment is a different automation with a different
  trigger. It may be worth adding later; it is not what this task is.
- **No automatic review of pull requests by a model in this repository.**
  The second opinion arrives from the gate; adding a same-vendor review
  on top would spend tokens to have a model check its own family's work.
- **No change to the gate script.** The marker it emits is profile-side
  and already in place.

## Verification plan

Agent-testable, no human involved:

- The workflow file is valid YAML and parses as a GitHub Actions
  workflow. (Done: three steps, parsed with `yq`.)
- It is byte-identical to the profile's template. This cannot be a check
  in this repository — the profile is the operator's own and is not
  public — so it is verified by whoever holds the profile at the moment
  of copying, and re-verified the same way whenever the template
  changes.

Genuinely needs human hands, because it needs credentials and a real
pull request:

1. Set `CLAUDE_CODE_OAUTH_TOKEN` (organization-level preferred).
2. On the next pull request that receives gate findings, confirm the
   workflow runs to completion rather than being cancelled or skipped —
   the failure this design exists to prevent is invisible unless the run
   list is actually read.
3. Confirm the dispositions comment names every finding the review
   raised, each either fixed with a commit hash or declined with
   reasoning.
