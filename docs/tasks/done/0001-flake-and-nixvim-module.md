Title: The flake and the nixvim module
Milestone: M1

# 0001 — The flake and the nixvim module

Dovetail's first buildable artifact: a flake that exports the shared
nixvim module, so that an editor instance launched from this
configuration is born reachable over a socket. This brief also settles
the socket path scheme — the first half of the vision's first open
question — because the module cannot guarantee reachability without
naming the path. The discovery half (which instance is "current" when
several exist) is deliberately left to task 0002, the `show` verb,
where a consumer actually needs the answer.

Everything in `docs/vision.md` applies; read it first. In particular:
public mechanism, private configuration (no colorscheme, no keymaps,
no taste of any kind hardcoded here), and docs written for strangers.

## Deliverables

1. **`flake.nix`** with `nixpkgs` and `nixvim` as inputs, exporting:
   - the Dovetail nixvim module, in whatever attribute shape nixvim's
     documentation says modules are consumed in — verify against
     current nixvim docs, do not pattern-match from memory;
   - a runnable package (the configured Neovim) so a stranger can
     `nix run` it without adopting any module system, and so the
     checks below have something to execute;
   - a dev shell if the implementation wants one;
   - `checks` wired so `nix flake check` runs the verification below.
2. **The module itself:**
   - Socket-on-launch under the scheme below, guaranteed by the
     shipped configuration — the agent never configures at runtime.
   - Treesitter enabled, including markdown.
   - Prose-friendly markdown defaults, buffer-local to markdown:
     soft wrap with `linebreak`, and whatever minimal companions the
     implementer judges sensible. Keep this list short; anything a
     resident might reasonably want different is taste and belongs in
     the overlay point, not here.
   - **The overlay point:** the documented place a private layer adds
     its keymaps, colorscheme, and cosmetics. Prefer the mechanism
     nixvim's own module system already provides (importing a second
     module alongside ours) over inventing an option — but verify
     what composes cleanly and document the winner with a worked
     example using placeholder paths (`/home/resident/...`).
3. **CI:** a GitHub Actions workflow running `nix flake check` on
   pull requests and pushes to `main`.
4. **Vision amendment**, in this same branch once implementation
   confirms the scheme: record the socket-path decision under the
   vision's open questions, leaving the discovery half explicitly
   open for 0002.

## The socket path scheme

One socket per editor instance, at:

    $XDG_RUNTIME_DIR/dovetail/nvim-<pid>.sock

- `$XDG_RUNTIME_DIR` because it is per-user, tmpfs-backed, and
  permission-safe by platform contract; a `dovetail/` subdirectory so
  discovery is "list one directory," never "know a magic name."
- `<pid>` because the instance knows it at startup with no
  coordination, and it is unique among live instances by construction.
- The configuration creates the directory if absent, starts the
  server at that path on launch, and removes the socket on clean
  exit. Consumers must nevertheless tolerate stale sockets from
  unclean exits — connect-and-verify, not trust-the-listing. That
  tolerance is 0002's to implement; this task's job is only to keep
  the common case clean.
- Prefer guaranteeing this inside the shipped editor configuration
  (Neovim can start a server from its own init) over a wrapper script
  that passes `--listen`, so the guarantee travels with the
  configuration rather than with one launch path. If implementation
  finds the in-config route unreliable, a wrapper is acceptable —
  record the finding in this brief.

**Considered and rejected.** Per-Sway-workspace naming: bakes a
compositor concept into the editor layer, exactly the coupling the
provider slot exists to avoid. A single primary socket at a fixed
path: fails the moment a second instance launches, and "second
instance" is the normal case, not the edge case.

## Non-goals

- No `show` verb, no Sway IPC, no discovery CLI — all task 0002.
- No castle-turing-side consumption; the framework re-exporting this
  flake is a follow-up in that repo, not here.
- No Emacs anything.

## Verification plan

Agent-testable, no human involved:

- `nix flake check` passes; the package builds.
- A headless-launch check: with a scratch `XDG_RUNTIME_DIR`, start
  the configured Neovim headless, assert the socket file appears at
  the scheme path, connect to it and evaluate a trivial expression
  over RPC, then exit cleanly and assert the socket is gone.
- Assert markdown buffer-local settings via the same RPC channel
  (open a markdown file, read the options back).

Needs human hands:

- Confirming the overlay point accepts a real private-layer
  configuration (colorscheme and a keymap) without friction.
- Eyeballing the markdown defaults on a real screen; "prose-friendly"
  is ultimately a judgment.

## Judgment calls to report

Per the operator contract: where this brief is ambiguous — the exact
prose-settings list, the overlay-point mechanism, in-config server
versus wrapper — decide, and report the decision and its reasoning in
the PR so the record stays honest.

## Implementation record

Written during implementation, per the section above. Where this
contradicts anything earlier in the brief, this section is what was
built.

**The in-config server works; no wrapper was needed.** The socket is
started from `extraConfigLuaPre`, which runs before any private-layer
configuration, so a broken overlay still leaves an instance you can
reach and inspect. The guarantee therefore travels with the
configuration and holds for every launch path, including
`nvim --headless`, which is what the check exercises. The brief's
fallback to a `--listen` wrapper was not taken.

**Failure is reported in globals, not on stderr.** `g:dovetail_socket`
carries the path and `g:dovetail_socket_error` carries the reason there
isn't one; the module prints nothing at startup. This is not only
tidiness: nixvim's own `build.test` runs `nvim --headless +q` and fails
the build if a single byte reaches stderr, and it runs in a sandbox
where `$XDG_RUNTIME_DIR` is unset — so a `vim.notify` on that path
would have made the module's own smoke test unpassable. Since a missing
`$XDG_RUNTIME_DIR` means there is no second location that is equally
private, the module declines to invent one and records why.

**The prose settings are four, all buffer-local to markdown:** `wrap`
and `linebreak` (required by the brief), plus `breakindent`, which is
what makes a wrapped list item readable rather than merely wrapped, and
`textwidth=0`, so that soft wrapping is never quietly undone by the
editor rewriting the file to hard-wrap it. Spell checking and its
dictionary, `conceallevel`, `showbreak`, and remapping `j`/`k` to move
by display line were all considered and left out: each is something one
reasonable person wants set differently from the next, which is the
definition of taste under Principle 01. They belong in the overlay
point, and the example private layer shipped with the checks sets two
of them to prove it.

**The overlay point is nixvim's own module composition**, with no
Dovetail-specific option invented. A private layer is a nixvim module
listed alongside ours in `evalNixvim`'s `modules`, or imported inside
`programs.nixvim` under Home Manager, NixOS or nix-darwin. This
composes cleanly because the module leaves every cosmetic option
undefined, so nothing collides; where both sides do define an option,
ordinary module-system merging applies. The mechanism is documented
with a worked example in `docs/module.md` and is exercised by the
`overlay-point` check, so the example is a tested claim.

**The treesitter grammar set is bounded, not nixvim's default of every
grammar it can build.** Markdown and `markdown_inline` are the reason
the project exists; the rest are the languages this ecosystem's own
trees are written in. `grammarPackages` is a list option, so a private
layer adds to the set rather than replacing it — documented, and shown
in the worked example.

**Nixvim's `nixpkgs` input is not overridden.** `inputs.nixvim.inputs.
nixpkgs.follows = "nixpkgs"` is the reflexive thing to write and it
makes nixvim emit a warning that its own `build.test` treats as fatal;
nixvim is tested against the Nixpkgs it pins. The editor is therefore
built from nixvim's Nixpkgs, and this flake's own `nixpkgs` input
supplies only the scaffolding: the check runner, the RPC client, the
formatter. The `headless-socket` check consequently talks to the editor
across two Nixpkgs revisions, which is a small bonus — it demonstrates
the socket is a real interface rather than an artefact of one closure.

**The `nix run` entry point is `packages.default`**, aliased as
`packages.dovetail` rather than `packages.dovetail-nvim`: the package
is the editor Dovetail ships, and naming it after the reference
provider would be the same design smell the vision's starting position
4 warns about.

### Verification as built

`nix flake check` runs three checks, all agent-testable:

- `config` — nixvim's smoke test: no warnings, no failed assertions,
  and `nvim` starts and quits without writing to stderr.
- `headless-socket` — the brief's headless-launch check, plus the
  markdown assertions. Launches a headless instance with a scratch
  `$XDG_RUNTIME_DIR`; asserts exactly one socket appears under
  `dovetail/`; asserts the process id in its name is the instance's own
  by asking the instance over the socket rather than trusting the
  shell; round-trips a trivial expression over RPC; reads back the four
  markdown options buffer-locally and confirms they have not leaked
  into the global options; confirms the markdown parser is on the
  runtime path; then quits cleanly and asserts the socket is gone and
  the directory empty. The RPC client is unwrapped Neovim from a
  different Nixpkgs, so the check cannot pass by talking to itself.
- `overlay-point` — the example private layer composes and builds.

The two items the brief listed as needing human hands still need them:
confirming a real private layer lands without friction, and judging the
markdown defaults on a screen.
