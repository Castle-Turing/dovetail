# The Dovetail nixvim module

This is the reference documentation for Dovetail's first artifact: a
[nixvim] module that makes every Neovim instance built from it reachable
over a socket at a predictable path, turns on treesitter, and sets a
short list of prose-friendly markdown defaults.

It is written for a stranger. You do not need to know anything about
Castle Turing to use it; you need Nix with flakes enabled, and a
willingness to let Nix own your editor's configuration.

[nixvim]: https://github.com/nix-community/nixvim

## Trying it

```
nix run github:Castle-Turing/dovetail
```

That builds and runs the module's configuration on its own, with no
private layer attached and nothing of anybody's taste in it.

## What the module guarantees

**Reachability.** Every instance starts a msgpack-RPC server on a Unix
socket before any other configuration runs, and reports the path in
`g:dovetail_socket`. Nothing has to be arranged at launch time and no
agent has to configure anything at runtime; an instance is reachable
because it exists.

**Treesitter, including markdown.** Highlighting and indentation are on,
with a bounded set of grammars installed through Nix — markdown and
`markdown_inline` first, then the languages this ecosystem's own trees
are written in (Bash, Git, JSON, Lua, Nix, Python, TOML, Vimscript,
YAML, and treesitter's own query language). No grammar is compiled at
runtime.

**Prose-friendly markdown, buffer-locally.** In markdown buffers only:
`wrap`, `linebreak`, `breakindent`, and `textwidth=0`. Together those
mean long paragraphs wrap at the window edge, at word boundaries, with
continuation lines indented under the text they continue, and the file
on disk is never rewritten to hard-wrap it.

That list is short on purpose. Spell checking and its dictionary,
`conceallevel`, `showbreak`, and remapping `j`/`k` to move by display
line are all things a reasonable person wants set differently from the
next reasonable person. They are taste, and taste goes in the overlay
point below.

## The socket path scheme

One socket per instance, at:

```
$XDG_RUNTIME_DIR/dovetail/nvim-<pid>.sock
```

`$XDG_RUNTIME_DIR` because it is per-user, tmpfs-backed and
permission-safe by platform contract. A `dovetail/` subdirectory so that
discovering instances is "list one directory", never "know a magic
name". The process id because the instance knows it at startup with no
coordination, and it is unique among live instances by construction.

The module creates the directory if it is absent (mode `0700`), starts
the server there on launch, and removes the socket on clean exit.

**Consumers must still tolerate stale sockets.** A `SIGKILL`, a power
cut, or a crash leaves the file behind, and the process id it names may
by then belong to something else entirely. The rule for a consumer is
connect-and-verify, never trust-the-listing: open the socket, ask the
instance for something, and treat a failure to answer as "this entry is
rubbish, ignore it". Deciding *which* live instance is the current one
when several answer is a separate question, deliberately left open until
something needs the answer.

Two globals report the outcome, and the module writes nothing to stderr
at startup:

| Global | Meaning |
| --- | --- |
| `g:dovetail_socket` | the socket this instance is listening on, or `nil` |
| `g:dovetail_socket_error` | why there is no socket, or `nil` |

`g:dovetail_socket_error` is set, rather than a warning printed, when
`$XDG_RUNTIME_DIR` is unset — there is no second path that is equally
private, so the module declines to invent one and says why instead.

### Talking to an instance

Anything that speaks Neovim's msgpack-RPC will do. Neovim itself is the
shortest demonstration:

```
sock=$(ls "$XDG_RUNTIME_DIR"/dovetail/nvim-*.sock | head -n1)
nvim --server "$sock" --remote-expr 'getpid()'
nvim --server "$sock" --remote 'notes/today.md'
```

Dovetail's own tooling will not do it this way for long: the point of
the project is a set of verbs that name the *action*, not the editor.
Calling `nvim` by name is fine in a shell demonstration and a design
smell in a tool.

## The overlay point

Your private layer is a nixvim module, imported alongside this one.
There is no Dovetail-specific option to learn, no `dovetail.extraConfig`
attribute, and nothing that needs to be re-exported when nixvim gains
new options: whatever nixvim can express, your layer can set.

```nix
{
  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixpkgs-unstable";
    nixvim.url = "github:nix-community/nixvim";
    dovetail.url = "github:Castle-Turing/dovetail";
  };

  outputs =
    { nixpkgs, nixvim, dovetail, ... }:
    let
      system = "x86_64-linux";
      configuration = nixvim.lib.evalNixvim {
        inherit system;
        modules = [
          dovetail.nixvimModules.dovetail
          /home/resident/private/nvim  # <- your taste lives here
        ];
      };
    in
    {
      packages.${system}.default = configuration.config.build.package;
      checks.${system}.default = configuration.config.build.test;
    };
}
```

And `/home/resident/private/nvim/default.nix`:

```nix
{ config, ... }:
{
  colorscheme = "habamax";

  keymaps = [
    {
      mode = [ "n" "x" ];
      key = "j";
      action = "gj";
      options.desc = "Down by display line";
    }
  ];

  opts.spell = true;
  opts.spelllang = "en_gb";

  # Lists merge, so this adds grammars to Dovetail's set rather than
  # replacing it.
  plugins.treesitter.grammarPackages =
    with config.plugins.treesitter.package.builtGrammars;
    [
      go
      rust
    ];
}
```

Nothing in that file is Dovetail's business, and Dovetail sets none of
those options, so nothing collides. Where both modules do define the
same option, the ordinary Nix module-system rules apply: attribute sets
and lists merge, and a scalar conflict is an evaluation error you can
settle with `lib.mkForce` or `lib.mkDefault`.

Dovetail ships a stand-in private layer at
`nix/checks/example-private-layer.nix` and builds the combination in
`nix flake check`, so the example above is a tested claim rather than a
hopeful one.

### Keep your private layer out of the flake tree

If your taste lives inside a git repository that a flake evaluates, Nix
copies that whole tree into `/nix/store`, which is world-readable on the
machine. Point at a path outside the flake, as above, or keep the layer
in a private flake of its own.

### Other module systems

The same module goes anywhere nixvim modules go. Under Home Manager,
NixOS or nix-darwin, import it inside the `programs.nixvim` namespace:

```nix
{
  programs.nixvim = {
    enable = true;
    imports = [ dovetail.nixvimModules.dovetail ];
    # your taste, at the same level
    colorscheme = "habamax";
  };
}
```

## What `nix flake check` proves

Three checks, all runnable by anyone with no hardware and no hands:

- **`config`** — nixvim's own smoke test. The configuration evaluates
  with no warnings and no failed assertions, and the resulting `nvim`
  starts and quits without writing a byte to stderr.
- **`headless-socket`** — the reachability guarantee, end to end. A
  headless instance is launched with a scratch `$XDG_RUNTIME_DIR`; the
  check asserts that exactly one socket appears under `dovetail/`, that
  the process id in its name is the instance's own (confirmed by asking
  the instance over the socket, not by trusting the shell), that a
  trivial expression round-trips over RPC, that the markdown prose
  defaults are set buffer-locally and have not leaked into the global
  options, that the markdown parser is on the runtime path, and that a
  clean exit removes the socket and leaves the directory empty.
- **`overlay-point`** — a second module carrying nothing but taste
  composes with this one and still builds.

Two things still need human hands, and the checks do not pretend
otherwise: confirming that a *real* private layer lands without
friction, and deciding whether the markdown defaults actually read well
on a screen.
