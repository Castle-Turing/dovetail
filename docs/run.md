# The run verb

`dovetail-run` puts a command in front of you. It opens a terminal
showing who proposed the command and why, above a prompt line already
filled in with the command itself — editable, and **not executed**.
Nothing runs until you press Enter.

```
dovetail-run [--from NAME] [--why TEXT] [--terminal COMMAND]
             [--no-float] [--record PATH] COMMAND
```

It prints nothing when it works. The command's own output belongs to
the window it opens, not to whoever invoked the verb.

This is reference documentation for a stranger. You do not need to know
anything about Castle Turing to use the verb; you need Nix with flakes
enabled, Sway if you want the window floated, and a terminal emulator
you tell Dovetail how to run.

## Trying it

```
nix run github:Castle-Turing/dovetail#dovetail-run -- \
  --from "an agent session" --why "the flake needs rebuilding" \
  "nixos-rebuild switch --flake .#castle"
```

`nix run github:Castle-Turing/dovetail` with no attribute is still the
editor itself, as [`docs/module.md`](module.md) describes. Each verb is
its own executable: `dovetail` names the editor, and one word doing two
jobs is a defect rather than a convenience.

`COMMAND` is one positional argument — the exact shell line you would
type. Quote it as one argument; anything you leave unquoted is your
shell's, not Dovetail's.

## What you see

Four comment lines and a prompt:

```
# dovetail-run: a command has been proposed for you. Nothing has run yet.
# Proposed by: an agent session
# Why: the flake needs rebuilding
# Press Enter to run it, edit the line first, or clear it to decline.

$ nixos-rebuild switch --flake .#castle
```

The cursor is at the end of that line, and the line is a real readline
line: arrow keys, word motions, kill and yank all work, because it is
bash's `read -e` with the proposal seeded into it. Three things you can
do with it, and none of them is the default:

**Run it.** Press Enter. The command runs exactly as displayed.

**Edit it first.** Change anything you like and then press Enter. What
runs is what the line says at that moment — the proposal has no
privileged status once you have started typing.

**Decline it.** Clear the line (Ctrl-U) and press Enter: nothing runs,
the window says the line was cleared, and it closes. Ctrl-C at the
prompt runs nothing either; it takes the window with it without a word.
Either way the verb has no way to tell you apart from someone who ran
it: this is your prompt, not a dialog box with a default answer.

Ctrl-D declines too, but only once the line is empty. With text on the
line, readline binds Ctrl-D to "delete the character under the cursor",
which is what a shell does and not something Dovetail overrides.

After a command runs, its exit status is printed and the window waits
for one more Enter before closing. A terminal that vanishes on the
command's last line of output is a command whose output nobody read.

Nothing is written to any history file. Your shell history belongs to
your shell, and a one-shot prompt appending to it uninvited would put a
command you may never have run into the record you later grep.

## Why it does not just run the command

Because watching a command run teaches what is going on under the hood,
and being told a command ran teaches nothing. That is Castle Turing's
comprehension principle: in the domains you want to grow in, the posture
is doing rather than being shown. The proposing agent still closes the
loop afterwards by checking what the command was supposed to change —
never by asking you whether you ran it.

**There is no `--just-run`, and there will not be one until an authority
taxonomy exists to grant it.** That is a refusal, not an oversight.
Watch-and-run-yourself, agent-runs-with-report and agent-runs-silently
are rungs of a competence-gated ladder, and a flag that skips to the top
of it would be the whole hazard this verb is shaped around.

That hazard has a name: a pre-populated command habitually Entered is
the confirmation problem with your privileges attached. Three properties
hold it off, and they are the design rather than decoration — the line
is genuinely editable, the provenance is always printed, and what is
displayed is what runs.

### Provenance is always printed

`--from` names the proposer and `--why` says why. Leave either out and
the block still prints, saying so:

```
# Proposed by: unattributed — nothing named the proposer
# Why: not stated
```

An honest nag, not a blank. A command from nobody, for no stated reason,
is exactly the one to read twice.

## What is refused

Both the command and the `--from` / `--why` text are checked before
anything is opened, and a character that can make the drawn line differ
from the executed one is **refused, never repaired**:

| Refused | Why |
| --- | --- |
| C0 controls (`U+0000`–`U+001F`), including tab and newline | A terminal draws none of them as themselves. Escape starts a sequence that can rewrite what is already on screen; carriage return draws over it; tab is whitespace of unpredictable width; a newline is an Enter nobody pressed. |
| `U+007F` DELETE and the C1 range (`U+0080`–`U+009F`) | Some terminal encodings still parse these as control functions rather than showing them. |
| The Unicode bidirectional controls: `U+061C`, `U+200E`, `U+200F`, `U+202A`–`U+202E`, `U+2066`–`U+2069` | They reorder what is drawn without changing a byte of what runs. This is the trick the "Trojan Source" class of attacks is built on. |
| `U+2028` and `U+2029`, the line and paragraph separators | A terminal or pager may break the line at one, putting half the command where you are not looking. |
| The zero-width characters `U+00AD`, `U+200B`, `U+FEFF` | They occupy no width at all: `rm /tmp<U+200B>x` reads as one path and runs as another. |
| An empty or whitespace-only command | There is nothing to propose, and an empty prompt under a provenance comment says nothing about what was meant. |

Each refusal names the character, gives its Unicode code point and its
offset in the string (counted in characters, from zero), and says which
argument it was in:

```
dovetail-run: the command contains U+202E RIGHT-TO-LEFT OVERRIDE, at offset 12
```

The verb exits non-zero and opens nothing. Repairing the string instead
would hand you a command nobody wrote, running with your privileges,
with no sign that it happened.

Two characters that look like they belong on that list are deliberately
allowed: the zero-width joiner and non-joiner (`U+200D`, `U+200C`). They
are load-bearing inside ordinary text — an emoji sequence in a commit
message is the obvious case — and they hide nothing that is not already
visible beside them.

**A newline being refused means there are no multi-line commands.** If
you have three commands, that is three invocations, or one line joined
with `&&`. This is a real limitation and a deliberate one: a proposal
you can read in a single line is one you can check before pressing
Enter.

## The launch path

The prompt runs inside a terminal, and the terminal is yours to name.
Dovetail does not know which terminal emulator you run and will not
guess one:

```
export DOVETAIL_TERMINAL="foot -e"
export DOVETAIL_TERMINAL="wezterm start --"
```

The setting is an **argv prefix**, parsed the way a shell would parse
it, and the prompt is appended to it as further argv elements — so no
shell sits between the verb and the prompt, and nothing you passed is
reinterpreted on the way in. The resolution chain is exactly
`dovetail-show`'s, including the declarative file for sessions that
inherit no environment: `--terminal`, then `$DOVETAIL_TERMINAL`, then
`$XDG_CONFIG_HOME/dovetail/terminal` (falling back to
`~/.config/dovetail/terminal`), then `$TERMINAL`. Nothing set anywhere
in that chain is a refusal rather than a guess.
[`docs/show.md`](show.md#the-terminal-is-yours-to-name) documents it in
full; a private layer managed with home-manager writes the file
declaratively:

```nix
xdg.configFile."dovetail/terminal".text = "foot -e";
```

The shell that runs the prompt is *not* a slot. It is the bash this
flake built, baked in as an absolute store path, because the prompt is
bash's `read -e -i` and a shell that cannot run it cannot hold the slot.

### Floating, and confirming the window opened

After spawning the terminal, `dovetail-run` asks Sway for its window
tree until a window appears belonging to the terminal it started or one
of its descendants, and issues `floating enable` for it. This is the
same machinery `dovetail-show` uses, with the same reasoning, and
[`docs/show.md`](show.md#floating-without-configuring-your-compositor)
is where it is explained.

The wait is the launch confirmation, not the floating: it runs whether
or not `--no-float` was given. A window that has not appeared within
five seconds is a warning on stderr and nothing more. A terminal that
*exited* instead of mapping a window is a failure — nothing opened, so
nobody was asked anything — and the diagnostic names the command and its
exit status.

With no compositor reachable at all, there is no tree to poll, so the
spawned terminal is watched for two seconds instead. A terminal that
exits nonzero inside that window fails the invocation; one still running
is presumed fine.

**A prompt that cannot be displayed never runs.** If the terminal
command hands the prompt no terminal — a stand-in that runs its
arguments in the background, say — the prompt refuses with exit status
2 rather than reading a proposal from a pipe, and the verb reports that
as a failed launch. The promise is that you read the line; a line nobody
could read does not get to run.

### What the verb's exit status means

Zero means the prompt is on screen. It does **not** mean the command
ran, and it never carries the command's own exit status: whether you run
it, edit it or decline it is yours to decide after the verb has
returned. An agent that proposed the command closes the loop by looking
at what the command was supposed to change.

## The record

`--record PATH` is how the agent that proposed a command closes the
loop without asking anyone whether it ran: the delta between what was
proposed and what was actually typed is the correction signal Castle
Turing's evidence ranks above a rating, and this is where Dovetail keeps
it.

Given `--record PATH`, `dovetail-run` writes one JSON object to `PATH`
once the interaction ends, for every ending the verb can act on:
accepted, edited, declined by clearing the line, and end of input. Two
endings the wrapper cannot act on write nothing: Ctrl-C takes the window
with it without a word (see above), and a line that ends the wrapper's
own process — one ending in a bare `exit`, or using `exec` — hands
control to `exit`/`exec` before the wrapper's own next line ever runs.

```json
{
  "proposed": "nixos-rebuild switch --flake .#castle",
  "executed": "nixos-rebuild switch --flake .#castle --show-trace",
  "declined": false,
  "exit_status": 0,
  "transcript": "/var/lib/castle/records/nixos-rebuild.json.transcript",
  "from": "an agent session",
  "why": "the flake needs rebuilding",
  "proposed_at": "2026-09-06T22:14:03Z",
  "finished_at": "2026-09-06T22:14:41Z"
}
```

The fields:

| Field | Meaning |
| --- | --- |
| `proposed` | The command as proposed, verbatim. |
| `executed` | The line actually run, verbatim; `null` if declined. |
| `declined` | Whether the resident cleared the line or hit end of input instead of running anything. |
| `exit_status` | The executed command's exit status; `null` if declined. |
| `transcript` | Path to the transcript file beside the record (see [The transcript](#the-transcript)); `null` if declined. |
| `from`, `why` | The provenance, exactly as given to `--from`/`--why`; `null` when neither was passed. |
| `proposed_at`, `finished_at` | ISO 8601 UTC timestamps: when the prompt was shown, and when this record was written. |

It is JSON, not the `Key: value` lines the rest of this document favors,
because a shell command can contain any text at all, and the record has
to carry it without ambiguity.

The file is written via a temporary file in the same directory, then an
atomic rename, so a poller either finds no record yet or finds a whole
one — never one that is half-written. Without `--record`, none of this
happens: no file is written and nothing else about the verb changes.

If `PATH`'s parent directory does not exist, `dovetail-run` refuses
before opening any terminal, naming the path — creating directories on
your behalf would be a guess about your layout this verb has no
business making.

This verb writes the file and nothing more. `dovetail-run` returns as
soon as the prompt is on screen, long before the record exists — the
resident may take an hour to press Enter — so a caller that wants the
outcome polls for the file rather than waiting on the verb itself.
Anything past that, such as a castle seat filing the record into its own
journal, is the caller's business in the caller's repository; it is not
this verb's concern.

### The transcript

The record's own fields say *that* a command ran and *what its exit
status was*. They say nothing about what happened on screen while it
ran — and an exit status of 0 is not the same claim as "this did what it
was supposed to". The incident that prompted this feature was exactly
that gap: a rebuild the resident ran appeared to succeed while having
silently done nothing, and the agent that proposed it had no way to see
what she saw.

So, only when `--record PATH` is given, the accepted line runs under a
pty recorder — `script -qec` — instead of directly. The command still
believes it has a real terminal, so progress bars, prompts and color
survive exactly as they would without `--record`; everything drawn to
that terminal is also captured to a transcript file beside the record,
named `PATH` with `.transcript` appended (`record.json` gets
`record.json.transcript`).

The transcript is its own file, not a field in the JSON record: a
rebuild's output can run to megabytes, and the record has to stay a
small thing a poller reads cheaply. What the record carries is one
field, `transcript`, naming the file — or `null` when nothing was
captured, which is any declined interaction: a cleared line or end of
input closes the window without running anything, so there is nothing
to record.

**Ordering is the contract.** The record is written — atomically, as
above — only after the command has finished and its transcript is
complete. A poller that waits for the record and then reads the file
`transcript` names never finds a partial transcript; by the time the
record exists, `script` has already exited.

**The exit status is still the command's own.** `script -e` (folded
into `-qec`) hands back the child's exit status rather than
substituting its own, so `exit_status` in the record means exactly what
it means without `--record`, including when it is nonzero.

**Unechoed input is not captured.** A pty transcript contains what the
terminal actually drew — which is to say, what was echoed. A program
that disables terminal echo before reading a secret, the way a password
prompt does, never has those keystrokes appear in the transcript,
because they were never drawn in the first place; `script` cannot
record what the terminal itself never showed.

**The resident is told up front.** The provenance block gains a fifth
line whenever `--record` is given — "This session's output is being
recorded for the proposing agent." — printed before the prompt, so
capture is never something she discovers after the fact.

## Options

| Option | Meaning |
| --- | --- |
| `--from NAME` | Who is proposing the command. Shown above the prompt; absent means "unattributed". |
| `--why TEXT` | Why it is being proposed. Shown above the prompt; absent means "not stated". |
| `--terminal COMMAND` | Terminal argv prefix for this invocation, overriding the environment and the terminal file. |
| `--no-float` | Leave the new window wherever the compositor puts it. |
| `--record PATH` | Write a JSON record of what was proposed and what actually ran to `PATH` once the interaction ends, and capture the accepted command's own terminal output to a transcript beside it. See [The record](#the-record) and [The transcript](#the-transcript). Omit to write nothing. |

## Environment

| Variable | Meaning |
| --- | --- |
| `DOVETAIL_TERMINAL` | Argv prefix that runs a command in a new terminal window. No default. |
| `XDG_CONFIG_HOME` | Where the declarative terminal file (`dovetail/terminal`) is looked for, before falling back to `~/.config`. |
| `TERMINAL` | Fallback if none of the above resolves to a terminal. |
| `SWAYSOCK` | Set by Sway. Unset means there is no window tree to poll, and the terminal's own liveness is watched instead. |

## Timeouts, and what happens when they expire

| Wait | Bound | On expiry |
| --- | --- | --- |
| A new window appearing after a launch, when a compositor is reachable | 5 seconds | No window was seen; a warning goes to stderr. Exit status is still 0. A terminal that exited instead fails the command regardless of this wait. |
| A spawned terminal's own liveness, when no compositor is reachable | 2 seconds | A terminal still running is presumed fine; exit status is 0. A terminal that exited with a nonzero status inside the window fails the command, naming that status. |

Nothing waits for the resident. She may read the provenance block, go
and make coffee, and press Enter an hour later; the verb returned long
before.

## Known limitations

**One line, one command.** A newline is refused with the rest of the
control characters, so a proposal is always a single line. Join with
`&&` or propose twice.

**The prompt is bash.** `read -e -i` is a bash feature and the wrapper
is a bash script. Your login shell is irrelevant — the prompt runs the
bash this flake built — but a command written for another shell's syntax
will be run by bash, so write the line you would type into `sh`.

**No record, and no transcript, unless you ask for one.** Without
`--record`, the prompt is transient: the window closes and nothing
remembers what was proposed, what ran, or what it printed. See
[The record](#the-record) and [The transcript](#the-transcript).

**A terminal that daemonizes will not be floated.** Same as
`dovetail-show`, for the same reason: a client that hands the request to
an already-running server — `footclient`, `kitty @ launch` — produces a
window belonging to a process that is no relation. The prompt still
opens. Naming the standalone binary in `$DOVETAIL_TERMINAL` avoids it.

**Sway is the only compositor the floating step knows.** It is behind
its own seam in the source
(`tools/dovetail-seams/src/dovetail_seams/compositor.py`); this verb
uses only "make that window float".

## What `nix flake check` proves

Three of the flake's checks bear on this verb, and none of them needs
hardware or hands:

- **`run-unit`** — the refusals, as pure functions: every refused class
  of character named by code point, the offset reported in characters
  rather than bytes, the first offending character being the one
  reported, ordinary commands with quotes, backslashes, non-ASCII text
  and joined emoji passing through byte-identical, the empty command,
  the provenance block with and without `--from` and `--why`, and the
  argv the terminal is handed. Also that every refusal spawns nothing at
  all.
- **`run-prompt`** — the prompt itself, under a pseudo-terminal, which
  is the only place `read -e -i` can be checked rather than asserted.
  The terminal slot is filled with a stand-in that allocates a pty, runs
  what it is given, types a prepared key sequence, and writes down every
  byte the prompt drew. Four cases: Enter on the pre-filled line runs
  exactly the proposed command; an edited line runs the edit; a cleared
  line runs nothing and says it declined; and a terminal that provides
  no tty runs nothing and fails the invocation. The first two also strip
  the escape sequences out of the transcript and assert that the line
  *drawn on the screen* is byte-equal to the command that ran — the
  verb's one promise, checked the only way it can honestly be checked.
  The same three interactive cases are also run with `--record`: the
  accepted line's record has `proposed == executed`, the edited line's
  has `proposed != executed`, the declined case's has `executed` and
  `exit_status` both `null`, a fourth proposal made with no `--record`
  writes no file at all, and a final check over everything this run
  wrote confirms no temporary file from the atomic rename is left
  behind. Three more cases prove the transcript: an accepted command
  with distinctive output produces a transcript file containing it and
  a record whose `transcript` field names that file, alongside the
  provenance block having said recording was active; a nonzero exit
  status in the record is the command's own rather than the recorder's;
  and a declined line under `--record` leaves `transcript: null` in the
  record and no transcript file on disk.
- **`run-launch-failure`** — the launch path on the no-compositor branch
  the sandbox always is: `--terminal false` fails the whole invocation
  and names the command and its status, `--terminal true` is left alone,
  and each refusal exits non-zero *before* the terminal is spawned,
  proven with a stand-in terminal that records having been started.

What the sandbox cannot show is a real compositor floating a real
window, and the feel of the line under your own fingers. That is the
checklist below.

## Confirming it by hand

Five steps on a real Sway desktop. Three minutes.

1. **Set your terminal**, if you have not already:
   `export DOVETAIL_TERMINAL="foot -e"` — your terminal, not necessarily
   that one.
2. **Propose something harmless**:
   `dovetail-run --from "me" --why "checking the verb" "ls -la /tmp"`.
   A floating window should appear with the provenance block and the
   pre-filled line, and **nothing should have run**. Press Enter: the
   listing appears, then the exit status, then the window waits for
   another Enter.
3. **Edit before running**: propose `echo one` and, at the prompt, use
   Ctrl-A, arrow keys and Backspace to make it `echo two` before
   pressing Enter. `two` is what should appear.
4. **Decline**: propose anything, press Ctrl-U to clear the line, and
   press Enter. The window should say the line was cleared and that
   nothing was run, and close.
5. **Watch a genuinely interactive command under `--record`**: something
   with a progress bar or a color-coded status (`nixos-rebuild switch
   --flake .#castle`, or anything similar you have on hand) proposed
   with `--record /tmp/run-check.json`. The provenance block should say
   the session is being recorded, and the command should behave exactly
   as it does without `--record` — colors, cursor movement and progress
   bars all working normally. If the command prompts for a sudo
   password, type it: the prompt itself should appear in
   `/tmp/run-check.json.transcript` afterwards, and the password you
   typed should not.
