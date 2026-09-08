Title: The record carries a transcript
Milestone: m3-done
Model: standard
Requires: 0010-an-edited-command-is-a-correction
Requires-because: it extends the record and wrapper that 0010 builds; the transcript file is named from the record's own fields.

# 0012 — The record carries a transcript

A requirement from the incident that started this milestone, stated by
the resident and missed at spec time: the proposing agent must be able
to see the output of the command the resident ran — the incident's own
words are that the resident's attempt "silently no-op'd in a terminal
the agent could not see". Exit status alone tells an agent that
`nixos-rebuild` returned 0; the output is what tells it what actually
happened. Task 0010's record deliberately stopped at proposed line,
executed line and exit status; this task adds the output, without
touching anything else about the verb.

Read first: `AGENTS.md`, `docs/run.md` as tasks 0009 and 0010 left it,
`docs/vision.md`'s M3 section, and `tools/dovetail-run/` — this task
changes that package and nothing else.

## The transcript

Only when `--record PATH` is given, the wrapper runs the accepted line
under a pty recorder instead of directly — `script -qec` is the
intended mechanism — so the command still believes it has a terminal
(progress bars, prompts, and color survive for the resident watching),
while everything the resident saw is captured to a transcript file
beside the record. Without `--record`, nothing changes: no recorder,
no files, the command runs exactly as 0009 built it.

Semantics:

- The transcript is its own file next to the record, not a field in
  the JSON — a rebuild log can be megabytes, and the record must stay
  a small thing a poller reads cheaply. The record gains one field,
  `transcript`: the path, or `null` when nothing ran (a declined
  prompt captures nothing).
- Ordering is the contract: the record is written — atomically, as
  0010 built it — only after the command has finished and the
  transcript is complete. A poller that waits for the record and then
  reads the transcript never sees a partial one. State this guarantee
  in `docs/run.md`.
- The exit status in the record stays the command's own. `script -e`
  propagates the child's exit code; make sure the recorder does not
  substitute its own.
- The provenance block says, when capture is active, that the output
  is recorded for the proposing agent. The resident must never
  discover capture after the fact.
- A pty transcript contains what was echoed, so prompts appear but
  unechoed input does not — a typed sudo password does not land in
  the file. Say this in the docs, because a stranger will ask.
- `script` is baked into the package as an absolute store path at
  build time, exactly as bash is — the wrapper never goes looking on
  the resident's `$PATH`.

## Scope bound

No new flags. No change to the prompt contract, the sanitization, the
launch path, or the record's existing fields. The killed-prompt gap —
Ctrl-C writing no record at all — is a separate backlogged problem
(`docs/backlog/a-killed-prompt-leaves-no-record.md` on its own PR at
the time of writing); do not widen this task into it.

## Verification plan

Agent-testable, no human involved:

- Unit tests: with `--record`, the wrapper's argv carries the baked
  recorder path; without it, the recorder is absent and the argv is
  byte-identical to 0010's.
- Extend the pty-driven Nix check: an accepted command that prints
  distinctive output produces a transcript containing that output and
  a record whose `transcript` field names the file; the record's exit
  status is the command's own, including a nonzero one; a declined
  prompt produces a record with `transcript: null` and no transcript
  file; without `--record`, neither file appears.
- `nix flake check` green.

Genuinely needs human hands: watching a genuinely interactive command
(a sudo prompt, a progress bar) behave normally under the recorder on
a real desktop — one line on the `docs/run.md` checklist.

## Housekeeping

This brief is `docs/tasks/0012-the-record-carries-a-transcript.md`.
Commit it on your branch with exactly these five header lines, which
are part of the file whether or not your prompt showed them to you:

    Title: The record carries a transcript
    Milestone: M3
    Model: standard
    Requires: 0010-an-edited-command-is-a-correction
    Requires-because: it extends the record and wrapper that 0010 builds; the transcript file is named from the record's own fields.

Append a "Judgment calls made during implementation" section recording
every decision you made where this brief was ambiguous. That section
is part of the deliverable.

## Judgment calls made during implementation

**`Milestone: m3-done`, not the literal `Milestone: M3` the brief's own
Housekeeping section quotes.** Between this brief being drafted and
being implemented, task 0014 landed on `main` and ruled that every task
file written from 2026-09-08 forward must use a clause key from
`docs/state/MILESTONE.md` rather than the retired bare roadmap-name
form (`docs/tasks/README.md`'s `Milestone:` section). `docs/state/MILESTONE.md`
itself already names this task explicitly under `[m3-done]` — "The
record carries the executed command's output, not just its exit
status, so the proposing agent can see what actually happened (task
0012)" — so the clause key was not a guess, it was already on record
as this task's own citation. Writing `M3` here would have reintroduced
the retired form on the same day it was retired, in the one file where
the state document already names the correct replacement.

**The transcript filename is `PATH` with `.transcript` appended,
computed by a new pure function, `record.transcript_path_for`.** The
brief says only that the file sits "beside the record" and is "named
from the record's own fields" (per this brief's own `Requires-because`
line); it does not fix an exact scheme. Appending a suffix to the whole
path — rather than, say, swapping a `.json` extension — works
regardless of what extension (if any) the caller gave the record, and
needs no assumption about it.

**The baked `script` binary is threaded through `wrapper_argv` as two
extra trailing argv elements, present only when a transcript path is
given, rather than baked as a literal into `prompt.bash` the way the
Python interpreter is.** This follows `BASH`'s own precedent in
`prompt.py` (also assembled into the argv list, not substituted into
the bash text) rather than `@dovetailPython@`'s (substituted directly
into `prompt.bash`). It also makes the "wrapper's argv carries the
baked recorder path" unit test this brief's verification plan asks for
possible to write against `prompt.wrapper_argv` directly, with no
package build in the loop — a test against a bash-text substitution
would need to inspect the built `prompt.bash`, not the Python module.
The two elements are appended only when a transcript path is given
(never as trailing empty strings) specifically so that an invocation
with no `--record` produces an argv byte-identical to 0010's, which is
what the brief's first unit-test bullet asks for.

**The child shell `script -c` runs the accepted line under is the same
bash binary the wrapper itself runs under, forced via `SHELL="$BASH"`.**
`script`'s manual says the `-c` command runs under `$SHELL`, falling
back to the Bourne shell if unset — and the resident's ambient `$SHELL`
could be anything, or unset, inside whatever terminal launched this
wrapper. Since `docs/run.md` already promises "a command written for
[bash's] syntax will be run by bash," letting `script` fall back to
`sh` under `--record` would quietter that promise specifically when
capture is on. Bash sets its own built-in `$BASH` variable to the exact
path used to invoke the running instance, which — because
`wrapper_argv` puts the baked `BASH` path first in the terminal's
argv — is exactly the same store path already running `prompt.bash`.
Setting `SHELL` to it, rather than to a second independently-baked
constant, guarantees the two can never drift apart.

**`script -qec` is invoked exactly as named in the brief, banner lines
and all — the transcript file also carries `script`'s own "Script
started on ... / Script done on ..." lines, which `-q` only suppresses
from the terminal, not from the file.** Confirmed empirically (`script
-qec 'echo hi' out.log` writes those two lines into `out.log` even
though nothing appears on the invoking terminal). There is no flag in
this version of `script` to suppress them from the file too, and the
brief specifies the mechanism (`script -qec`) rather than asking for a
clean transcript, so this is left as `script`'s own behavior rather
than post-processed away.

**The provenance recording notice is shown whenever `--record` is
given, independent of whether the resident goes on to accept, edit or
decline.** The brief's requirement is that "the resident must never
discover capture after the fact" — she has to learn about it before she
decides what to do at the prompt, not only when the interaction turns
out to be one that actually wrote a transcript. Tying the notice to
`--record` rather than to the eventual outcome is the only reading that
satisfies "never discover ... after the fact" for the decline case too.

**The record's field order places `transcript` immediately after
`exit_status`, before `from`/`why`.** The brief does not fix an order
beyond "the record gains one field." `docs/run.md` already explains
that the existing field order tells the story in the order it
happened: what was proposed, what ran, whether it was declined, how it
went. `transcript` is part of "how it went," alongside `exit_status`,
so it sits with that group rather than at the very end.

**The Nix check's new nonzero-exit-status case runs `sleep 3; exit 3`,
not a bare `exit 3`.** `run-prompt.nix`'s pty-terminal stand-in forwards
its forked child's own wait status as its own exit code, and
`prompt.bash` already `exit`s with the executed command's status — so
an instantly-exiting nonzero command makes the stand-in look, to
`dovetail-run`'s own no-compositor liveness watch
(`NO_COMPOSITOR_LIVENESS_BUDGET`, 2 seconds), exactly like a terminal
that died within the watch window, and `dovetail-run` fails the whole
invocation before the check ever gets to inspect the record. This is a
property of the check's own stand-in terminal, not of a real terminal
emulator, which does not exit when the command running inside it does.
The sleep clears the 2-second window so the check exercises what the
brief actually asks about (the record's `exit_status`), not the
liveness watch.
