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

## Judgment calls made during implementation

Every decision below is one this brief left open, recorded here so a
reader who was not in the room can see what was chosen and why.

**The refused set grew, as the brief invited.** Beyond the classes it
names, four more are refused, each for the same reason as the named
ones — the drawn line and the executed line would differ:

- The three remaining Unicode bidirectional controls, `U+061C`,
  `U+200E` and `U+200F`. The brief named the embeddings, overrides and
  isolates; the marks belong to the same property (`Bidi_Control` is
  exactly these nine code points) and reorder drawn text just as
  effectively. Refusing eight of nine would have been an arbitrary
  line.
- `U+2028` and `U+2029`, the line and paragraph separators, which a
  terminal or pager may break the line at — the newline failure with a
  different code point.
- The zero-width characters `U+00AD`, `U+200B` and `U+FEFF`. They
  occupy no width, so `rm /tmp<U+200B>x` reads as one path and runs as
  another. This is the hazard with no escape sequence involved.
- The zero-width joiner and non-joiner (`U+200D`, `U+200C`) are
  deliberately **not** refused, which is the other half of the same
  call. They are load-bearing inside ordinary text — an emoji sequence
  in a commit message — and they hide nothing that is not already
  visible beside them, so refusing them would reject commands a
  resident legitimately means to run.

**A prompt with no terminal refuses rather than reads.** The brief did
not say what the wrapper should do when its standard input is not a
tty. It exits 2 without running anything, which the verb then reports
as a failed launch. The reasoning is the verb's own promise: the
guarantee is that the resident *read* the line, and a line that cannot
be displayed has not been read by anyone. Reading a proposal from a
pipe would be the one path on which a command runs unseen. The
`run-prompt` check covers it.

**Declining does not hold the window open.** The brief's step 5 attaches
the hold-open to a command that ran, and its step 3 says a decline
"exits without executing anything", so a decline says what happened and
closes. A resident who has just cleared a line knows what she did; the
hold-open exists so that a command's *output* survives long enough to
read.

**The provenance block is rendered in Python, not in the wrapper.** It
is passed to the wrapper as one argument, whose only job is to print
it. The block is the thing the resident is asked to read before pressing
Enter, so it is worth unit-testing in the language the rest of the verb
is written in, and it leaves the wrapper with a job it cannot get wrong.

**Bash is baked in as a store path, with no override.** `dovetail-seams`
bakes in the editor, the client and the REPL; the prompt needs a bash
new enough for `read -e -i`, and the terminal the resident named may
start any shell or none. It is substituted in
`nix/packages/dovetail-run.nix` exactly as the other three are, and
there is deliberately no `$DOVETAIL_SHELL`: the wrapper *is* a bash
script, so a shell slot would be a slot nothing else could fill.

**The pty check drives the whole verb, not the wrapper alone.** The
brief offered either. Filling the terminal slot with a stand-in that
allocates a pty exercises the real argv path — the resident's prefix,
the baked bash, the shipped wrapper, the two sanitized strings — for the
same effort as running the wrapper directly, and it is the path a
resident's `foot -e` takes.

**`--from` reaches argparse as `dest="proposer"`.** `from` is a Python
keyword, so the attribute needs another name; the flag itself is spelled
as the brief specifies.

**`Milestone: M3` was added to this brief's header.** The brief arrived
with `Title:` only. Its own vision amendment makes the run verb M3, and
task 0006 carries the equivalent header for M2, so the queue reads
consistently with it.

**Four one-word corrections outside the vision document.** The brief
says not to rewrite anything else in `docs/vision.md`, and nothing else
in it was touched. But renumbering the joint left four references to it
as "M3" stale elsewhere in the tree — two in `docs/scriptorium.md`, one
each in `dovetail_seams/__init__.py` and `dovetail_seams/editor.py` —
and each was corrected to M4. A document that contradicts the founding
context is worse than a slightly wider diff.
