Title: The run verb
Milestone: M3

# 0009 — The run verb

Promotes `docs/backlog/an-agent-cannot-hand-the-resident-a-command.md`,
per the backlog lifecycle in `docs/backlog/README.md`: the same commit
that adds this brief deletes the backlog file.

Read first, in this order: `AGENTS.md`; `docs/vision.md`; the backlog
entry itself — its design notes are starting positions for this task,
not suggestions; `docs/show.md` for the sibling verb's structure and
launch semantics; `tools/dovetail-seams/src/dovetail_seams/launch.py`
for the machinery you reuse; `docs/scriptorium.md` for the refusal
conventions; `nix/checks/show-launch-failure.nix` and
`nix/checks/scriptorium-room.nix` for the check patterns.

## What it is

`dovetail-run` puts a command in front of the resident — visible,
editable, and **not executed**. One invocation opens a terminal
(floating, by the same rule and machinery as `dovetail-show`'s launch
path) whose content is a provenance comment and a pre-filled shell
line. Nothing runs until the resident presses Enter; editing the line
first, or declining it entirely, are equal citizens. The editor gave
agent and resident a shared page; this gives them a shared prompt.

```
dovetail-run [--from NAME] [--why TEXT] [--terminal COMMAND]
             [--no-float] COMMAND
```

`COMMAND` is one positional argument: the exact shell line the
resident would type. `--from` names the proposing agent, `--why` says
why, and both feed the provenance comment. `--terminal` and
`--no-float` mean what they mean on `dovetail-show`.

New package `tools/dovetail-run/`, mirroring its siblings' layout,
with `nix/packages/dovetail-run.nix` and the flake exposing the
executable. One word, one job: `dovetail-run` is its own executable,
as each verb is.

## The center of the design: the reflex-yes hazard

A pre-populated command habitually Entered is the confirmation
problem with the resident's privileges attached. The backlog entry
names three bindings, and they are the spec, not decoration:

1. **The line is editable.** The pre-fill mechanism is a wrapper
   shell using bash's `read -e -i` — a real readline line the
   resident can edit, with the terminal resolved through the same
   argv-prefix slot as every other verb. A multiplexer's send-keys
   was rejected because it would tie the verb to one multiplexer by
   name, exactly what the terminal seam exists to avoid; kernel
   TIOCSTI stuffing is disabled by default on modern kernels. Verify
   `read -e -i` against reality in the Nix check (under a pty), not
   by assertion.
2. **Provenance is always printed.** Comment lines above the prompt
   name the proposing agent and the why, from `--from` and `--why`;
   when they are absent the block still prints, with the proposer
   shown as unattributed — an honest nag, not a blank.
3. **What is displayed is what runs.** The proposed command, and the
   `--from`/`--why` text (they are echoed into the same terminal),
   are refused — never repaired — if they contain anything that can
   make display and execution differ: C0 control characters
   (including tab and newline), DEL, the C1 range, and the Unicode
   bidirectional controls (U+202A–U+202E, U+2066–U+2069). Name the
   offending character and its offset in the refusal. An empty or
   whitespace-only command is refused too. This is the paste-jacking
   class; if you find another member of it, refuse that as well and
   record the addition.

## The wrapper

A small script shipped inside the package, invoked as the trailing
arguments of the resolved terminal argv (so `foot -e` and
`wezterm start --` both work, and no shell sits between the verb and
the wrapper — arguments pass as argv elements, already sanitized).
Its behavior, in order:

1. Print the provenance block.
2. `read -e` with the proposed command pre-filled, as a prompt line.
3. An empty accepted line, or EOF (Ctrl-D), declines: say so and
   exit without executing anything. Ctrl-C likewise runs nothing.
4. Execute exactly the accepted line — byte for byte the line that
   was displayed at the moment Enter was pressed.
5. Print the command's exit status, then hold the window open until
   the resident presses Enter again, so output survives long enough
   to be read.
6. Write nothing to any history file. The resident's shell history
   belongs to the resident's shell; a one-shot wrapper appending to
   `~/.bash_history` uninvited would be the wrong-channel failure
   this ecosystem exists to avoid.

The verb itself behaves like `dovetail-show`'s launch path: spawn the
terminal, confirm the launch loudly on every path (window wait plus
floating when a compositor is reachable, the bounded liveness watch
when not — task 0007's semantics, via the seams), then exit. The
command's eventual outcome is deliberately not the verb's exit
status: the agent closes the loop afterward from artifact state, and
task 0010 gives it a record to read. Do not build the record in this
task.

## Non-goals

- **No `--just-run`, no auto-execute of any kind.** Auto-run arrives
  via the authority taxonomy or not at all; state this in
  `docs/run.md` so a stranger knows it is a refusal, not an
  oversight.
- **No execution record yet** — that is task 0010.
- **No multi-line commands.** A newline is refused with the rest of
  the control characters; document the limitation.

## The vision amendment

The same PR amends `docs/vision.md`, in its voice:

- A new roadmap section "M3 — the run verb", after M2: what the verb
  is, the comprehension-principle reasoning (watching the command run
  teaches what is going on under the hood; the posture is doing, not
  being shown), and the reflex-yes bindings in one breath.
- The joint becomes M4. Update the "must come last" sentence and the
  contract-extraction sentence: the contract is extracted from what
  M1, M2 and M3 actually called.
- Do not rewrite anything else in the document.

## Documentation

`docs/run.md`, written for strangers, mirroring `docs/show.md`'s
structure: what it is, trying it, the prompt contract (provenance,
editability, decline, the hold-open), the refusals and why they are
refusals, options and environment tables, what `nix flake check`
proves, and a short by-hand checklist for the parts only a real
desktop can show. Add the verb to `README.md` alongside its siblings.

## Verification plan

Agent-testable, no human involved:

- Unit tests: sanitization refusals (each character class, offset
  named), empty-command refusal, argv assembly through a terminal
  prefix, provenance rendering with and without `--from`/`--why`.
- A Nix check driving the wrapper directly under a pty (the terminal
  slot filled with `env`, as `scriptorium-room` does, or the wrapper
  run headless under `script`/a Python pty): Enter on the pre-filled
  line runs exactly the proposed command (prove it by side effect);
  an edited line runs the edited line; a cleared line runs nothing
  and says it declined; the pty capture shows the displayed line
  byte-equal to what ran.
- The launch-failure check pattern: `--terminal false` fails the
  whole invocation loudly, naming the exit status;
  refusal cases exit nonzero before any terminal is spawned.
- `nix flake check` green.

Genuinely needs human hands: the floating placement on a real Sway
desktop and the feel of editing the line — the checklist at the end
of `docs/run.md`.

## Housekeeping

This brief is `docs/tasks/0009-the-run-verb.md`. Commit it on your
branch exactly as you received it, header lines included — deleting
the backlog file in that same commit — and append a "Judgment calls
made during implementation" section recording every decision you made
where this brief was ambiguous. That section is part of the
deliverable.
