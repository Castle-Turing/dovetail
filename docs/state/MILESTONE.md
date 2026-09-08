# The current milestone

This is `docs/state/` truth (see this directory's README): what the
project is building now, patched in the same PR that changes it.
Clauses carry bracketed keys; deriving work cites them. `[stated
<date>]` marks the resident's own words, with where they were said;
`[inferred]` marks the system's reading, held until the resident
confirms or corrects it, with the basis named.

## Milestone 3 — the joint

[inferred from `docs/vision.md`'s Roadmap section, corroborated by
`README.md`'s status line ("Two artifacts exist") and by every open
queue file 0008–0012 carrying `Milestone: M3`] M1 ("show me the
file") and M2 (the scriptorium) are both built and merged — their
history lives in `docs/tasks/done/` (0001, 0002, 0005, 0006, 0007),
not here. M3 is the milestone the open queue is currently working:
nothing in the repo's record states M3 as "current" in so many words,
but every in-flight task cites it and no task cites M1 or M2, which is
the basis for this reading.

### Intent [m3-intent]

[inferred from `docs/vision.md`'s M3 section] Extract the editor
contract from what M1 and M2 actually called — never designed in
advance — as a document written for strangers: ensure an instance
exists and is reachable; open a file, optionally at a line; create a
scratch buffer bound to a file; read buffer contents; apply an edit
through the editor; subscribe to or poll for changes; report what is
open where; and a discovery affordance, given a session, for its
control socket and protocol. Alongside the contract: the provider slot
as a module interface with Neovim as the default implementation,
existing tooling refactored to call the slot, and a providers
directory whose Emacs entry is a README only.

### Done looks like [m3-done]

[inferred from `docs/vision.md`'s M3 section] The contract document
exists, derived from M1 and M2's actual calls rather than imposed on
them. The provider slot exists as a real module interface, Neovim
occupies it as the reference provider, and existing tooling calls the
slot rather than shelling out to `nvim` by name. A stranger who wants
to implement a different editor has the Emacs-stub README as the hook.
Acceptance for the milestone lives in its numbered briefs, not here —
`docs/vision.md`'s own words.

### Explicitly out [m3-out]

[inferred from `docs/vision.md`'s Non-goals section, which is stated
against the project as a whole rather than M3 specifically, so its
scope here is an inference] The general rooms mechanism (the
scriptorium stays one concrete worksession). An Emacs implementation
beyond the stub. Rendered markdown previews. Any outward-facing
authority — nothing here sends, declines, or communicates on anyone's
behalf. Becoming the agent layer's edit path — the castle's worker
seat proposes diffs under its own contract, and Dovetail does not sit
in that path.

### Position [m3-now] — patched per PR

- Current-state layer: landing with this PR (task 0014, adopting
  Castle Turing task 0061's conventions).
- Merged and not yet swept to `done/`: tasks 0008, 0009, 0010, and
  0011 (the tidying task itself) are all merged into `origin/main` but
  still sit at the top level of `docs/tasks/` — directly checkable
  against `git log origin/main` and the directory listing, not an
  inference. Sweeping them is hygiene per `docs/tasks/README.md`, not
  a state fact, and is left for whoever next tidies the queue.
- Open queue, unmerged, at the top level: task 0012 ("the record
  carries a transcript") and task 0013 ("an AI pair-programming
  seat"). Both exist only as untracked files in the primary checkout —
  neither is on `origin/main` nor on any fetched remote branch as of
  this PR, verified directly. [stated 2026-09-08, via the operator's
  session] Task 0013 was added 2026-09-07 by the operator's session,
  out of the Castle Turing conversation-seat elicitation, and predates
  this migration.
- [stated 2026-09-08, via the operator's session] Migration to the
  `docs/state/` conventions this PR adds was ordered before the next
  sprint launches.
- `Milestone:` header semantics: dovetail's task files already use a
  `Milestone:` header (undocumented until this PR — see
  `docs/tasks/README.md`) whose values are roadmap-milestone names
  (`M1`/`M2`/`M3`) rather than clause keys into this file, plus the
  explicit non-milestone value `none — repository mechanism` (task
  0004). This migration does not retrofit that convention onto
  existing files; it is flagged as an open reconciliation question in
  `docs/tasks/README.md` and in this PR's brief, task 0014, for the
  resident to close.
