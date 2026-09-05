Title: The launch path, as it behaves on a real desktop
Milestone: M1

# 0005 — The launch path, as it behaves on a real desktop

Task 0002's verification plan said which steps needed human hands and
why: the Nix sandbox has no Wayland session, so steps two and three of
the rule — the focused-editor targeting and the floating launch — could
only be confirmed on a running compositor. Walking that checklist
(2026-09-04, Sway 1.12, foot) found the targeting rule correct and the
launch path broken in two ways, neither of which any check in the
repository could have caught.

The reuse path needs no changes and got none: with an editor focused,
`dovetail-show --line 42 README.md` put the file into that instance at
the right line with no new window, and the fall-through and both refusal
paths behaved as documented.

## Defect one: the floating step could never work

Every launch printed `could not float the new window` and left the
window tiled.

The floating step subscribed to Sway's window events before spawning the
terminal, and — as of task 0004's review round — waited for Sway to
acknowledge the subscription before returning, so that a window mapped
in the gap could not be missed. That acknowledgement does not exist.
`swaymsg -t subscribe` consumes Sway's reply itself and prints only
events, in **both** raw and pretty modes; measured directly against Sway
1.12, the first payload on the stream is an ordinary `window` event and
no `{"success": true}` ever arrives. The wait therefore either read an
event and rejected it as a malformed reply, or timed out — and in both
cases tore the subscription down, so nothing was ever watching.

The race the acknowledgement was meant to close is real, and the fix
removes the need for it rather than trying again. **The window tree is
polled instead of subscribed to.** After spawning, `dovetail-show` asks
`swaymsg -t get_tree` every tenth of a second, up to the same five-second
budget, for a window whose process id belongs to the terminal it
started. A polled state has no establishment gap: the window is either
in the tree or is not there yet, and asking again costs one round trip
over a local socket.

Two smaller things fall out of the rewrite. The match now accepts the
spawned process *or any descendant of it*, re-read on each attempt, so a
terminal that forks or re-execs before mapping is still found; the
process set cannot be computed once up front because those descendants
do not exist when the wait begins. And `window_for_pids` is a pure walk
over a tree it is handed, so every shape a real tree takes — nested
under workspaces, already floating, no windows at all, no tree because
the compositor could not be reached — is testable with no compositor.

The five-second budget bounds the whole wait rather than each attempt.
That distinction is not pedantry: a `get_tree` that hangs would
otherwise receive a fresh query timeout of its own, and a wait that
began just under the deadline could run to roughly twice the documented
budget while the resident waits for a window they were promised in five
seconds. Each query and each sleep is clamped to what is left. (Found by
the gate on this pull request.)

**Considered and rejected: speaking Sway's IPC protocol directly.** A
subscription made over `$SWAYSOCK` does get a real reply, and would
allow a genuine acknowledgement. It means implementing the binary
message framing and holding a socket open, which is a great deal more
code for a question — "has this window appeared yet" — that a poll
answers exactly. Worth revisiting only when something needs a *stream*
of compositor events rather than one state change.

## Defect two: the editor inherited the caller's pipes

The launched terminal was started with `start_new_session=True` but with
its standard streams left alone, so it inherited whatever the caller
had. Two failures followed, both measured:

- A caller that reads the tool's output **blocks until the editor window
  is closed**, because the terminal is still holding the write end of
  the pipe. An invocation that piped output hung for two minutes and
  completed the instant the window was closed by hand.
- A caller that gives up first **kills the editor**. The first instance
  launched during the walkthrough died when its pipe was torn down,
  while an otherwise identical launch with output redirected to a file
  survived.

The primary consumer of this verb is an agent session capturing output,
so both of those are the normal case rather than an exotic one. The
child now gets `stdin`, `stdout` and `stderr` on `/dev/null`: the editor
is a window, and nothing should be reading its pipe. The new session was
already correct and stays.

Silencing the child's stderr costs one thing, and the poll pays it back.
A terminal that starts and then exits — bad arguments, a missing font,
a configuration error — used to leave a warning on the caller's stderr;
now it would leave nothing. So when no window appears within the budget,
the child is checked: if it has exited non-zero, that is not a placement
problem but a file that never opened, and `dovetail-show` fails with the
terminal's exit status rather than printing a cosmetic warning and
returning success.

## Verification plan

Agent-testable, and done:

- Unit tests for `window_for_pids` over every tree shape (nested,
  floating, absent, no tree at all) and for `wait_for_window` (already
  present, appears later, pids re-read between attempts, times out),
  with the clock and sleep injected so the suite does not wait.
- Unit tests asserting the spawn puts all three standard streams on
  `/dev/null` and keeps `start_new_session`, and that a terminal which
  exits without mapping a window raises rather than warns.
- `nix flake check` passes, including the packaged `show-unit` and
  `show-explicit-socket` checks.

Needs human hands, because the sandbox still has no compositor — and
this task exists because that gap is where both defects lived:

1. With no editor focused, `dovetail-show <file>` must produce a
   **floating** window with the file in it. This is the step that failed
   before; it is the reason this brief exists.
2. Capture the output — `dovetail-show <file> | cat` — and confirm the
   command returns immediately rather than blocking until the window is
   closed.
3. Confirm the editor outlives the shell that launched it.
4. Re-walk the rest of `docs/show.md`'s checklist, which passed before
   and must still pass.
