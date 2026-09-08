Title: Task 0014 — adopt the state-and-tasks conventions
Model: deep
Model-because: I am Claude Sonnet 5, running as the dedicated agent for
this migration rather than delegating it onward. The work is not
mechanical: deciding what in this repo is current truth versus record,
which vision.md claims can be safely marked [inferred] versus left out
entirely, and — the one judgment call this brief spends the most words
on — noticing and not silently resolving a real semantic collision
between dovetail's existing `Milestone:` header and the one this
migration imports. A standard-tier pass would likely have copied
castle-turing's `Milestone:` rule over the top of dovetail's existing,
already-in-use one without noticing the collision; catching that
required reading the actual queue files, not just the convention docs.
Milestone: none — repository mechanism

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
- `docs/state/MILESTONE.md` — seeded with Milestone 3 ("the joint"),
  the milestone the open queue is currently working, inferred (never
  directly stated by the resident in any record this migration found)
  from `docs/vision.md`'s Roadmap section, `README.md`'s status line,
  and every open queue file 0008–0012 citing `Milestone: M3`. Every
  clause is marked `[inferred]` with its basis named; nothing is marked
  `[stated]` except the two operator-session facts named in the
  Position section (the migration order, and task 0013's provenance).
- `docs/tasks/README.md` — a new "The `Milestone:` header" section
  documenting the header's existing, previously-undocumented semantics
  (a roadmap-milestone name or `none — repository mechanism`), plus the
  wrapped-header-line parsing fact from Castle Turing's tasks README.
  It does **not** redefine the header to mean clause keys — see
  "Left deliberately unresolved" below.
- `AGENTS.md` — a new bullet in "The work record" naming `docs/state/`
  and pointing at its README, and a one-line addition to the task-file
  format bullet flagging the `Milestone:` header's two meanings.
  `CLAUDE.md` is an import of `AGENTS.md` (`@AGENTS.md`) and carries no
  conventions of its own, so it needed no separate edit.
- `docs/backlog/generated-reporting-has-no-enforced-discipline.md` — a
  new backlog entry, since dovetail has a backlog convention (unlike
  the deliverable list's fallback instruction to note its absence): the
  reporting discipline in `docs/state/README.md` is a stated rule with
  no generator yet to check it against.

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
- **No retrofit of `Milestone:` headers onto 0006–0013.** Their values
  are the resident's to assign, per this migration's own constraint —
  see "Migration debt" below.
- **No `[m3-constraints]` section in `MILESTONE.md`.** Castle Turing's
  M2 carries a constraints section because the resident stated two
  binding constraints for that milestone specifically. No equivalent
  resident statement exists for dovetail's M3; inventing one from
  `docs/vision.md`'s general non-goals would overstate what the
  resident actually bound the milestone to, so the Non-goals section
  is reported as `[m3-out]` (scope) rather than manufactured into
  `[m3-constraints]` (binding rules with waiver authority).

## The one genuine conflict, and why it stays open

Castle Turing task 0061 makes `Milestone:` on a task file cite a
`docs/state/MILESTONE.md` clause key, or the explicit value `none —
hygiene`. Dovetail already has a `Milestone:` header — used since task
0001, so before this migration existed — whose values are bare
roadmap-milestone names (`M1`, `M2`, `M3`) from `docs/vision.md`, plus
`none — repository mechanism` (task 0004) as its own explicit
non-milestone value. These are two different things wearing the same
key name: one cites a clause in a document patched per PR, the other
cites a section of a document that is explicitly *not* patched per PR
("nothing in it is yet a binding commitment," per `docs/vision.md`
itself).

Per this migration's own instructions, a genuine conflict is reported
rather than resolved silently, so: `docs/tasks/README.md` now documents
dovetail's existing `Milestone:` semantics (closing a real
documentation gap — it was used in seven files and specified nowhere)
and separately introduces the clause-keyed option `docs/state/`
provides, without picking one as the rule going forward. This brief
itself uses dovetail's existing phrase, `Milestone: none — repository
mechanism`, in its own header, in preference to the literal
`Milestone: none — hygiene` wording this task's instructions specified
— using a second synonym for the same explicit value would be exactly
the naming collision this project's own conventions treat as a defect.
Whether new task files should cite roadmap-milestone names, state
clause keys, or both is the resident's decision, not this migration's.

## Migration debt

Queue files that predate this migration and are not touched by it:

- **0006, 0007, 0008, 0009, 0010, 0012** already carry `Milestone:`
  headers with roadmap-milestone values (`M1`, `M2`, `M3`) — correct
  under the pre-existing convention this migration documents but does
  not change.
- **0011** and **0013** have no `Milestone:` header at all. This
  migration's own instructions named 0013 as the known gap; checking
  the full 0006–0013 range at write time found 0011 in the same state
  (it predates the `Milestone:` header becoming apparently-universal
  practice) — corrected here in the report, not retrofitted onto the
  files.
- **0012 and 0013 are not on `origin/main`.** Both exist only as
  untracked files in the primary checkout (`docs/tasks/0012-...md`,
  dated 2026-09-06, and `docs/tasks/0013-...md`, dated 2026-09-07);
  neither is on any fetched remote branch. This worktree, built from
  `origin/main`, does not contain either file. `docs/state/MILESTONE.md`
  records this as a Position fact; it is not this migration's place to
  commit or move those files.

None of the above is retrofitted by this task. The resident assigns
`Milestone:` values to existing files if and when they warrant it.

## Verification

No code changed; nothing here alters build behavior. Agent-verifiable:
the new and edited files are plain markdown with no schema to
validate — read them for internal consistency (clause keys used
consistently, every `[inferred]` clause naming its basis, no
`[stated]` clause without a citable source). Needs the resident: this
PR's description asks explicitly that every `[inferred]` clause in
`docs/state/MILESTONE.md` be checked against what the resident actually
knows to be true, since an inference this migration got wrong is worse
than a section left blank — nothing here should be treated as settled
until that pass happens.
