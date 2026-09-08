Title: Task 0014 — adopt the state-and-tasks conventions
Model: deep
Model-because: I am Claude Sonnet 5, running as the dedicated agent for
this migration rather than delegating it onward. The work is not
mechanical: deciding what in this repo is current truth versus record,
which vision.md claims can be safely marked [inferred] versus left out
entirely, catching a real mislabeling in my own first draft (see
"Correction" below) by rereading the source from a fresh checkout
instead of trusting an earlier read, and — after the resident's ruling
retired the two-vocabulary state this brief first described — deciding
per file whether a clause-key retrofit is honest or would misrepresent
already-completed work. A standard-tier pass would likely have taken
its first read of `docs/vision.md` on faith and copied `Milestone:` M3
content over the top of what M3 actually is; catching the mismatch
required rereading the primary source against the real branch, not the
convention docs.
Milestone: none — hygiene

# Task 0014 — adopt the state-and-tasks conventions

## What this is

Dovetail adopts the state/record split that Castle Turing built in its
own task 0061 ("a current-state layer, and the milestone document as
its first page"): a `docs/state/` directory holding maintained, current
truth, with everything else under `docs/` demoted to record — decided,
found, or considered, and when, but never assumed still true. The
motivation is the same one 0061 names for Castle Turing: intent
otherwise lives only in the resident's head or gets read out of
whichever brief happens to be cited as authority, and citing a brief as
authority is exactly what rots when that brief moves to `done/`.

This was ordered by the resident before the next sprint launches
[stated 2026-09-08, via the operator's session] — recorded as a
Position fact in `docs/state/MILESTONE.md` rather than only here, since
it is current, not historical.

## Correction: this branch's first `MILESTONE.md` mislabeled the milestone

The version of `docs/state/MILESTONE.md` first committed to this branch
read `docs/vision.md` from the primary checkout, which was 22 commits
behind `origin/main` at the time — exactly the staleness hazard
`AGENTS.md`'s session-discipline section warns about, encountered here
despite the warning because the worktree, not the primary checkout, was
used for every *edit*, but the primary checkout was still used for the
initial *reading* pass. The stale copy's Roadmap section named M3 "the
joint"; the current `docs/vision.md` on `origin/main` numbers the
milestones differently — M3 is "the run verb," M4 is "the joint," not
yet started. `MILESTONE.md` is corrected in this PR to describe the
real M3. This is stated plainly rather than folded into the "what
migrated" list below because it is a mistake this brief made and fixed,
not a design decision.

## What migrated, from where

- `docs/state/README.md` — the authority rule, the same-PR patch rule,
  the deliberate-accommodation rule, the provenance marks
  (`[stated <date>]` / `[inferred]`), and the ambiguity-tag discipline,
  adapted from Castle Turing's `docs/state/README.md` (task 0061) and
  cited there by name rather than reproduced from its source research.
  A "How status is reported" section was added, carrying the reporting
  discipline from Castle Turing task 0062 (the operator handover): no
  completeness vocabulary in generated reports, every claim cited,
  ungrounded lines marked `[unverified]`, threats and drift reported
  before accomplishments. Dovetail has no generator that reads
  `docs/state/` yet, so this section is a rule for the first one that
  gets built, not an enforced check — see the backlog entry below.
- `docs/state/MILESTONE.md` — seeded with Milestone 3 ("the run verb",
  corrected per above), the milestone the open queue is currently
  working, inferred from `docs/vision.md`'s Roadmap section and
  corroborated by tasks 0009 and 0010 both citing the old-style
  `Milestone: M3`. Every clause is marked `[inferred]` with its basis
  named; the only `[stated]` marks are the operator-session facts named
  in the Position section (the migration order, task 0013's provenance,
  and the resident's 2026-09-08 ruling on the `Milestone:` header
  below).
- `docs/tasks/README.md` — a rewritten "The `Milestone:` header"
  section, plus the wrapped-header-line parsing fact from Castle
  Turing's tasks README. See "The `Milestone:` header, resolved" below.
- `AGENTS.md` — a new bullet in "The work record" naming `docs/state/`
  and pointing at its README, and a one-line addition to the task-file
  format bullet pointing at the `Milestone:` header's documentation.
  `CLAUDE.md` is an import of `AGENTS.md` (`@AGENTS.md`) and carries no
  conventions of its own, so it needed no separate edit.
- `docs/backlog/generated-reporting-has-no-enforced-discipline.md` — a
  new backlog entry, since dovetail has a backlog convention (unlike
  the deliverable list's fallback instruction to note its absence): the
  reporting discipline in `docs/state/README.md` is a stated rule with
  no generator yet to check it against.

## The `Milestone:` header, resolved

This brief's first version reported a genuine collision: dovetail
already had a `Milestone:` header (used since task 0001, undocumented)
whose values were bare roadmap-milestone names (`M1`/`M2`/`M3`) or the
explicit phrase `none — repository mechanism` (task 0004), wearing the
same key name as Castle Turing task 0061's clause-keyed convention. The
resident ruled on 2026-09-08: the castle-turing convention wins.
`Milestone:` in dovetail now means exclusively a `docs/state/
MILESTONE.md` clause key, or the explicit value `none — hygiene`; the
roadmap-name form and `none — repository mechanism` are retired.
`docs/tasks/README.md` records the ruling and its date, and notes in
one sentence which pre-existing files still carry a retired value so a
reader meeting one in `done/` or history understands it rather than
mistaking it for current practice.

## Retrofit performed on the tracked queue

The resident's ruling asked for the tracked queue files carrying old-
style or missing `Milestone:` values to be retrofitted with a proposed
clause key (or `none — hygiene`), each with a reason, flagged for the
resident to confirm or reassign at review — these four are proposals,
not settled:

- **0008** ("the terminal slot is declarative") → `m3-done`. Its own
  text calls itself "groundwork for the run verb" — direct textual
  evidence it serves `[m3-done]`'s declarative-terminal-resolution
  clause.
- **0009** ("the run verb") → `m3-done`. This is the verb `[m3-intent]`
  and `[m3-done]` both describe; it previously cited the roadmap name
  `M3` under the old convention, which was already the right milestone,
  just the wrong header form.
- **0010** ("an edited command is a correction worth keeping") →
  `m3-done`. Extends 0009's verb with the correction record
  `[m3-done]` names explicitly; also previously `Milestone: M3`.
- **0011** ("file merged briefs into done") → `none — hygiene`. Pure
  queue tidying (moving already-merged files to `done/`), textbook fit
  for the explicit non-milestone value — the clearest assignment of the
  four.

## Left unresolved, not retrofitted

Two tracked files were in scope for the retrofit and were deliberately
left untouched, because forcing either allowed value would misstate
them:

- **0006** ("scriptorium", `Milestone: M2`) and **0007** ("launch
  failures are loud on every path", `Milestone: M1`) both cite already-
  achieved milestones. `docs/state/MILESTONE.md` records only *current*
  truth — it has no live M1 or M2 clause key for them to cite, the same
  way Castle Turing's own `MILESTONE.md` keeps no clause for its
  achieved Milestone 1. `none — hygiene` would misrepresent them:
  both were substantive milestone work, not tidying. Retrofitting them
  would require either inventing historical clause keys in
  `MILESTONE.md` for milestones that are no longer current — a new
  accommodation this brief did not judge itself entitled to make
  unilaterally — or some other resolution the resident has not stated.
  `docs/state/MILESTONE.md`'s Position section records this as
  unresolved rather than choosing silently.

Four more files were never in the retrofit's stated scope (0006–0011)
and were left alone entirely, still carrying retired values: **0001**,
**0002**, **0005** (`Milestone: M1`) and **0004** (`Milestone: none —
repository mechanism`). Whether the resident wants these brought
forward too, on the same terms as 0006/0007 above, is open.

## Proposed values for the untracked files (0012, 0013) — not applied here

Tasks 0012 and 0013 exist only as untracked files in the primary
checkout, on neither `origin/main` nor any fetched remote branch; this
branch cannot reach them, and this PR does not touch them. Proposed
values, for the record and for whoever does apply them:

- **0012** ("the record carries a transcript") → `m3-done`, same
  reasoning as 0008–0010: it extends 0010 (`Requires: 0010`) and is the
  transcript clause `[m3-done]` names explicitly.
- **0013** ("an AI pair-programming seat in the editor") → no clean fit.
  It builds toward neither `[m3-done]` (the run verb) nor any M4 clause
  (M4 has none yet — "the joint" has no task file). It is not hygiene
  either: it is substantive feature work, from the Castle Turing
  conversation-seat elicitation, sitting outside the M1–M4 roadmap
  sequence entirely. Forcing `none — hygiene` on it would carry the
  same misrepresentation risk as forcing it on 0006/0007. This is
  reported rather than resolved.

## What was deliberately left out

- **No CI or lint enforcement of anything above.** Castle Turing's own
  0061 explicitly deferred this ("enforcement, if wanted, is a later
  task once the convention has been lived with"); the same applies
  here, more so, since dovetail has lived with the convention for zero
  PRs.
- **No `docs/architecture.md` or "Proposal" citations.** Castle
  Turing's `docs/state/README.md` and task 0062 both lean on
  `docs/architecture.md` Proposal 06 for the receipt/verdict grammar
  that grounds "no completeness claims." Dovetail has no equivalent
  document, so the reporting-discipline section states the rule
  directly (attributed to Castle Turing's operator-handover research
  and task 0062 by name) rather than inventing a local Proposal
  citation that would misrepresent dovetail as having its own
  architecture-decision record.
- **No `[m3-constraints]` section in `MILESTONE.md`.** Castle Turing's
  M2 carries a constraints section because the resident stated two
  binding constraints for that milestone specifically. No equivalent
  resident statement exists for dovetail's M3; inventing one from
  `docs/vision.md`'s general non-goals would overstate what the
  resident actually bound the milestone to, so the Non-goals section
  (plus the M3-specific auto-run exclusion `docs/vision.md` states
  directly) is reported as `[m3-out]` (scope) rather than manufactured
  into `[m3-constraints]` (binding rules with waiver authority).
- **No new historical clause keys for M1/M2 in `MILESTONE.md`.** See
  "Left unresolved, not retrofitted" above — adding them would resolve
  0006/0007's citation cleanly, but it is a real accommodation to the
  state layer's shape and stays the resident's call, not a byproduct of
  a header retrofit.

## Verification

No code changed; nothing here alters build behavior. `nix flake check`
passes (no derivations reference `docs/`). Agent-verifiable: the new
and edited files are plain markdown with no schema to validate — read
them for internal consistency (clause keys used consistently, every
`[inferred]` clause naming its basis, no `[stated]` clause without a
citable source, every retrofitted `Milestone:` value resolving against
a clause key that actually exists in `docs/state/MILESTONE.md`). Needs
the resident: this PR's description asks explicitly that every
`[inferred]` clause in `docs/state/MILESTONE.md` be checked against
what the resident actually knows to be true, and that the four
retrofit proposals above and the two unresolved cases be confirmed or
reassigned — nothing here should be treated as settled until that pass
happens.
