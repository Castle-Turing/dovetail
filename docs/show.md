# The show verb

`dovetail-show` puts a named file in front of you. If you are looking at
an editor, the file opens in *that* editor; if you are not, a new one is
launched as a floating window you can move wherever you like.

```
dovetail-show [--line N] [--socket PATH] [--terminal COMMAND]
              [--no-float] [--print-socket] FILE
```

It prints nothing when it works, unless you asked for `--print-socket`.

This is reference documentation for a stranger. You do not need to know
anything about Castle Turing to use the verb; you need Nix with flakes
enabled, Sway if you want the focused-window half of the rule, and a
terminal emulator you tell Dovetail how to run.

## Trying it

```
nix run github:Castle-Turing/dovetail#dovetail-show -- notes/today.md
```

`nix run github:Castle-Turing/dovetail` with no attribute is still the
editor itself, as [`docs/module.md`](module.md) describes. Each verb is
its own executable: `dovetail` names the editor, and one word doing two
jobs is a defect rather than a convenience.

## The targeting rule

Three steps, in order. The first that yields a live instance wins.

**One: the caller said so.** If `--socket PATH` is given, or
`$DOVETAIL_SOCKET` is set, that instance is used. An agent session that
launched an instance itself already knows which one it means, and
ambient discovery would be a guess replacing a fact the caller holds.

The named socket is connected to and verified before it is used. If it
does not answer, the command fails and names the path — a caller that
named a dead socket wants to hear about it, not to have a different
editor silently substituted.

**Two: the focused editor.** The compositor is asked which window has
focus, and the Dovetail instances running inside that window are found:

1. `swaymsg -t get_tree` is walked for the node with `focused` true, and
   its process id taken. That process id belongs to the *terminal
   emulator*, not to the editor — the editor is typically several
   levels below it.
2. The process table is read from `/proc`, and every descendant of the
   focused process is collected, each with its depth below the window.
3. Those process ids are intersected with the sockets in
   `$XDG_RUNTIME_DIR/dovetail/`, whose names are `nvim-<pid>.sock`.
4. Survivors are ranked **deepest first**, so an editor running inside
   another editor's `:terminal` wins over its host. Candidates at equal
   depth are ranked by **highest process id**, which is arbitrary but
   total: the answer never depends on directory listing order.
5. Each candidate in rank order is connected to and asked a question.
   The first that answers is used.

That last step is not ceremony. A crash leaves a socket file behind, and
the process id in its name may by then belong to something else
entirely; `docs/module.md` requires connect-and-verify of every
consumer, and this is where the requirement is implemented.

If the compositor cannot be reached at all — `$SWAYSOCK` unset,
`swaymsg` missing, `swaymsg` failing — that is **not an error**. It
means no focused editor was found, and the rule falls through.

**Three: launch one.** No live instance inside the focused window means
you are not looking at an editor, so one is made, floating.

## The launch path

The editor is started inside a terminal, with the file already on its
command line. Nothing waits for a socket: the socket appears
asynchronously, some way into the editor's startup, so opening the file
by connecting to it afterwards would be a race with no benefit. Only
`--print-socket` needs the socket, and only there is it waited for.

### The terminal is yours to name

Dovetail does not know which terminal emulator you run and will not
guess one. Set `$DOVETAIL_TERMINAL` to the command that runs a program
in a new terminal window, as an **argv prefix**, parsed the way a shell
would parse it. The editor invocation is appended to it:

```
export DOVETAIL_TERMINAL="foot -e"
export DOVETAIL_TERMINAL="wezterm start --"
export DOVETAIL_TERMINAL="alacritty -e"
export DOVETAIL_TERMINAL="kitty --"
```

`$TERMINAL` is the fallback if `$DOVETAIL_TERMINAL` is unset, and
`--terminal` overrides both for one invocation. If none of the three is
set, the command fails and says so; there is no hardcoded default,
because a wrong terminal is worse than a clear refusal.

### The editor is a build-time default with a runtime override

The packaged `dovetail-show` has this flake's own `dovetail` editor
baked in as an absolute store path. Set `$DOVETAIL_EDITOR` to override
it — if your private layer builds its own nixvim, you want your build
launched, not ours.

```
export DOVETAIL_EDITOR=/home/resident/.local/state/nix/profiles/editor/bin/nvim
```

### Floating, without configuring your compositor

You do not have to add a `for_window` rule to your Sway config. After
spawning the terminal, `dovetail-show` asks Sway for its window tree
until a window appears whose process id is the terminal it just started
or one of that terminal's descendants, and then issues `floating enable`
for that container.

It asks repeatedly rather than subscribing to window events, and that is
not laziness. `swaymsg -t subscribe` never reports the subscription
being established: it consumes Sway's reply and prints only events, in
both raw and pretty modes. So a caller cannot know when it is listening,
and a window mapped before it is has no second chance. A tree that is
polled has no such gap — the window is either there or not there yet —
and each ask is one round trip over a local socket.

Matching on process id rather than application id is deliberate. An
application-id rule would make you carry the flag that *sets* the
application id in your terminal setting, and every terminal spells it
differently — `--app-id` for foot, `--class` for alacritty and kitty.
Process id keeps your private configuration down to "how I start a
terminal".

If the window is not seen within five seconds, the window is left where
the compositor put it and a warning goes to stderr. The file is open,
which is what you asked for; failing the whole invocation over placement
would be worse than a slightly misplaced window. `--no-float` skips only
the `floating enable` call, never this wait: the wait is what confirms
the launch actually produced something, not just the floating, so a
tiled launch gets the same failure detection as a floating one, at no
cost when everything goes right. With `--no-float`, a window that simply
has not appeared yet within the five seconds is still just a warning —
worded as "no window was seen" rather than "could not float", since
nothing asked to float it.

One case is distinguished from that, because it is not cosmetic: if the
terminal command *exited* rather than mapping a window, nothing opened
at all, and `dovetail-show` fails and says so with the exit status
instead of reporting a placement problem. This applies whether or not
`--no-float` was given.

### Without a compositor

If no compositor is reachable at all — `$SWAYSOCK` unset, `swaymsg`
missing — there is no window tree to poll, so `dovetail-show` instead
watches the spawned terminal itself for two seconds. A terminal that
exits within that window, with a nonzero status, fails the invocation
and names the exit status, the same as a terminal that exits instead of
mapping a window on the compositor path above. A terminal still running
when the two seconds are up is presumed fine: the watch exists to catch
a terminal that fails immediately — a broken `$DOVETAIL_TERMINAL`, bad
arguments — not to prove that the editor will ever produce a visible
result, which this path has no way to check at all.

## Options

| Option | Meaning |
| --- | --- |
| `--line N` | Put the cursor on line N. `+N` on the command line for a launched instance, the equivalent over RPC for an existing one. |
| `--socket PATH` | Use the instance listening on PATH. Step one of the rule. |
| `--terminal COMMAND` | Terminal argv prefix for this invocation, overriding `$DOVETAIL_TERMINAL`. |
| `--no-float` | Leave a launched window wherever the compositor puts it. |
| `--print-socket` | Print the socket of the instance the file was shown in. |

## Environment

| Variable | Meaning |
| --- | --- |
| `DOVETAIL_SOCKET` | The instance to use, exactly as if `--socket` had been given. |
| `DOVETAIL_TERMINAL` | Argv prefix that runs a command in a new terminal window. No default. |
| `TERMINAL` | Fallback for the above. |
| `DOVETAIL_EDITOR` | The editor to launch, overriding the build-time default. |
| `XDG_RUNTIME_DIR` | Where instances announce themselves. Unset means no instance is discoverable; see `docs/module.md`. |
| `SWAYSOCK` | Set by Sway. Unset means step two of the rule finds nothing. |

## Timeouts, and what happens when they expire

Four waits are bounded, and each expiry has a defined outcome rather
than a hang.

| Wait | Bound | On expiry |
| --- | --- | --- |
| A single question to an instance | 5 seconds | That instance is treated as not answering, and ranking moves to the next candidate. |
| A new window appearing after a launch, when a compositor is reachable | 5 seconds | The window is left tiled, and a warning goes to stderr. Exit status is still 0. Runs whether or not `--no-float` was given; a terminal that exited instead fails the command regardless of this wait. |
| A spawned terminal's own liveness, when no compositor is reachable | 2 seconds | A terminal still running is presumed fine; exit status is 0. A terminal that exited with a nonzero status inside the window fails the command, naming that status. |
| A launched instance publishing its socket, for `--print-socket` only | 10 seconds | The command fails with exit status 1, saying that the file was opened but no socket appeared. The file is open regardless. |

## A worked example

You are an agent session that wants the resident to read a brief, at the
paragraph you are talking about:

```
dovetail-show --line 42 /home/resident/castle/docs/tasks/0007-digest.md
```

If she is looking at an editor, the brief appears in it at line 42. If
she is reading mail, a new floating editor appears with the brief in it.

If you have launched an instance yourself and want every later call to
land in it:

```
sock=$(dovetail-show --print-socket /home/resident/scratch/notes.md)
dovetail-show --socket "$sock" --line 12 /home/resident/scratch/notes.md
```

or set `DOVETAIL_SOCKET="$sock"` once and stop passing `--socket`.

## Known limitations

**A terminal multiplexer defeats step two.** An editor running under
tmux or screen is a child of the multiplexer *server*, not of the
terminal that displays it, so it is not a descendant of the focused
window and will not be found. The rule falls through to launching a new
instance — wrong, but not harmful. Use `--socket` or `$DOVETAIL_SOCKET`
if you work this way.

**A terminal that daemonizes will not be floated.** The floating step
matches the window against the process id of the command it spawned, or
any descendant of it, so a terminal that forks or re-execs before
mapping is still found. A client that hands the request to an
*already-running server*, though — `footclient`, `kitty @ launch`,
`wezterm connect` — produces a window belonging to a process that is no
relation, and the command itself exits right away, so the wait gives up
as soon as that exit is seen rather than running to the full timeout;
the window is left tiled. The file still opens. Naming the standalone
binary in `$DOVETAIL_TERMINAL` avoids it.

**Sway is the only compositor step two knows.** That is a real limit,
not a temporary one: `swaymsg` is the only compositor query implemented.
It is behind its own seam in the source (`compositor.py`), where a class
answering three questions — which window has focus, which window belongs
to a process I just started, make that window float — is the whole of
what another compositor would have to supply.

**`/proc` is a Linux interface.** Step two needs the process tree, and
reads it from `/proc`. On a system without one, the rule falls through
to step three.

**`show` opens files; it does not change them.** Editing *through* a
live buffer belongs to the co-editing worksessions of M2, which a
resident enters deliberately. An agent that edits the buffer you happen
to be looking at, uninvited, is the wrong-channel failure this ecosystem
exists to avoid.

## What `nix flake check` proves

Three of the flake's checks belong to this verb, and none of them needs
hardware or hands:

- **`show-unit`** — the targeting rule as a pure function. It takes a
  Sway tree as parsed JSON, a process table snapshot, a socket listing
  and a predicate standing in for connect-and-verify, and returns a
  target. The cases asserted are the editor in the focused terminal; two
  editors where the deeper one wins; a tie broken by process id; a stale
  socket naming a process that is not there; a stale socket whose
  process id has been reused by something that does not answer; a
  focused window with no editor under it; an unreachable compositor; and
  the multiplexer-shaped case above, which asserts the fall-through
  rather than hoping for it. These run in the package's own check phase.
- **`show-explicit-socket`** — step one of the rule end to end. A
  headless instance is launched on some *other* file, so that a buffer
  arriving is evidence of the verb rather than of the launch; then
  `dovetail-show --socket` is asserted to load the file, `--line` to
  place the cursor, `--print-socket` to print the socket and nothing
  else, and a socket that does not answer to fail loudly, name itself,
  and leave the live instance untouched.
- **`show-launch-failure`** — the launch path's failure detection on the
  no-compositor branch, which the sandbox is *always* on, since it has no
  Wayland session: `--terminal false` fails the whole invocation and
  names the command and its exit status, and `--terminal true` (a
  stand-in for a terminal that daemonizes and exits 0 immediately) is
  left alone.

The rest of step two and three — a real compositor placing and floating
a window — cannot be checked in the Nix sandbox, which has no Wayland
session. That is the checklist below.

## Confirming it by hand

Five steps on a real Sway desktop. Two minutes.

1. **Set your terminal**, if you have not already:
   `export DOVETAIL_TERMINAL="foot -e"` — your terminal, not necessarily
   that one.
2. **With no editor focused** (a browser or a terminal will do), run
   `dovetail-show ~/notes.md`. A new editor window should appear
   **floating**, with `notes.md` in it.
3. **Click that editor window to focus it**, then run
   `dovetail-show --line 5 /etc/hostname` from another terminal. The
   file should appear **in that same editor**, cursor on line 5, with no
   new window.
4. **Check the fall-through**: focus a window that is not an editor and
   run `dovetail-show ~/notes.md` again. A second floating editor should
   appear rather than the file landing in the first.
5. **Check the refusal**: run
   `dovetail-show --socket /nonexistent.sock ~/notes.md`. It should
   print a diagnostic naming `/nonexistent.sock`, exit non-zero, and
   open nothing anywhere.
