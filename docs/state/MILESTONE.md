# The current milestone

This is `docs/state/` truth (see this directory's README): what the
project is building now, patched in the same PR that changes it.
Clauses carry bracketed keys; deriving work cites them. `[stated
<date>]` marks the resident's own words, with where they were said;
`[inferred]` marks the system's reading, held until the resident
confirms or corrects it, with the basis named.

**Correction, 2026-09-08:** this document's first version, landed
earlier in this same PR, read `docs/vision.md` from a checkout 22
commits behind `origin/main` and mislabeled the current milestone "M3 —
the joint." The current `docs/vision.md` numbers it differently: M3 is
"the run verb," and "the joint" is M4, not yet started. This version
corrects that; nothing below should be read as ever having been shown
to the resident under the wrong label.

## Milestone 3 — the run verb

[inferred from `docs/vision.md`'s Roadmap section, corroborated by
tasks 0009 and 0010 both citing `Milestone: M3` under the old
roadmap-name convention] M1 ("show me the file") and M2 (the
scriptorium) are both built and merged — their history lives in
`docs/tasks/done/` (0001, 0002, 0005, 0006, 0007), not here. M3 is the
milestone the open queue is currently working; M4 ("the joint") is
next and no task file yet addresses it.

### Intent [m3-intent]

[inferred from `docs/vision.md`'s M3 section] One verb opens a
terminal holding a command the agent has composed — visible, editable,
and not executed — above a line naming who proposed it and why.
Nothing runs until the resident presses Enter; editing the line first
or declining it outright are equal citizens. The reason it does not
simply run the command is the comprehension principle: watching a
command run teaches what is going on, being told one ran teaches
nothing. Three bindings hold off a pre-populated command becoming the
confirmation problem with the resident's privileges attached: the line
is genuinely editable, provenance is always printed, and what is
displayed is what runs — text that could make those two differ is
refused rather than repaired.

### Done looks like [m3-done]

[inferred from `docs/vision.md`'s M3 section and the shape of tasks
0008–0010 and 0012, which build it in sequence] Terminal resolution is
declarative rather than environment-only, so an agent session with no
inherited interactive environment can still reach a terminal (task
0008). The run verb itself exists and behaves as `[m3-intent]`
describes (task 0009). The delta between the command an agent proposed
and the command the resident actually ran is kept as a correction
worth recording (task 0010). The record carries the executed command's
output, not just its exit status, so the proposing agent can see what
actually happened (task 0012). `docs/vision.md` states explicitly that
auto-run is out of scope for this milestone: "Auto-run arrives through
an authority taxonomy or not at all; there is no flag for it."

### Explicitly out [m3-out]

[inferred from `docs/vision.md`'s Non-goals section, stated
project-wide rather than M3-specifically, so its scope here is an
inference] The general rooms mechanism. An Emacs implementation beyond
the eventual stub. Rendered markdown previews. Any outward-facing
authority. Becoming the agent layer's edit path. Specific to M3
[inferred directly from `docs/vision.md`'s M3 section]: auto-running
the composed command without the resident's keypress.

### Position [m3-now] — patched per PR

- Current-state layer: landing with this PR (task 0014, adopting
  Castle Turing task 0061's conventions) — corrected in place, per the
  note at the top of this file.
- Merged and not yet swept to `done/`: tasks 0008, 0009, 0010, 0011
  (the tidying task itself), and 0012 ("the record carries a
  transcript," extending task 0010 — the piece that completes
  `[m3-done]`) are all merged into `origin/main` — checked directly
  against `git log origin/main` and the current directory listing, not
  an inference — but still sit at the top level of `docs/tasks/`.
  Sweeping them is hygiene per `docs/tasks/README.md`, left for whoever
  next tidies the queue. Task 0013
  ("an AI pair-programming seat"), added 2026-09-07 out of the Castle
  Turing conversation-seat elicitation, built toward neither `[m3-done]`
  nor any M4 clause (M4 has none yet); [stated 2026-09-08, via the
  operator's session] the resident resolved that fit question by
  parking task 0013 out of the queue entirely, handled outside this PR.
- [stated 2026-09-08, via the operator's session] Migration to the
  `docs/state/` conventions this PR adds was ordered before the next
  sprint launches. [stated 2026-09-08, via the operator's session] The
  `Milestone:` header means exclusively a clause key from this file, or
  the explicit value `none — hygiene`, binding on every task file
  written from that date forward; the roadmap-name form (`M1`/`M2`/`M3`)
  and the phrase `none — repository mechanism` are retired for new
  files — see `docs/tasks/README.md`.
- **Resolved:** tasks 0006 (`Milestone: M2`) and 0007 (`Milestone: M1`)
  predate this document and cite already-achieved milestones with no
  live clause key here. [stated 2026-09-08, via the operator's session]
  The resident ruled: a file written before the 2026-09-08 ruling keeps
  its retired value standing as record of the convention at the time it
  was written; only files written after the ruling must use the
  clause-key form. 0006 and 0007 (and, on the same basis, 0001, 0002,
  0004, 0005) are untouched by design, not by omission.
