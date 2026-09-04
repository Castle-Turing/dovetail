Title: The show verb
Milestone: M1

# 0002 — The show verb

Dovetail's first verb, and the half of M1 that makes the project useful:
one invocation puts a named file in front of the resident. If an editor
is focused, the file opens in *that* editor; otherwise a new editor is
launched as a floating window the resident can move wherever she likes.

This brief also settles the second half of the vision's first open
question — instance discovery — which task 0001 deliberately left to
whichever consumer first needed the answer. This is that consumer.

Everything in `docs/vision.md` applies; read it first, along with
`docs/module.md` (the socket scheme this builds on) and `AGENTS.md`.
In particular: public mechanism, private configuration — no terminal
emulator, no colorscheme, no workspace number and no path of anybody's
is hardcoded here — and documentation written for a stranger on
hardware that is not ours.

**Commit this brief.** Your first commit on the branch writes this file
to `docs/tasks/0002-show-verb.md`, reconstructing the header as
`Title: The show verb` and `Milestone: M1` only. The `Model:` line is
harness routing, not repository content, and does not belong in the
committed file. If the design shifts while you implement, amend the
brief in the same pull request rather than leaving it describing a
design nobody built.

## Deliverables

1. **`dovetail-show`**, a command-line tool: `dovetail-show [--line N]
   [--socket PATH] [--no-float] [--print-socket] FILE`. It opens `FILE`
   in an editor by the targeting rule below, and prints nothing on the
   happy path unless `--print-socket` is given.
2. **The targeting rule**, implemented as specified below and written
   so that its decision function is testable without a compositor.
3. **The launch path**, including the floating-window arrangement and
   the private-layer slot for the terminal command.
4. **Packaging**: the tool is a `packages.dovetail-show` output of the
   flake, runnable as `nix run .#dovetail-show`, with its unit tests
   wired into `nix flake check` alongside the existing three checks.
   Leave `packages.default` as the editor; `nix run github:...` is a
   documented entry point and must keep meaning what `docs/module.md`
   says it means.
5. **`docs/show.md`**: reference documentation for a stranger — the
   rule, the environment variables, the limitations, and a worked
   example using placeholder paths (`/home/resident/...`).
6. **Vision amendment**, in this same branch: mark the instance
   discovery question settled under the vision's open questions, the
   way task 0001 recorded the socket-path half, and note where the
   rule is documented.

## The targeting rule

Three steps, in order, with the first that yields an instance winning.

**One: the caller said so.** If `--socket PATH` is given, or
`$DOVETAIL_SOCKET` is set, use it. An agent session that launched an
instance itself already knows which one it means, and ambient discovery
would be a guess replacing a fact the caller holds. Verify it answers
before using it, and fail loudly naming the path if it does not — a
caller that named a dead socket wants to hear about it, not to have a
different editor silently substituted.

**Two: the focused editor.** Ask the compositor which window has focus,
find the Dovetail instances running inside it, and use the innermost
one. Concretely:

- `swaymsg -t get_tree`, walk the tree for the node with `focused` true,
  and take its `pid`.
- That process id belongs to the *terminal emulator*, not to Neovim.
  Confirmed by measurement on the operator's machine (2026-09-03): the
  focused node reported `app_id: "foot"` and a process id belonging to a
  foot process, with the editor four levels below it. So build the
  process tree from `/proc/<pid>/stat` — field 4 is the parent process
  id, and the executable name in field 2 can contain spaces and
  parentheses, so parse after the last `)` — and collect every
  descendant of the focused process.
- Intersect those process ids with the sockets in
  `$XDG_RUNTIME_DIR/dovetail/`, whose names are `nvim-<pid>.sock`.
- Rank surviving candidates by depth, deepest first, so a Neovim running
  inside another Neovim's `:terminal` wins over its host. Ties below
  that are broken by highest process id, so the rule is total and
  documented rather than dependent on directory order.
- Connect to each candidate in rank order and verify it answers before
  using it. A crash leaves a socket file behind whose process id may by
  then belong to something else entirely; `docs/module.md` already
  requires connect-and-verify of every consumer, and this is where that
  requirement gets its first implementation.

If the compositor cannot be reached at all — `$SWAYSOCK` unset,
`swaymsg` missing or failing — that is not an error. It means no focused
editor was found, and the rule falls through to step three.

**Three: launch one.** No live instance inside the focused window means
the resident is not looking at an editor, so make one, floating.

## The launch path

Launch the editor inside a terminal, as a floating window, with the file
already on its command line. Passing the filename as an argument avoids
waiting for the socket entirely: the socket appears *asynchronously*
after the process starts — measured, a listing taken immediately after
spawning found no directory at all — so a spawn-then-connect
implementation would race. Only `--print-socket` needs the socket, and
only there do you poll for it, bounded, with a stated timeout and a
stated behaviour when it expires.

**The terminal is private configuration.** Dovetail must not know that
this operator runs foot. Read the launch command from `$DOVETAIL_TERMINAL`
(overridable with `--terminal`), treat it as an argv prefix parsed with
`shlex.split`, and append the editor invocation as trailing arguments —
so `DOVETAIL_TERMINAL="foot -e"` and `DOVETAIL_TERMINAL="wezterm start --"`
both work without Dovetail knowing either. Fall back to `$TERMINAL` if
`$DOVETAIL_TERMINAL` is unset. If neither is set, fail loudly, naming
both variables and showing an example — never guess a terminal, and
never fall back to a hardcoded one.

**The editor is a build-time default with a runtime override.** Bake the
flake's own `dovetail` editor package in as the default, overridable by
`$DOVETAIL_EDITOR`, because a resident whose private layer builds its
own nixvim wants her build launched, not ours.

**Floating, without requiring compositor configuration.** Subscribe to
Sway's window events *before* spawning (`swaymsg -t subscribe -m
'["window"]'`), spawn the terminal, then read events until one reports a
new window whose `pid` matches the spawned child, and issue
`swaymsg '[con_id=<id>] floating enable'`. Doing it by process id rather
than by application id keeps the private-layer slot down to "how I start
a terminal": an application-id rule would have to carry the flag that
sets it, which foot spells `--app-id`, and alacritty and kitty spell
`--class`. Bound the wait; on timeout, leave the window tiled and warn
on stderr — the file is open, which is what the caller asked for, and
failing the whole invocation over placement would be worse than a
slightly misplaced window. `--no-float` skips this step.

## Talking to an editor

Use Neovim's msgpack-RPC, but do not hand-roll a client: shell out to
`nvim --server <socket> --remote-expr` and `--remote`, as
`nix/checks/headless-socket.nix` already does, with `neovim-unwrapped`
supplying the client so the tool does not depend on the configuration it
is opening files in.

**Isolate every one of those calls in a single module** — one file whose
job is "this is how the Neovim provider implements the verbs" — and say
so in a comment at its head. The vision's fourth starting position makes
the editor a slot rather than a hardcode, and M3 extracts the contract
from what M1 and M2 actually called. That extraction is much easier if
the Neovim-specific code already sits behind one seam. The rest of the
tool must not know what protocol the editor speaks.

`--line N` opens at a line: `+N` on the command line for a launched
instance, and the equivalent over RPC for an existing one.

## Considered and rejected

**Ranking instances by recency of use.** A Unix socket's mtime is set
when the server binds it, so ranking by mtime is "oldest instance wins"
wearing a disguise. Honest recency would mean the nixvim module
recording focus events into a variable that discovery reads back, which
is new module state in a task that does not otherwise need any.

**Matching the focused window by application id instead of process id.**
Requires the private layer to carry the flag that sets the application
id, which every terminal spells differently, and breaks for any editor
launched by a means the operator did not annotate.

**A single `dovetail` command with `show` as a subcommand.** The name
`dovetail` is already the runnable editor package documented in
`docs/module.md`, and a word doing two jobs in one project is a defect
by `AGENTS.md`'s naming rule. One executable per verb, so M2's
worksession verb is a sibling rather than a subcommand of something that
also means "the editor".

**A placement rule for tiling the new window.** Settled by the operator
(2026-09-03): float it, and let her move it. This is why the brief
contains no workspace, split direction or tile-reuse policy.

## Known limitations, to be documented rather than solved

A terminal multiplexer defeats step two: Neovim under tmux or screen is
a child of the multiplexer *server*, not of the terminal that displays
it, so it is not a descendant of the focused window and will not be
found. The rule falls through to launching a new instance, which is
wrong but not harmful. Document it in `docs/show.md` as a known
limitation. Do not solve it in this task.

Sway is the only compositor step two knows. That is acceptable for M1 —
the vision's ecosystem runs Sway — but write the compositor query behind
its own small seam too, so a stranger on another compositor has an
obvious place to add one.

## Non-goals

- No worksession, no REPL tile, no scratch files — all M2.
- No editor contract document, no provider slot as a module interface,
  no Emacs stub — all M3, extracted from this and M2, never imposed on
  them.
- No editing *through* a live buffer. `show` opens files; it does not
  change them.
- No daemon, no state file, no instance registry. The socket directory
  plus the process table is the whole of the state, and it is enough.

## Verification plan

Agent-testable, no human involved:

- Unit tests over the decision function, which must take the Sway tree
  as parsed JSON, a process table snapshot, and a socket listing, and
  return a target — pure, no subprocesses. Cover at minimum: the editor
  in the focused terminal; two editors where the deeper one wins; a
  stale socket whose process id is not in the tree; a focused window
  with no editor under it; an unreachable compositor; and the
  multiplexer-shaped case where the editor exists but is not a
  descendant, asserting that it falls through to launch.
- An end-to-end check in the Nix sandbox for the explicit-socket path:
  start a headless instance from the flake's editor, run `dovetail-show
  --socket <path> note.md`, and assert over RPC that the buffer is
  loaded and, with `--line`, that the cursor is on the requested line.
  `nix/checks/headless-socket.nix` is the model to follow.
- `nix flake check` passes with the new checks wired in, and the
  existing three still pass.

Genuinely needs human hands, because the Nix sandbox has no Wayland
session: opening a file into a focused editor on a real Sway desktop,
and confirming that a launch with no editor focused produces a floating
window with the file in it. Write that as a short numbered checklist at
the end of `docs/show.md` — five steps at most, each with the command to
run and what should happen — so the operator can walk it in two minutes
rather than reconstructing it.

## Report your judgment calls

Where this brief was ambiguous and you had to choose, say so in the pull
request description — those reports have repeatedly surfaced real
defects in the thing being specified. The choice of timeout values, the
exact tie-break when two candidates sit at equal depth, and what
`--print-socket` does when the socket never appears are all places the
brief states an intent without fixing a number.
