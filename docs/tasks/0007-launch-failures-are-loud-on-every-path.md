Title: Launch failures are loud on every path
Milestone: M1

# 0007 — Launch failures are loud on every path

Promotes `docs/backlog/launch-failures-are-silent-when-the-float-step-is-skipped.md`,
per the backlog lifecycle in `docs/backlog/README.md`.

## The defect

Found by the cross-vendor gate on pull request #6 and verified still
present on `main`: when `dovetail-show` launches an editor with
`--no-float`, or with no reachable compositor, the spawned terminal's
stdio is deliberately detached (`/dev/null` — the reasons are stated in
a comment in `launch.py` and remain valid), and `_report_no_window` is
only reached from the float step's window wait. A terminal that starts
and then exits — a broken `$DOVETAIL_TERMINAL`, bad arguments — leaves
no window, no diagnostic, and a zero exit status unless
`--print-socket` was requested. The resident asked for a file, got
nothing, and was told everything went fine.

## The fix

Make the window wait the launch confirmation, and floating the optional
action on top of it:

- **When a compositor is reachable, always wait for the window** —
  `--no-float` skips only the `floating enable` command, never the
  wait. The wait already distinguishes "the terminal exited" from "the
  window never mapped", returns as soon as the window appears, and is
  bounded by the existing five-second budget; a tiled launch gains the
  same failure detection the floating launch has, at no cost on the
  happy path.
- **When no compositor is reachable, watch the child briefly.** There
  is no tree to poll, so poll the child process instead: if it exits
  within a short bounded window, report that loudly. A child still
  alive when the budget expires is presumed fine — the check exists to
  catch quick deaths, not to prove a window will ever appear. Choose
  the budget deliberately, document it in `docs/show.md`'s timeout
  table, and report the choice in the pull request; two seconds is the
  brief's starting suggestion, not a requirement.

Exit semantics, on every path: a launch whose terminal died without
mapping a window **fails the invocation** with a nonzero exit status
that says what happened, including the terminal's own exit status —
the file was not put in front of anybody. A window that appeared but
could not be floated stays a stderr warning with a zero exit, exactly
as today: the file is open, which is what the caller asked for.

Update `docs/show.md` where it describes the failure and timeout
behavior. Do not widen the change past this: no new flags, no changes
to targeting, no changes to the float mechanics themselves.

## Verification plan

Agent-testable, no human involved:

- Unit tests over the no-compositor liveness watch with a driven clock
  and a fake process handle: a child that exits inside the budget is
  reported and fails; a child alive at the budget's end passes; the
  watch never outlives its budget.
- Unit tests asserting `--no-float` with a reachable compositor runs
  the window wait and reports a vanished terminal.
- An end-to-end check in the Nix sandbox (no compositor there, which is
  exactly the path under test): `dovetail-show` with `--terminal false`
  must exit nonzero and name the failure; the existing checks must
  still pass; `nix flake check` green.

Genuinely needs human hands: nothing. This task changes failure paths
that the sandbox can reach.

## Judgment calls made during implementation

- **The no-compositor liveness budget is two seconds** — the brief's own
  starting suggestion, kept as-is: it only has to catch a terminal that
  fails immediately, and the float path's five-second window-wait budget
  is for a genuinely different wait (a compositor placing a window),
  not a floor this one needs to match.
- **A clean exit (status 0) within the liveness budget is not a
  failure**, mirroring `_report_no_window`'s existing treatment of a
  zero exit status on the compositor path: a terminal that hands off to
  an already-running server (`footclient`, `kitty @ launch`) exits 0
  immediately as a matter of course, and is a documented, harmless
  limitation (`docs/show.md`, "A terminal that daemonizes will not be
  floated") rather than a failure. Only a nonzero exit is treated as
  proof the terminal itself failed.
- **`--no-float` plus a window that simply has not appeared yet within
  the timeout gets its own stderr wording** ("no window was seen for
  the new terminal", not "could not float the new window"), since
  nothing asked to float it in that case and the old wording would have
  been inaccurate now that the wait runs unconditionally.
- **A new Nix check, `show-launch-failure`**, exercises the
  no-compositor path end to end (`--terminal false` fails loudly,
  `--terminal true` does not), because the sandbox's total absence of a
  Wayland session makes it exactly the case this task added detection
  for — unlike the compositor-reachable paths, this one needed no
  compositor to check.
