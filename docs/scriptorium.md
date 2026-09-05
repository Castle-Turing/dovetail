# The scriptorium verb

`dovetail-scriptorium` builds a room for working through an idea. One
invocation gives you three things: a durable scratch file open in an
editor tile, a REPL beside it, and the editor's control socket printed
so that an agent can read what you are typing and — if you have asked it
to — write into the same buffer.

```
dovetail-scriptorium [--scratch-dir DIR] [--repl COMMAND]
                     [--terminal COMMAND] TOPIC
```

It prints exactly two lines on stdout, and nothing else:

```
socket /run/user/1000/dovetail/nvim-31337.sock
file /home/resident/.local/share/dovetail/scratch/2026-09-05-parser-rewrite.md
```

Two labelled lines rather than prose, because the first consumer of this
verb is an agent session that has to know which socket and which file
without guessing. Everything a person needs to be told — a window that
came out in the wrong place, a compositor that could not be reached —
goes to stderr, where it cannot be mistaken for either.

This is reference documentation for a stranger. You do not need to know
anything about Castle Turing to use the verb; you need Nix with flakes
enabled, a terminal emulator you tell Dovetail how to run, and Sway if
you want the two tiles arranged rather than merely opened.

## Trying it

```
nix run github:Castle-Turing/dovetail#dovetail-scriptorium -- \
  --terminal "foot -e" parser-rewrite
```

`nix run github:Castle-Turing/dovetail` with no attribute is still the
editor itself, as [`docs/module.md`](module.md) describes. Each verb is
its own executable: `dovetail` names the editor, and one word doing two
jobs is a defect rather than a convenience.

## The scratch file

The file is the point of the room. The windows are teardown — you close
them and they are gone — and the file is what is still there tomorrow.

### What it is called

`<YYYY-MM-DD>-<topic>.md`, with the date taken when you run the verb.
The date leads so that a directory listing sorts chronologically, which
is the order you will look for these in. Markdown because the room is
for prose first; pseudocode and Python live in fenced blocks, and the
REPL beside it is where code is actually run.

`TOPIC` is required and is validated as a slug: lowercase letters and
digits in hyphen-separated runs. `parser-rewrite`, `m2-layout` and
`0006` are topics; `Parser Rewrite`, `parser_rewrite`, `-notes` and
`two--hyphens` are not, and each is refused with a message that names
the rule and shows what you probably meant.

The refusal is deliberate and the suggestion is never silently used. A
caller who typed spaces wants to know what the file will be called *now*,
not to discover a guess three days later when they cannot find it. The
refusal happens before anything is started, so a mistyped topic costs
you a message rather than two windows to close.

### Where it lives

Four places are consulted, and the first that is set wins:

| Source | Meaning |
| --- | --- |
| `--scratch-dir DIR` | This invocation only. |
| `$DOVETAIL_SCRATCH_DIR` | Your standing choice. This is the private-layer slot. |
| `$XDG_DATA_HOME/dovetail/scratch` | The specification's data home. |
| `~/.local/share/dovetail/scratch` | What the specification says that means when it is unset. |

Unlike the terminal, this slot has a default rather than a refusal: a
resident who has configured nothing should still be able to type one
word and get a room. `$XDG_DATA_HOME` rather than `$XDG_STATE_HOME`
because the specification gives the state home logs-and-history
semantics, and these are durable documents you are expected to come back
to. An `$XDG_DATA_HOME` that is empty or not an absolute path is treated
as unset, as the specification requires, so a stray relative setting
falls through to the home default instead of scattering scratch
directories under whatever directory you happened to be in.

The scratch directory itself — the immediate parent of the file — is
created mode `0700` if missing, and the file `0600`. Any further-out
ancestor this also has to create (the `deep` in a
`DOVETAIL_SCRATCH_DIR=/data/deep/scratch`, say) gets the platform's
ordinary default for a new directory, umask included: `mkdir -p`
semantics apply the requested mode only to the leaf. That leaf is where
the resident's unfinished thinking actually lives, so it is the one
directory this is not willing to inherit a multi-user machine's umask
for.

> **Do not point this inside a flake-tracked tree.** Nix evaluation
> copies the tree it is given into the Nix store, which is
> world-readable, so a scratch directory inside one publishes every
> half-formed thought in it to every user on the machine. This is a
> mechanism, not a policy: nothing warns you, and deleting the file
> afterwards does not remove the store copy. Castle Turing's
> `docs/private-layer.md` documents it in full, and
> [`docs/vision.md`](vision.md) cites it as the inherited lesson that
> applies the moment a scratch directory is named.

### Reopening is a feature

If the file already exists, it is opened exactly as it is. Nothing is
truncated, nothing is clobbered, and not even the modification time
moves — the file is created with `O_CREAT` and no `O_TRUNC`, which does
nothing at all to a file that is already there. Typing the same topic
this afternoon reopens this morning's session, which is the intended
way to use the verb rather than an edge case it survives.

A new file is created empty. Dovetail never writes a line into your
scratch file; the first line is yours.

### Promoting one

There is no promote verb and there will not be one. When a scratch file
has earned a place in a repository, move it there yourself:

```
git mv ~/.local/share/dovetail/scratch/2026-09-05-parser-rewrite.md \
       ~/projects/thing/docs/research/parser-rewrite.md
git add -A && git commit
```

Promotion is a judgment about whether the thinking is finished, made
once per file, in a repository whose conventions Dovetail knows nothing
about. Automating it would mean Dovetail deciding where other people's
documents go.

## The two tiles

On the workspace you are looking at: the editor on the left, the REPL on
the right, side by side. No workspace numbers, no floating, no sizes —
you move and resize as you like, and the rule only puts two tiles
somewhere predictable.

The mechanism is worth knowing, because it explains the failure modes:

1. The editor is started in a terminal, with the scratch file already on
   its command line, and Sway is asked for its window tree until a
   window appears belonging to that terminal or one of its descendants.
2. That window is focused and given a horizontal split. This is the
   whole of the placement: Sway opens a new window as a sibling of the
   focused container, in the direction its parent is split, so the next
   window to map lands beside the editor. The editor is wrapped in a
   split of its own, and whatever else was on the workspace keeps the
   space it had.
3. The REPL terminal is started, and its window waited for the same way.
4. The tree is read back and checked: two tiles, one workspace, one
   horizontal split, editor first.

Placement is *asked for* rather than imposed afterwards, because every
command that moves a window after the fact produces a result that
depends on where the window happened to land — which is the kind of rule
that works on the machine it was written on. Asking the compositor to do
what it already does has no such dependency.

If the check fails, one correction is attempted and only one: if the two
tiles are siblings in a horizontal split but the wrong way round, they
are swapped. Every other way of coming out wrong needs a container
moved, and those are reported rather than guessed at.

**A misplaced tile is never a failure.** If the room is not arranged,
you get a line on stderr naming what actually happened — "they share a
container laid out `'splitv'`", "they ended up on different workspaces"
— and an exit status of 0. Both windows are open, which is what you
asked for; failing the invocation over placement would be worse than a
tile you can drag.

**A missing tile is a failure.** If either window never appears within
five seconds, the command fails and says which half is missing. Half a
room is not a room, and you asked for a worksession rather than for
whichever piece happened to start.

If no compositor can be reached at all — `$SWAYSOCK` unset, `swaymsg`
missing, or you are not on Sway — the two terminals are still started
and a line on stderr says they were not arranged. There is no window
tree to poll on that path, so each terminal is instead watched for two
seconds for an immediate death; a broken `$DOVETAIL_TERMINAL` still
fails loudly.

## The three slots

Nothing about your taste is compiled into Dovetail. Three settings, each
with a documented precedence.

### The terminal, which has no default

Dovetail does not know which terminal emulator you run and will not
guess one. Set `$DOVETAIL_TERMINAL` to the command that runs a program
in a new terminal window, as an **argv prefix**, parsed the way a shell
would parse it:

```
export DOVETAIL_TERMINAL="foot -e"
export DOVETAIL_TERMINAL="wezterm start --"
export DOVETAIL_TERMINAL="alacritty -e"
export DOVETAIL_TERMINAL="kitty --"
```

`$TERMINAL` is the fallback, and `--terminal` overrides both for one
invocation. If none is set the command fails and says so: a wrong
terminal is worse than a clear refusal.

### The REPL, which has one

`python3`, baked in at build time as an absolute store path from this
flake's own Nixpkgs. This slot has a default where the terminal does not,
and the difference is not arbitrary: Dovetail can build a Python and
hand you one hermetically, so refusing to would be withholding something
it is already holding. It cannot build your terminal emulator.

Override it with `$DOVETAIL_REPL`, or `--repl` for one invocation. Both
are argv, shell-quoted, because a REPL worth switching to usually has
arguments:

```
export DOVETAIL_REPL="ipython --no-banner"
dovetail-scriptorium --repl "python3 -q" parser-rewrite
dovetail-scriptorium --repl ghci type-checker
```

The REPL is a plain program in a terminal. Dovetail does not talk to it,
read from it, or send it anything — it is there because thinking in
Python beside your prose is the case M2 was built for, and a program you
can replace with `ghci` is a slot rather than a dependency.

### The editor

The packaged verb has this flake's own `dovetail` editor baked in as an
absolute store path. Set `$DOVETAIL_EDITOR` to override it — if your
private layer builds its own nixvim, you want your build launched, not
ours.

```
export DOVETAIL_EDITOR=/home/resident/.local/state/nix/profiles/editor/bin/nvim
```

## Co-editing: the recipe

The verb builds the room; it does not read your buffer. What follows is
the recipe an agent session uses once it holds the socket, written out
because it is the thing M2 exists for and because getting the quoting
wrong costs twenty minutes.

**All of this is Neovim-specific**, which is why it is a recipe in a
document rather than a feature of the verb. When M3 extracts the editor
contract, "read the buffer" and "write through the buffer" are two of
the verbs it will name, and this section is the evidence for what they
have to do. Until then, the calls below are the Neovim provider's, and a
tool that hardcodes them is betting on the provider.

Everything here was run against a live instance while this document was
written; the transcripts are the source of the claims below.

### Reading what the resident is typing, without waiting for a save

```
sock=...        # the socket line from stdout
file=...        # the file line from stdout
nvim="nvim --clean --headless --server $sock"

# The whole buffer, unsaved changes included:
$nvim --remote-expr \
  "join(nvim_buf_get_lines(bufnr('$file'), 0, -1, v:false), \"\n\")"

# Are there unsaved changes at all?
$nvim --remote-expr "getbufvar(bufnr('$file'), '&modified')"
```

`bufnr('<absolute path>')` is the buffer holding that file, or `-1` if
nothing has it open. Reading works while the resident is looking at some
entirely different buffer, so an agent never has to move her cursor to
find out what she wrote.

Two quoting traps, both of which will bite you once:

- **Single-quoted strings in Vimscript do not interpret escapes.**
  `join(..., '\n')` joins with a literal backslash-n. The separator must
  be double-quoted *inside the expression*, which is why the shell
  quoting above is arranged the way it is.
- `--remote-expr` prints the expression's value, and a Neovim API
  function that returns nothing prints `vim.NIL`. That is success, not
  an error.

### Writing through the buffer

```
$nvim --remote-expr \
  "nvim_buf_set_lines(bufnr('$file'), 1, 1, v:false, ['', '> a line from the agent'])"
```

The arguments are the buffer, a start line and an end line (zero-based,
end-exclusive — `1, 1` inserts before line 2 without replacing
anything), a strict-indexing flag, and the lines.

Three things are true of a write made this way, and all three were
checked:

1. It lands in the buffer, not on disk. The buffer is left modified and
   the resident's next `:w` is what writes it.
2. It joins the resident's undo history. One `u` in her window removes
   the agent's insertion — this is *shared undo*, which is the point of
   editing through the buffer rather than through the file, and also the
   reason it is dangerous.
3. Her cursor stays where it was.

### The rule about when you may do this

Never outside a worksession the resident explicitly entered.

This is the fifth of [`docs/vision.md`](vision.md)'s starting positions
and it is a hard rule, not a default. An agent that edits the buffer
someone happens to be looking at, uninvited, is the wrong-channel
failure the Castle Turing ecosystem exists to avoid, and shared undo
makes it worse rather than better: the resident's own `u` now walks
backwards through someone else's edits.

The room this verb builds is the explicit entry. Running
`dovetail-scriptorium` and handing an agent the socket is the resident
saying "we are working on this together". Nothing else is.

Ordinary edits — an agent changing a file it was asked to change — go to
disk, and the editor reloads. That is `docs/vision.md`'s fifth position
in the other direction, and it is the path almost every edit takes.

### The follow-up: events instead of polling

Reading the buffer as shown above is a *poll*. An agent that wants to
know the moment a line changes has to ask again.

[`docs/vision.md`](vision.md) says to try `nvim_buf_attach`'s change
events before settling for polling, and that position stands. It is not
implemented here for a plain reason: `--remote-expr` opens a connection,
evaluates one expression, prints the result and disconnects, so there is
nowhere for an event to be delivered to. Subscribing means a client that
stays connected — a persistent msgpack-RPC process, holding a
subscription, with its own lifecycle and its own failure modes. That is
a real shipped artifact, and it has no consumer until a co-editing
session actually wants one.

So it is deliberately not built. When a session demands it, the change
is a new capability behind the editor seam, and the first flag in the
optional-capability set M3's contract describes. Until then, poll, and
note how often you actually needed to.

## Options

| Option | Meaning |
| --- | --- |
| `TOPIC` | Required. A slug: lowercase letters and digits in hyphen-separated runs. |
| `--scratch-dir DIR` | Where the scratch file lives, for this invocation. |
| `--repl COMMAND` | The REPL to run beside the editor, shell-quoted argv. |
| `--terminal COMMAND` | Terminal argv prefix, overriding `$DOVETAIL_TERMINAL`. |

## Environment

| Variable | Meaning |
| --- | --- |
| `DOVETAIL_SCRATCH_DIR` | Where scratch files live. The private-layer slot. |
| `DOVETAIL_TERMINAL` | Argv prefix that runs a command in a new terminal window. No default. |
| `TERMINAL` | Fallback for the above. |
| `DOVETAIL_REPL` | The REPL to run beside the editor, overriding the build-time `python3`. |
| `DOVETAIL_EDITOR` | The editor to launch, overriding the build-time default. |
| `XDG_DATA_HOME` | Where the scratch directory defaults to living under. |
| `XDG_RUNTIME_DIR` | Where the editor announces its socket. Unset means no socket can be found; see [`docs/module.md`](module.md). |
| `SWAYSOCK` | Set by Sway. Unset means the tiles are opened but not arranged. |

## Timeouts, and what happens when they expire

| Wait | Bound | On expiry |
| --- | --- | --- |
| A tile's window appearing, when a compositor is reachable | 5 seconds | The command **fails**, naming which tile. Half a room is not a room. |
| A terminal's own liveness, when no compositor is reachable | 2 seconds | A terminal still running is presumed fine. One that exited nonzero fails the command, naming the status. |
| The editor publishing its socket | 10 seconds | The command fails, naming the scratch file and saying the windows are yours to close. |
| A single question to an instance | 5 seconds | That instance is treated as not answering. |

The socket is waited for **last**, after both windows are up, because it
is the longest of the waits and the room is already usable while it
happens.

## A worked example

You are an agent session and the resident wants to think through a
parser rewrite with you:

```
$ dovetail-scriptorium parser-rewrite
socket /run/user/1000/dovetail/nvim-31337.sock
file /home/resident/.local/share/dovetail/scratch/2026-09-05-parser-rewrite.md
```

Two tiles appear. You keep both lines. She writes three paragraphs and
does not save; you read them:

```
sock=/run/user/1000/dovetail/nvim-31337.sock
file=/home/resident/.local/share/dovetail/scratch/2026-09-05-parser-rewrite.md
nvim --clean --headless --server "$sock" --remote-expr \
  "join(nvim_buf_get_lines(bufnr('$file'), 0, -1, v:false), \"\n\")"
```

She tries something in the REPL tile, pastes the traceback into the
file, and asks you to sketch the alternative underneath it. Because she
asked, you write into the buffer, and because you wrote into the buffer
rather than the file, her `u` undoes you as easily as it undoes herself.

Tomorrow morning she types `dovetail-scriptorium parser-rewrite` and
gets a *new* file — the date leads the name. To carry on with
yesterday's, she names yesterday's topic in the same session, or opens
the file with [`dovetail-show`](show.md). When it is finished she
`git mv`s it into the project's `docs/`.

Teardown is closing the windows. There is no daemon, no state file, no
registry and no cleanup verb; the editor removes its own socket on a
clean exit, and the scratch file stays, which is the whole point of it.

## Known limitations

**Sway is the only compositor.** That is a real limit, not a temporary
one. The seam is
`tools/dovetail-seams/src/dovetail_seams/compositor.py`, where one class
answering six things — which window has focus, which window belongs to a
process I just started, float this one, focus this one, split this one
horizontally, swap these two — is the whole of what another compositor
would have to supply. No verb outside that file writes a line of Sway
command syntax.

**Focus is assumed to stay put between the two launches.** Placement
works by focusing the editor's window and splitting it, then letting the
REPL's window map beside it. If something takes focus in that
window — you click another window, a notification steals it — the REPL
can land somewhere else. The tree is read back afterwards, so you are
*told*; you are not silently left with a room you did not ask for.

**A terminal that daemonizes will not be found.** The window wait
matches on the process id of the command spawned, or any descendant, so
a terminal that forks or re-execs before mapping is fine. A client that
hands the request to an *already-running server* — `footclient`,
`kitty @ launch`, `wezterm connect` — produces a window belonging to a
process that is no relation. For `show` that costs a floating window;
here it costs the whole invocation, because a window that never appears
is indistinguishable from a tile that failed to open. Name the
standalone binary in `$DOVETAIL_TERMINAL`.

**`/proc` is a Linux interface.** Matching windows to the processes that
own them reads the process table from `/proc`. On a system without one,
no window is ever matched and the launch cannot be confirmed.

**The REPL and the editor do not know about each other.** There is no
shared kernel, no send-region-to-REPL, no variable inspection. Two tiles
that happen to be next to each other is the whole of it, and generalising
past that is what [`docs/vision.md`](vision.md) calls the rooms
mechanism and declines to build.

## What `nix flake check` proves

Three of the flake's checks bear on this verb, and none of them needs
hardware or hands:

- **`seams-unit`** — the machinery shared with `dovetail-show`: the
  terminal, editor and REPL slots and their precedence, the process
  table, and the compositor's bounded wait for a new window.
- **`scriptorium-unit`** — this verb's own rules as pure functions. The
  scratch file convention: the name built from a supplied date, every
  shape of topic that is refused and the suggestion each refusal makes,
  all four steps of the directory chain including the relative
  `$XDG_DATA_HOME` the specification says to ignore, and that an
  existing file survives byte-identical with its modification time
  untouched. The layout rule: a room that came out right, and each way
  of coming out wrong — a lost window, a floating tile, two workspaces,
  tiles that are not siblings, a vertical or tabbed split, and the one
  case worth swapping. And the order the steps run in: that a misplaced
  tile warns and exits 0, that a missing tile fails, and that a bad
  topic or an unset terminal starts no process and creates no file.
- **`scriptorium-room`** — the verb end to end against a real editor.
  The sandbox has no Wayland session, so the terminal slot is filled
  with `env` and the editor slot with a headless wrapper, which is the
  same code path `foot -e` takes. It asserts that the scratch file is
  created where the convention says with the name it says and empty;
  that stdout is exactly the two labelled lines; that the socket
  answers and the instance listening on it has *that* file loaded; that
  content written into the buffer and saved survives a second
  invocation on the same topic byte-for-byte, and that the reopened
  buffer holds it; that a topic which is not a slug is refused with a
  suggestion and leaves no file behind; and that the scratch directory
  is mode 0700.

The two-tile layout itself cannot be checked in the Nix sandbox, which
has no compositor. That is the checklist below.

## Confirming it by hand

Five steps on a real Sway desktop. Five minutes.

1. **Set your terminal**, if you have not already:
   `export DOVETAIL_TERMINAL="foot -e"` — yours, not necessarily that
   one. Then run `dovetail-scriptorium parser-rewrite`.
2. **Look at the room.** Two tiles, side by side, editor on the left,
   REPL on the right, on the workspace you were already on. The editor
   holds an empty file named for today and your topic. Two lines were
   printed; the paths in them are real.
3. **Check the REPL is a REPL.** Type `2 + 2` in the right-hand tile.
   Then close both windows — that is the entire teardown — and confirm
   the scratch file is still there.
4. **Reopen this morning's session.** Write a line in the editor tile,
   save, close both windows, and run `dovetail-scriptorium` with the
   *same* topic. The same file comes back with your line in it, and the
   printed `file` path is identical to the first run's.
5. **Try the co-editing recipe.** With the room open, type a line and
   *do not save it*. From another terminal, run the
   `nvim_buf_get_lines` command from the recipe above with the printed
   socket and file. You should see the unsaved line. Then run the
   `nvim_buf_set_lines` command, watch the text appear in the tile you
   are looking at, and press `u` — your undo should remove it.

Step 5 is the one to pay attention to. It is the mechanism the entire
milestone is built on, and the moment where "the agent can edit what I
am looking at" stops being an abstraction. If it makes you uneasy, that
is the correct response, and it is why the rule about explicit
worksessions is a rule.
