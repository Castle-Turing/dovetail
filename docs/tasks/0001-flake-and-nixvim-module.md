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
