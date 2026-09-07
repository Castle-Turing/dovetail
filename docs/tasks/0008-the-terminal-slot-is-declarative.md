Title: The terminal slot is declarative

# 0008 — The terminal slot is declarative

Groundwork for the run verb. The backlog entry
`docs/backlog/an-agent-cannot-hand-the-resident-a-command.md` (which
task 0009 promotes, not this one) records the incident: an agent
session had a command ready and no terminal to put it in, because
terminal resolution is environment-only and agent sessions do not
inherit the resident's interactive environment. A variable exported in
a shell rc never reaches a session spawned by a harness or a service
manager. The entry asks for the gap to be fixed once, declaratively,
for both verbs; this task is that fix.

Read first: `AGENTS.md`, `docs/vision.md`, the backlog entry above,
and `terminal_argv` in
`tools/dovetail-seams/src/dovetail_seams/launch.py` — the one function
this task changes. `docs/show.md` ("The terminal is yours to name")
and `docs/scriptorium.md` describe the current contract.

## The fix

`terminal_argv` gains one resolution step. The chain becomes, first
match wins:

1. `--terminal` (unchanged),
2. `$DOVETAIL_TERMINAL` (unchanged),
3. **new:** the file `$XDG_CONFIG_HOME/dovetail/terminal`, falling
   back to `~/.config/dovetail/terminal` when `$XDG_CONFIG_HOME` is
   unset — its content parsed as the same shell-quoted argv prefix
   the environment variables carry,
4. `$TERMINAL` (unchanged),
5. else the existing refusal, which now also names the file path it
   looked for, so the error message teaches the declarative slot.

Why the file sits below `$DOVETAIL_TERMINAL` but above `$TERMINAL`:
the file is Dovetail-specific and deliberately written, so it beats an
ambient, generic `$TERMINAL` that a desktop environment may have set
to something that is not an argv prefix; but an explicitly set
`$DOVETAIL_TERMINAL` is a session-scoped choice the resident or agent
made over their own standing configuration, and overrides it.

Semantics, matching the existing treatment of the environment
variables:

- A file that does not exist: the chain moves on, silently.
- A file that exists but is empty or whitespace-only: the chain moves
  on, as an empty environment variable does.
- A file with malformed shell quoting: refuse, naming the file path —
  `split_argv` already takes a name for exactly this.
- A file that exists but cannot be read (permissions, I/O error):
  refuse loudly, naming the path and the error. A present-but-broken
  configuration is a fact the resident wants to hear, not skip.
- Content is read as one argv prefix; a trailing newline is tolerated.

This is public mechanism, private configuration: the file is the slot,
its value is taste. The private layer writes it however it likes — a
home-manager `xdg.configFile."dovetail/terminal".text = "foot -e";`
is the one-line declarative form worth showing in the docs. Dovetail
ships no Nix option for it; the documented path is the whole
contract.

Both verbs get this automatically, because both resolve the terminal
through `terminal_argv`. Do not widen the change: the editor and REPL
slots keep their existing resolution (they have build-time defaults
and were not part of the incident); no new flags; no changes to launch
or confirmation behavior.

## Documentation

- `docs/show.md`: the "terminal is yours to name" section and the
  environment table gain the file, with the precedence order stated
  and the home-manager one-liner shown with placeholder paths
  (`/home/resident/...` if a path is ever needed — never a real one).
- `docs/scriptorium.md`: wherever terminal resolution is described,
  the same update.
- Docs are written for strangers: a reader who has never heard of
  Castle Turing, on hardware that is not ours.

## Verification plan

Agent-testable, no human involved:

- Unit tests in `dovetail-seams` over the new step: full precedence
  order (each source beating the next); missing file skipped; blank
  file skipped; malformed quoting refused naming the path; unreadable
  file refused naming the path and error; `$XDG_CONFIG_HOME` honored
  and the home fallback used when it is unset. The existing tests
  must keep passing unchanged except where they enumerate the chain.
- `nix flake check` green.

Genuinely needs human hands: nothing. This changes a pure resolution
function.

## Judgment calls made during implementation

- **`$XDG_CONFIG_HOME` is treated as unset only when empty or blank,
  not when set-but-relative.** The scratch-directory precedent in
  `dovetail-scriptorium/scratch.py` additionally requires
  `$XDG_DATA_HOME` to be an absolute path, per the XDG base-directory
  specification, and falls back otherwise. The brief did not ask for
  that nuance for `$XDG_CONFIG_HOME`, and the terminal file is an
  optional, best-effort slot rather than one Dovetail must always be
  able to resolve, so I left the stricter spec-conformance out rather
  than guess the brief wanted it. Worth revisiting if a resident is
  ever seen with a relative `$XDG_CONFIG_HOME`.
- **Neither `$XDG_CONFIG_HOME` nor `$HOME` set** is not a case the
  brief names. I treat it the same as "the file does not exist": the
  resolution step is silently skipped and the chain moves on to
  `$TERMINAL`. The refusal message falls back to naming the
  documented path (`$XDG_CONFIG_HOME/dovetail/terminal (or
  ~/.config/dovetail/terminal)`) instead of a resolved one in that
  case, since there is nothing to resolve. In practice `$HOME` is
  POSIX-guaranteed to be set, so this only matters for a deliberately
  stripped test environment.
- **An unreadable file is simulated in tests with a directory in place
  of a file**, not with permission bits, so the test does not depend on
  running as a non-root user (`chmod 000` is not honored by root, which
  a sandboxed test runner sometimes is). `Path.read_text()` on a
  directory raises `IsADirectoryError`, a genuine `OSError`, giving the
  same code path a real unreadable file would take.
- **The `--terminal` option-table rows in both docs** now say the flag
  overrides "the environment and the terminal file" rather than naming
  `$DOVETAIL_TERMINAL` alone, since it now overrides two lower-priority
  sources, not one.
