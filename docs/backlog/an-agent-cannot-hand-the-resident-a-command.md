# An agent cannot hand the resident a command

**What.** Proposed by the resident, 2026-09-06, out of a live
incident: an agent had composed the exact `nixos-rebuild` invocation
a deploy needed, had no way to place it in front of the resident
(the harness's `!`-prefix is lore, not a surface), and the resident's
own attempt then silently no-op'd in a terminal the agent could not
see. The proposal: a new verb, `dovetail run`, which opens a terminal
pre-populated with a command — visible, editable, and **not
executed** — so the resident watches, learns, and presses Enter. The
editor gave the agent and resident a shared page; this gives them a
shared prompt.

**Why not silent execution, in the resident's words:** watching the
command run teaches what is going on under the hood. This is Castle
Turing's comprehension principle operating — in domains the resident
wants to grow in, the posture is doing, not being shown — and it is
the first concrete mechanism for the long-standing
`apprenticeship-has-no-mechanism` gap in the castle's backlog. The
agent still closes the loop by verifying the outcome from artifact
state afterward, never from the resident's or its own say-so.

**Design notes for whoever specs it.**

- *The joint is half built.* `dovetail-show` already resolves
  terminals via `dovetail-seams` (`terminal_argv`); `run` is the
  second consumer of the same seam, and the terminal-resolution gap
  the incident also surfaced (no `$DOVETAIL_TERMINAL` in agent
  session environments) should be fixed once, declaratively, for
  both verbs.
- *Pre-fill mechanism is a spec-time question.* Kernel TIOCSTI
  stuffing is dead on modern kernels; the candidates are a wrapper
  shell (`read -e -i "$cmd"` then eval — editable line, real
  history) or a multiplexer's send-keys-without-Enter. Verify
  against the current foot/tmux reality then, not now.
- *The reflex-yes hazard is the design's center, not a footnote.* A
  pre-populated command habitually Entered is the confirmation
  problem with the resident's privileges attached (castle task 0059
  is the precedent surface). Bindings: the line is editable; a
  provenance comment above it names the proposing agent and the why;
  and the stuffed text is sanitized so what is displayed is what
  runs — escape sequences can make those differ (the paste-jacking
  class).
- *An edited command is a verbatim correction.* The delta between
  proposed and executed is exactly the correction signal the
  castle's evidence ranks above ratings; the verb should preserve
  both forms for the journal when the proposer is a castle seat.
- *Auto-run arrives via the authority taxonomy or not at all.*
  Watch-and-run-yourself, agent-runs-with-report,
  agent-runs-silently is a competence-gated ladder; the records this
  verb keeps are what let a rung be earned. No `--just-run` flag
  before the taxonomy grants it.
- *Cross-repo consumer.* castle-turing's
  `approval-channel-has-no-transfer-of-control-strategy` names the
  gap this verb may generally fill; whoever specs either side should
  read the other.
