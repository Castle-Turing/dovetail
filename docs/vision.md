# Dovetail

*The editor joint. Dovetail is the glue between the agent, the window
manager, and the text editor, in the Castle Turing ecosystem. A dovetail
joint is two pieces of wood cut to interlock without fasteners: the
components stay themselves but are shaped to fit each other. This
document is the founding context for the project — nothing in it is
adopted principle; every position below is held only until
implementation confirms or overturns it, and this document is amended
when one falls.*

## What this is

Castle Turing's trust model runs on the resident reading what the
system writes. The worker proposes a diff the resident reviews before
anything is applied; the digest, the task briefs, the research library,
and the decision journal are all markdown the resident is expected to
actually read, and the vision's comprehension principle makes their
ability to exercise judgment over that reading load-bearing, not
cosmetic. Today that reading happens in a web browser or raw in a
terminal — the reading half of the trust loop is the least designed
part of the system, and a browser tab does not fit an environment whose
entire premise is that plain text in a terminal-native workflow is the
shared language of resident and agent.

Dovetail makes the text editor that surface: the place the castle shows
its operator code and markdown, and an instrument the agent can drive
the same way it drives the display. Sway is operated over IPC; the
editor is operated over a socket; one interaction grammar, two
instances of it.

It has two consumers from birth. The first is interactive agent
sessions — the agentic development workflow the ecosystem is built
with, where "show me the file" and "let's work through this idea
together" should land in an editor tile, not a browser. The second,
later, is the castle's own seats, which will need somewhere to put a
diff or a brief in front of the resident.

## Relation to Castle Turing

Dovetail is a real dependency of the framework, not a sibling: the
castle-turing flake consumes it as an input and re-exports its module,
the same way it consumes sops-nix, so a resident gets it through their
own pin. It is also independently adoptable — someone running Sway and
Neovim who has never heard of Castle Turing should be able to use
Dovetail's verbs on their own. Both halves are deliberate: the first
makes it mechanism the castle can rely on, the second keeps it honest
as a standalone tool with a contract written for strangers.

Design Principle 01 applies in full: everything here is public
mechanism; every taste decision — colorscheme, keymaps, typefaces,
where scratch files live — is private configuration in a documented
slot.

## Starting positions

1. **The reference editor is Neovim, configured via nixvim.** The
   editor's static configuration is Nix expressions: plugins, filetype
   settings, prose-friendly markdown defaults. Nix owns the
   configuration language; the editor does not get its own config
   problem. (The castle-turing framework's dev module ships Emacs
   today; reconciling that is a framework-side follow-up once Dovetail
   is consumable, not this project's concern.)
2. **The agent drives every surface over a socket.** Neovim's
   msgpack-RPC (`nvim --listen`) is the control channel, as Sway's IPC
   socket is for the display.
3. **Every editor instance is born reachable.** The shipped
   configuration guarantees a socket listening at a predictable path
   under `$XDG_RUNTIME_DIR` — settled in M1 as
   `$XDG_RUNTIME_DIR/dovetail/nvim-<pid>.sock`, one socket per
   instance; see the open questions below. The agent never configures
   at runtime; it only acts.
4. **The editor is a slot, not a hardcode.** Dovetail defines an editor
   contract; Neovim is the reference provider occupying the slot. This
   is castle-turing's Proposal 03 — intelligence is a tenant, not a
   structural member — applied to the editor: the contract is defined
   by its verbs, and any provider that implements them can hold the
   slot. Tooling calls Dovetail's verbs, never `nvim` by name; a tool
   that shells out to the editor directly is a design smell.
5. **Edits land on disk by default.** The normal path for an agent's
   edit is the file, with the editor reloading — and Dovetail's job on
   that path is making the reload seamless: no swap-file conflicts, no
   lost cursor, the change visibly landing. Editing *through* a live
   buffer (RPC into shared undo) is not a default and never an ambient
   policy: it is a feature of co-editing worksessions the resident
   explicitly enters, where the shared buffer is the point. An agent
   that edits the buffer you happen to be looking at, uninvited, is
   the wrong-channel failure the castle's vision warns about — and
   routing a harness's ordinary file edits through buffer RPC would
   make a harness feature load-bearing besides.
6. **The contract is derived from use.** It is extracted from the
   verbs the first consumers actually called, after they work — never
   designed in advance. A small required core plus declared optional
   capabilities (event subscription, shared undo), so it is not
   lowest-common-denominator.

## Roadmap

**M1 — show me the file.** A shared nixvim module (socket-on-launch,
treesitter, markdown-friendly prose settings, a documented overlay
point for private-layer keymaps and cosmetics) and a `show` verb: one
invocation opens a named file in a sensibly placed Sway tile, whether
or not an editor is already running. Placement is a deterministic,
documented rule, not judgment — where the rule can be written, the
rule is the best tenant; channel judgment belongs to the castle's
router, later, if ever. This milestone is the itch that started the
project: reading the ecosystem's own markdown without a browser.

**M2 — the scriptorium.** A worksession for working through an idea in
prose, pseudocode, or Python: one verb produces a Sway layout with a
buffer tile and a REPL tile, an editor instance with a known socket,
and a scratch file — a durable, real file in a location the private
layer names, never ephemeral. Resident and agent co-edit the same
buffer; the agent reads the resident's changes back over RPC without
waiting for saves. This is where *through* edits live, by
construction. Deliberately bounded and low-authority: the agent
arranges and co-edits, nothing outward-facing. Teardown is clean and
leaves the scratch file behind.

**M3 — the joint.** Extract the contract from what M1 and M2 actually
called, as a document written for strangers: ensure an instance exists
and is reachable; open a file, optionally at a line; create a scratch
buffer bound to a file; read buffer contents; apply an edit through
the editor; subscribe to or poll for changes; report what is open
where; and one discovery affordance — given a session, where is your
control socket and what protocol does it speak. The contract absorbs
protocol differences (msgpack-RPC vs. `emacsclient --eval`); it never
leaks them. Alongside it: the provider slot as a module interface with
Neovim as the default implementation, existing tooling refactored to
call the slot, and a providers directory whose Emacs entry is a README
only — implement these verbs, here is how the Neovim provider does
each one — the hook a stranger hangs an implementation on without us
in the room.

M3 must come last: the contract is extracted from M1 and M2, not
imposed on them. Acceptance for each milestone lives in its numbered
brief in `docs/tasks/`, not here.

## Non-goals

- **The general rooms mechanism.** The scriptorium is built as one
  concrete worksession. Rooms generalize from it later, if they earn
  it; the seams are left visible on purpose, and no framework is built
  now.
- **An Emacs implementation.** The hook only.
- **Rendered markdown previews.** In-buffer prose settings belong to
  the nixvim module; a browser-grade rendered view is a
  display-channel choice that belongs to the compositor layer, not
  this package.
- **Any outward-facing authority.** Nothing here sends, declines, or
  communicates on anyone's behalf.
- **Becoming the agent layer's edit path.** The castle's worker seat
  proposes diffs against checkouts under its own contract; Dovetail
  does not sit in that path and does not want to.

## The split (Principle 01, checked per deliverable)

Public framework: the nixvim module, all Dovetail tooling, the
contract, the provider slot, the Emacs stub, this document. Private
layer: editor cosmetics and keymaps via the overlay point, the scratch
directory location and retention policy, which worksessions exist. One
inherited lesson applies to the scratch directory the moment it is
named: nothing private goes inside a flake-tracked tree, because
evaluation copies that tree into the world-readable Nix store —
castle-turing's `docs/private-layer.md` documents the mechanism in
full. If any piece resists the public/private split during
implementation, stop and redesign; that is the smell test doing its
job.

## Name

Dovetail is the artisan community in Neal Stephenson's *The Diamond
Age* — the place where things are still made by hand, deliberately, in
a world of matter compilers. The same naming tradition as Castle Turing
and Chevaline, and the same reason: this is the surface where the
resident works text by hand in an environment full of generated
artifacts. The joinery reading — two pieces cut to interlock without
fasteners — is the bonus meaning, not the source.

## Open questions

Resolved answers are recorded here or in the brief that settles them.

- ~~Socket path scheme~~ — **settled by task 0001** (`docs/tasks/`),
  and implemented in the nixvim module: one socket per instance at
  `$XDG_RUNTIME_DIR/dovetail/nvim-<pid>.sock`, started from the shipped
  configuration and removed on clean exit, with consumers required to
  tolerate stale sockets by connecting and verifying rather than
  trusting the listing. Per-Sway-workspace naming was rejected for
  baking a compositor concept into the editor layer; a single primary
  socket at a fixed path was rejected because a second instance is the
  normal case. The reference documentation is `docs/module.md`.
- **Still open — instance discovery.** Given several live instances,
  which one is "current"? Deliberately left to task 0002, the `show`
  verb, where a consumer actually needs the answer; the scheme above
  makes discovery "list one directory" but does not rank what it
  finds.
- Scratch file convention: naming, the private-layer slot for its
  location, and the promotion path from scratch to design doc or task.
- Buffer-change reading in M2: `nvim_buf_attach` events versus
  polling — try events first; this decides the first capability flag.
- A headless, agent-owned editor instance — pure text-manipulation
  server, separate from anything visible — may be useful for on-disk
  edits that still want editor-grade manipulation. Deferred unless M1
  or M2 demands it.
