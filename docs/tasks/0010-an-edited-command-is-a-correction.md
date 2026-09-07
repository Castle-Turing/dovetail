Title: An edited command is a correction worth keeping
Milestone: M3

# 0010 — An edited command is a correction worth keeping

The backlog entry this milestone came from (promoted and deleted by
task 0009; its text survives in that task's PR and in git history)
holds the reasoning: the delta between the command an agent proposed
and the command the resident actually ran is exactly the correction
signal the castle's evidence ranks above ratings, and the record the
verb keeps is also what lets the proposing agent close the loop —
verify the outcome from artifact state, never from anyone's say-so.

Read first: `AGENTS.md`, `docs/run.md` and `docs/vision.md`'s M3
section as 0009 left them, and `tools/dovetail-run/` — this task
changes that package and nothing else.

## The record

`dovetail-run` gains one flag: `--record PATH`. When given, the
wrapper writes a single JSON object to PATH after the interaction
ends, whichever way it ends:

- `proposed` — the command as proposed, verbatim.
- `executed` — the line actually run, verbatim; `null` if declined.
- `declined` — boolean.
- `exit_status` — the executed command's exit status; `null` if
  declined.
- `from`, `why` — the provenance, as given; `null` when absent.
- `proposed_at`, `finished_at` — ISO 8601 UTC timestamps: when the
  prompt was shown, and when the record was written.

JSON, not `Key: value` lines, because a shell command can contain any
text at all, and the record must carry it unambiguously; the choice
belongs in `docs/run.md` with that one-sentence reason.

Semantics:

- Written via a temporary file in the same directory and an atomic
  rename, so a poller either sees no record or a whole one, never a
  half-written one.
- Without `--record`, no record is written and nothing else changes.
- The verb exits after launch confirmation as before; the record
  appears when the resident finishes. A caller that wants the outcome
  polls for the file — say exactly that in the docs.
- If PATH's parent directory does not exist, refuse before spawning
  the terminal, naming the path. Creating directories unasked is a
  guess about the caller's layout.
- What Dovetail keeps is the record file, nothing more. Journaling it
  when the proposer is a castle seat is the caller's business, in the
  caller's repo; `docs/run.md` says so in one line so nobody comes
  looking for more here.

## Scope bound

No other flags, no changes to the prompt contract, the sanitization,
or the launch path. Do not widen the diff past what the record
requires.

## Verification plan

Agent-testable, no human involved:

- Unit tests: the flag reaches the wrapper's argv; a missing parent
  directory is refused before any spawn, naming the path.
- Extend 0009's pty-driven Nix check: an accepted pre-filled line, an
  edited line, and a declined prompt each produce a record with the
  right `proposed`/`executed`/`declined`/`exit_status`; the edited
  case shows `proposed != executed`; no partial file is ever present
  afterward; without `--record` no file appears.
- `nix flake check` green.

Genuinely needs human hands: nothing.

## Housekeeping

This brief is `docs/tasks/0010-an-edited-command-is-a-correction.md`.
Commit it on your branch exactly as you received it, header lines
included, and append a "Judgment calls made during implementation"
section recording every decision you made where this brief was
ambiguous. That section is part of the deliverable.

## Judgment calls made during implementation

**`Milestone: M3` was added to this brief's header.** The brief arrived
with no header lines at all, just the body starting at `# 0010 — ...`.
Task 0009 hit the same gap and added `Milestone: M3` for the same
reason — this task is more of the run verb's own milestone, not a new
one — so the header here follows that precedent rather than leaving
`Title:` as the only key.

**The record is written by the wrapper, not by `dovetail-run` itself,
because `dovetail-run` has already exited by the time there is anything
to record.** The verb's whole contract is "return once the prompt is on
screen"; the resident may take an hour. So the write has to happen in
the process that outlives the verb — `prompt.bash` — which needed two
new things to do it: a JSON encoder, which bash does not have, and an
absolute path to a Python that has one, for the same reason bash itself
is baked in as a store path rather than found on `$PATH`. `record.py`
is shipped as package data beside `prompt.bash` (self-located via `$0`,
no `dirname` process) and doubles as an ordinary importable module, so
its `build_record`/`check_record_path` functions are unit-tested
directly in pytest without going anywhere near a pty.

**The record is written before the wrapper's final "press Enter to
close" hold-open, not after.** The brief says the record "appears when
the resident finishes," which could mean either the command finishing
or the window finishing. I read it as the former: a caller polling for
the correction signal is waiting on the outcome, not on the resident
having read the output and dismissed the window, and the two can be
minutes apart. `docs/run.md` states this choice in the record section.

**A record write that fails does not change the command's own exit
status.** The wrapper prints a warning to stderr and continues to
`exit "$status"` for the command that actually ran. The alternative —
folding a disk-full or permissions failure into the number the resident
watches — would make the one thing this verb promises (the exit status
you see is the command's) conditional on something it does not
promise.

**`from` and `why` collapse blank and absent to the same `null`,
matching the rest of the verb.** `cli.py` already turns `--from ""` (or
`--from` omitted) into the same `None` used for the provenance block's
"unattributed" text, before this task's code ever sees it. The record
reuses that same value rather than adding separate presence-tracking to
distinguish "typed a blank string" from "said nothing," a distinction
nothing else in this verb makes either.

**Ctrl-C is not specially handled, and writes no record.** `docs/run.md`
already documents Ctrl-C as taking the window with it "without a word,"
because the wrapper has no `trap` and bash's default SIGINT disposition
simply ends the script. That means a resident who kills the window with
Ctrl-C leaves no record even when `--record` was given — consistent
with the existing behavior the docs describe, and outside the three
cases (accepted, edited, declined-via-clear-or-EOF) the brief's
verification plan asks for.

**The wrapper's own arity moved from two arguments to five, always.**
Rather than a variable argument count depending on whether `--record`
was given, the wrapper always receives `block`, `command`, `record_path`,
`from`, `why` — an empty string standing in for "not given" in the last
three. A fixed shape is simpler to check for than optional trailing
arguments, and it is an internal contract `prompt.bash` and `prompt.py`
share; nothing public depends on its exact argument count.

**Timestamps use bash's `printf '%(fmt)T'` builtin under `TZ=UTC`,
not an external `date` call.** The wrapper otherwise depends on nothing
but bash builtins so it never has to guess what is on the resident's
`$PATH`; reaching for `date` here would have been the one exception.
`printf`'s strftime builtin (bash 4.2+) gives the same ISO 8601 UTC
timestamp with no process spawned.
