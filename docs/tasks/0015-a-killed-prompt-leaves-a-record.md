Title: A killed prompt leaves a record
Milestone: m3-done
Model: standard
Requires: 0012-the-record-carries-a-transcript
Requires-because: it adds a third way `write_record` gets called from `prompt.bash`, alongside the cleared-line and end-of-input paths 0010 built and the transcript-cleanup logic 0012 added to that same function; there is nothing to extend until both exist.

# 0015 — A killed prompt leaves a record

Promotes `docs/backlog/a-killed-prompt-leaves-no-record.md`, per the
backlog lifecycle in `docs/backlog/README.md`: the same commit that
adds this brief deletes the backlog file. Its text survives in git
history and in this brief's own retelling below.

Read first, in this order: `AGENTS.md`; `docs/run.md` as tasks 0009,
0010 and 0012 left it; `docs/vision.md`'s M3 section;
`tools/dovetail-run/src/dovetail_run/prompt.bash` and `record.py` —
this task changes the first and calls the second exactly as it is
already called, adding no new fields; `nix/checks/run-prompt.nix` and
`nix/checks/run-prompt-terminal.py` for the check this task extends.

## The gap

`dovetail-run --record PATH` writes a record for every ending the
wrapper's own code reaches: accepted, edited, declined by clearing the
line, and end of input (task 0010), and a `script` setup failure
(task 0012). It writes nothing for the ending `docs/run.md` already
documents as possible — "Ctrl-C at the prompt runs nothing either; it
takes the window with it without a word" — because bash's default
disposition for `SIGINT` is to terminate the process immediately, and
nothing in `prompt.bash` traps it. The same is true of the window
dying outright: closing a terminal window ordinarily delivers `SIGHUP`
to the foreground process group of the pty it owned (a kernel/tty-driver
behavior, not something a specific terminal emulator has to implement),
and that is untrapped too.

The consequence is exactly what the backlog entry names: a caller
polling `PATH` cannot tell "the resident is still deciding" from "the
prompt is gone", and is left guessing at a human's pace with a timeout
— the gap the record exists to close, reopened on its most common form
of refusal.

## Resolving the backlog's open questions

**Is a killed prompt a fourth outcome, or is `declined` the honest
word for it?** `declined` stays the word, and no field is added. The
record's `declined` field is already overloaded past "the resident
typed nothing": task 0012 folded a `script` setup failure into
`declined: true` with the explicit note that this is "imprecise ...
but there is no true exit status to report." A killed prompt is the
same shape of case — nothing ran, there is no executed line, no exit
status, and no transcript — and the record already has no way to
distinguish *why* an existing decline happened (cleared line, end of
input, and a `script` failure are three shades of the same boolean
today). Adding a fourth ending as a distinct schema value would fix
that ambiguity only for this one new case while leaving the other
three exactly as underspecified as before, at the cost of a schema
change every existing reader of the record has to learn. Keep the
boolean; extend the field's prose description in `docs/run.md` with
one more bullet, matching the pattern the `script`-failure case
already set.

**Should the wrapper also write an "opened" marker?** No — out of
scope for this task, and not clearly needed at all. `dovetail-run`
itself already reports "the prompt is on screen" synchronously: per
`docs/run.md`, "Zero means the prompt is on screen," and a terminal
that fails to open is already a loud, non-zero exit naming why (task
0007's launch-failure contract, reused here). A caller that gets exit
status 0 from `dovetail-run` already knows the prompt appeared, before
it ever starts polling `PATH` for the record; a marker file would only
duplicate information the verb already hands back synchronously at
launch time. If a future caller turns out to need "the prompt was
shown" to survive past the verb's own process (e.g. a supervisor that
launched `dovetail-run` and then lost its own exit status), that is a
new problem with a different shape than this one, and belongs in its
own backlog entry rather than folded into a fix for the killed-prompt
gap.

**What does the reference terminal actually send its child when its
window is closed?** Verified by reasoning rather than assumed: closing
a terminal emulator's window ends the process holding the master side
of the pty, which closes that file descriptor; the kernel's own tty
driver then delivers `SIGHUP` to the foreground process group of the
slave side. This is standard POSIX terminal behavior implemented by
the kernel, not by the specific emulator — `foot`, `wezterm`, or any
other terminal built on a normal pty gets this from the OS for free,
so trapping `SIGHUP` covers "the window disappeared" regardless of
which terminal the resident named. What genuinely varies by emulator
is whether it *additionally* sends its child a signal of its own
before or instead of relying on the kernel's hangup (some process
supervisors send `SIGTERM` to a child group on shutdown); trapping
`SIGTERM` as well costs one more line and closes that variation too.
`SIGKILL` cannot be trapped by anything running in the process it
targets — see Non-goals.

## The fix

`prompt.bash` traps `INT`, `HUP` and `TERM` for exactly the window
during which the resident is looking at an undecided prompt: armed
before the provenance block is printed, disarmed the instant `read -e
-i` returns, for any reason (accepted, edited, or end-of-input — all
three already have their own decline/accept handling right after
`read` returns, untouched by this task). A signal received before the
prompt is drawn, or while `read` is blocked waiting on the resident, is
caught; a signal received after acceptance, while the command itself
is running, is not — that is a killed *command*, and the existing
`write_record` call after the command finishes already reports it
correctly (bash reports 128+signal as the exit status of a
signal-terminated foreground pipeline, so a rebuild killed with Ctrl-C
mid-run already ends up with, e.g., `exit_status: 130` in today's
record — nothing to fix there).

The trap handler calls the same `write_record true "" "" ""` the
cleared-line and end-of-input paths already call — no new arguments,
no new call shape — so the stale-transcript cleanup and the
`finished_at` timestamp `write_record` already computes apply
identically to a killed prompt. `proposed` is unaffected, since it was
already known before the prompt was drawn; there is no way to recover
whatever partial edit was on the readline buffer at the moment of the
signal (bash's `read` does not expose a partial line on interruption),
so `executed` stays `null`, consistent with every other declined case.

After writing the record, the handler resets the trapped signal's
disposition to default and re-raises the same signal against the
wrapper's own PID, rather than calling `exit` with a fixed status —
this is the standard idiom for "a script wants to run cleanup on a
signal but still die exactly as if it hadn't caught it," and it means
a killed prompt still ends the wrapper's process the same way it does
today (which is what closes the window, since the wrapper runs as the
terminal's direct child with nothing between them): a caller inspecting
the wrapper's own wait status — if anything ever does — still sees a
real signal death, not a fabricated exit code.

The traps are installed unconditionally, not only when `--record` was
given. `write_record` already no-ops with an empty `record_path`, so
an invocation with no `--record` runs the same handler, writes
nothing, and re-raises exactly as before — no behavioral difference
from today. Installing them unconditionally means the killed-prompt
code path is exercised (and can regress a check) whether or not
`--record` is in play, rather than only in the flag's own branch.

## Non-goals

- **No schema change.** `declined`, `executed`, `exit_status` and
  `transcript` all mean exactly what they already mean; a killed
  prompt sets them exactly as a cleared-line decline does. No `reason`
  field, no fourth top-level state.
- **No "opened" marker file.** See above.
- **No handling for signals received once a command is running.**
  Already correctly reported through the command's own exit status;
  widening this task to touch that path would be following the
  backlog off a cliff it does not describe.
- **`SIGKILL` is out of reach at this layer, and belongs at a
  different layer if it matters.** No process can trap or clean up
  after its own `SIGKILL`; if a resident's environment routinely kills
  windows this way (an OOM killer, a compositor that force-kills on a
  timeout), no amount of wrapper code can leave a record — the only
  way to observe that ending at all is an external supervisor
  independently watching whether the process is still alive, which is
  a different mechanism entirely (a liveness watch, not a record) and
  a different backlog entry if it turns out to be needed. This task
  does not build that.
- **No change to the provenance block, the sanitization, or the launch
  path.** Scope stays the wrapper's signal handling and nothing else,
  the same bound tasks 0010 and 0012 held themselves to.

## Documentation

`docs/run.md` currently states, twice, that Ctrl-C "takes the window
with it without a word" — once in the "Decline it" section and once in
the record section ("One ending the wrapper cannot act on writes
nothing: Ctrl-C takes the window with it without a word"). Both need
correcting: with this task, the wrapper *can* act on it. Add a fourth
bullet to the `declined` field's description alongside the cleared-line,
end-of-input, and `script`-setup-failure cases already listed, naming
Ctrl-C, the window closing, and the wrapper being sent `SIGTERM` while
the prompt is still up as the same ending. State plainly that without
`--record`, none of this is observable — the window still closes
silently, because there is nowhere to write anything to.

## Verification plan

Agent-testable, no human involved:

- `run-prompt-terminal.py` gains a way to end the interaction with a
  signal instead of a keystroke: closing the pty master file
  descriptor immediately once the prompt is drawn, instead of typing
  anything, produces a genuine kernel-delivered `SIGHUP` on the slave
  side — the real mechanism a closed terminal window relies on, not a
  simulation of it — and a direct `os.kill(pid, signal.SIGTERM)` at the
  same point covers the case a specific emulator sends its own signal.
  `SIGINT` needs no change to the stand-in at all: typing the literal
  INTR byte (`\x03`) into the pty, exactly like the existing `\x15`
  (Ctrl-U) case already does, exercises the real kernel line-discipline
  path that generates `SIGINT` for a real terminal too.
- Extend `nix/checks/run-prompt.nix` with three new cases (Ctrl-C,
  early master-close, direct `SIGTERM`), each under `--record`: the
  wrapper's own process ends, a record appears at the polled path
  (reusing the existing wait-for-capture-file pattern, since the
  record is written before the wrapper's process fully exits) with
  `declined: true` and `executed`, `exit_status`, `transcript` all
  `null`, and no `.tmp` file survives the atomic rename. One case
  reuses a `--record PATH` that already holds a transcript from an
  earlier accepted proposal at the same path, to confirm the killed
  path also clears a stale transcript exactly as the other decline
  paths already do.
- A case without `--record`: the same three signals still end the
  wrapper (no change in observable behavior), and no file appears
  anywhere.
- `nix flake check` green.

Genuinely needs human hands: one line added to `docs/run.md`'s by-hand
checklist — close a real floating window (Ctrl-C, or closing it with
the mouse) on a real Sway desktop with `--record` given, and confirm
the record appears. This is a cross-check that the reference terminal's
actual behavior matches the kernel-`SIGHUP` path already proven in the
sandbox, not a load-bearing part of the fix — the sandbox check does
not depend on it to be meaningful.

## Housekeeping

This brief is `docs/tasks/0015-a-killed-prompt-leaves-a-record.md`.
Commit it on your branch exactly as you received it, header lines
included, and append a "Judgment calls made during implementation"
section recording every decision you made where this brief was
ambiguous. That section is part of the deliverable.

## Judgment calls made in writing this brief

This brief was authored without implementing it, on explicit
instruction from the dispatch that assigned this task — a departure
from `docs/tasks/README.md`'s usual "committed on the branch that
implements it" rule, which this file does not otherwise question.
Judgment calls made while turning the backlog entry into this spec:

**The backlog's three open questions are resolved above rather than
left for the implementer.** The dispatch instructions asked for every
ambiguity in the entry to be recorded; the entry's own "Open questions"
section is exactly that ambiguity, so resolving it in the brief (with
the reasoning kept next to the decision) is what "recording" means
here, rather than restating the questions unanswered and pushing the
decision downstream.

**`SIGTERM` was added to the trapped set even though neither the
backlog entry nor `docs/run.md` names it.** The entry's own framing —
"what a compositor-closed window actually delivers to a child process
is terminal-emulator-dependent" — is itself the argument for trapping
one more signal that costs nothing to also catch: a terminal or
supervisor that sends `SIGTERM` directly, rather than relying on the
kernel's hangup-on-close, is exactly the variation the entry warned
about, and there is no plausible case where a wrapper sitting at an
undecided prompt should treat a `SIGTERM` differently from a `SIGINT`.

**The traps are scoped to the read-prompt window only, not the whole
script.** The backlog entry's title and body both say "a killed
*prompt*", and `docs/run.md` already correctly reports a killed
*command*'s exit status (128+signal) through the ordinary post-command
`write_record` call. Widening the trap to cover command execution too
would either duplicate that already-correct reporting or race with it
(the trap firing while `script`/`eval` is still finishing), and the
entry gives no reason to touch that path.

**No new field for "how the no was said."** Recorded above under
"Resolving the backlog's open questions" rather than repeated here;
flagged again because it is the single largest interpretive call in
this brief and the one most likely to be revisited if a future
consumer of the record turns out to care.

**This brief does not amend `docs/state/MILESTONE.md`'s `[m3-done]`
clause to name task 0015.** That clause currently lists the merged
tasks that satisfy it (0009, 0010, 0012); this brief is not yet
implemented, and adding an unimplemented task to a "done looks like"
clause would misstate current truth. The PR that implements this brief
is the one that should decide whether `[m3-done]` needs a patch, per
`docs/state/README.md`'s same-PR rule.
