Title: The scriptorium
Milestone: M2

M2's verb: one invocation builds the room for working through an idea
in prose, pseudocode, or Python — an editor tile holding a durable
scratch file, a REPL tile beside it, and a socket the agent can co-edit
through. `docs/vision.md`'s M2 section is the founding context; read it
first, along with `docs/module.md`, `docs/show.md`, and `AGENTS.md`.
Public mechanism, private configuration on every deliverable, and all
documentation written for a stranger on hardware that is not ours.

The operator settled this task's open questions on 2026-09-05; the
decisions below are fixed. Where the brief leaves a number or a
mechanism unstated, that is the implementing agent's judgment call to
make and report.

## Deliverables

1. **`dovetail-scriptorium`**, a command-line tool:
   `dovetail-scriptorium [--scratch-dir DIR] [--repl CMD]
   [--terminal CMD] TOPIC`. One executable per verb, per task 0002's
   rejection of subcommands. It creates or reopens the scratch file,
   builds the layout, and prints two labeled lines on stdout —
   `socket <path>` and `file <path>` — so an agent session can consume
   the room without parsing prose. Nothing else goes to stdout.
2. **The scratch file convention**, implemented and documented.
3. **The layout**, implemented as the deterministic rule below.
4. **Packaging**: a `packages.dovetail-scriptorium` flake output with
   its tests wired into `nix flake check`. `packages.default` stays the
   editor.
5. **`docs/scriptorium.md`**: the verb, the slots, the co-editing
   recipe, the limitations, a worked example with placeholder paths,
   and a human checklist (five steps at most).
6. **Vision amendment**: mark the scratch-file-convention open question
   settled, pointing at the new document, the way tasks 0001 and 0002
   recorded theirs.

## The scratch file

- **Location**: `$DOVETAIL_SCRATCH_DIR`, overridable per invocation
  with `--scratch-dir`. Unset, it defaults to
  `$XDG_DATA_HOME/dovetail/scratch`, falling back to
  `~/.local/share/dovetail/scratch` when `$XDG_DATA_HOME` is unset —
  the operator chose a zero-config default over the terminal slot's
  loud refusal. `XDG_DATA_HOME` rather than `XDG_STATE_HOME` because
  the spec assigns state-home logs-and-history semantics while these
  are durable documents; `XDG_DOCUMENTS_DIR` was rejected because it is
  not an environment variable at all — it needs xdg-user-dirs machinery
  a default must not depend on. Create the directory if it is missing.
  The private-layer lesson applies: the documentation must warn that a
  scratch directory inside a flake-tracked tree ends up world-readable
  in the Nix store (`docs/vision.md` cites the mechanism).
- **Naming**: `<YYYY-MM-DD>-<topic>.md`, date taken at invocation,
  `TOPIC` a required argument. Validate the topic as a slug — lowercase
  letters, digits, hyphens — and refuse anything else loudly rather
  than transforming it; a caller who typed spaces wants to know what
  the file will be called, not to discover a guess later.
- **Reopening is a feature.** If the file already exists, open it
  exactly as it is. Never truncate, never clobber; resuming this
  morning's session by typing the same topic is the intended behavior.
- **Promotion is a documented move, not a mechanism.** The document
  says: promote a scratch file by `git mv` into whatever repository's
  `docs/` it has earned a place in. No verb, no automation.

## The REPL tile

The flake bakes its own `python3` in as the build-time default —
the editor precedent (`$DOVETAIL_EDITOR`), not the terminal one: the
vision names Python in this milestone, and Dovetail can supply it
hermetically, so refusing to would be withholding something it holds.
`$DOVETAIL_REPL` overrides at runtime and `--repl` per invocation, both
parsed with `shlex.split` as an argv the terminal runs, exactly as
`$DOVETAIL_TERMINAL` is handled today.

## The layout

A written rule, not judgment, per the vision's placement position. On
the focused workspace: the editor tile on the left, the REPL tile on
the right, side by side. No workspace numbers, no floating, no sizes —
the resident moves and resizes as she likes; the rule only puts two
tiles somewhere predictable.

Mechanically: launch the editor (in a terminal, from the slots task
0002 built) with the scratch file on its command line, wait for its
window by process id — task 0007's machinery, which by then reports a
dead terminal loudly on every path — then launch the REPL terminal and
wait for its window, then arrange the two side by side by `con_id`.
If arrangement fails but both windows exist, warn on stderr and exit
zero: the room is usable, which is what the caller asked for; a tile
in the wrong place is not worth failing the invocation over. If either
window never appears, fail loudly — half a room is not a room.

The editor's socket comes from the same poll `--print-socket` uses
today. The compositor stays behind its seam; Sway is still the only
implementation, documented as such.

## Co-editing, in this task

The verb builds the room; it does not read the buffer. What ships here
is the **recipe**, in `docs/scriptorium.md`: how an agent holding the
socket reads the resident's buffer without waiting for saves
(`--remote-expr` over msgpack-RPC, through the editor seam's client),
and how it writes through the shared buffer during a worksession the
resident explicitly entered. The vision's starting position — try
`nvim_buf_attach` events before polling — stands, but an event bridge
is a shipped artifact with no consumer until a real co-editing session
demands one; note it in the document as the open follow-up rather than
building it speculatively. If implementing the recipe reveals that
position is wrong, amend the vision in this pull request and say why.

All Neovim-specific calls stay inside the editor seam module task 0002
established, for M3's extraction.

## Teardown

Closing the windows is the teardown. No daemon, no state file, no
registry, no cleanup verb; the scratch file survives, which is the
point of it. The module already removes sockets on clean editor exit.

## Non-goals

- No general rooms mechanism — this is one concrete worksession, seams
  left visible.
- No promote verb, no scratch-file lifecycle management.
- No buffer-event bridge (recipe and follow-up note only).
- No editing through the buffer outside an explicitly entered
  worksession — the vision's fifth starting position is a hard rule.
- No compositor other than Sway; the seam is the stranger's hook.

## Verification plan

Agent-testable, no human involved:

- Unit tests over the scratch-file logic: naming from a supplied date
  and topic, slug validation and its refusals, the directory default
  chain (`--scratch-dir` over `$DOVETAIL_SCRATCH_DIR` over
  `$XDG_DATA_HOME` over the home fallback), and that an existing file
  is left byte-identical.
- Unit tests over the layout decision logic with tree fixtures, pure,
  no compositor — the shape task 0002's targeting tests set.
- An end-to-end check in the Nix sandbox: no compositor there, so
  drive the scratch-file path — run the verb pointed at a temp scratch
  dir with a headless editor, and assert over RPC that the scratch
  file is the loaded buffer and that the printed `socket` and `file`
  lines are exact and true.
- `nix flake check` passes with the new checks wired in; every
  existing check still passes.

Genuinely needs human hands, because the sandbox has no Wayland
session: the two-tile layout on a real desktop, reopening yesterday's
topic, and the co-editing recipe against a live buffer. Write that as
the numbered checklist in `docs/scriptorium.md` — the walk task 0005
did for `show` is the model, and a follow-up task will act on what it
finds.
