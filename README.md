# Dovetail

The editor joint of the [Castle Turing](https://github.com/Castle-Turing/castle-turing)
ecosystem: glue between the agent, the window manager, and the text
editor. Castle Turing's trust model runs on its resident actually
reading what the system writes — diffs, digests, briefs, research —
and Dovetail makes the text editor that surface: the place the castle
shows its operator code and markdown, and an instrument an agent can
drive over a socket the same way it drives the display.

The name is from *The Diamond Age*: Dovetail is the artisan community
where things are still made by hand, deliberately, in a world of
matter compilers. The joinery reading — two pieces cut to interlock
without fasteners — is the bonus meaning.

**Status: pre-alpha.** Two artifacts exist. A nixvim module whose every
Neovim instance is born reachable over a socket, with treesitter and
prose-friendly markdown defaults:

```
nix run github:Castle-Turing/dovetail
```

and the first verb, which puts a named file in front of you — in the
editor you are looking at, or in a new floating one if you are not:

```
nix run github:Castle-Turing/dovetail#dovetail-show -- notes/today.md
```

Read [`docs/module.md`](docs/module.md) for what the module guarantees,
the socket path scheme, and the overlay point where your own keymaps and
colourscheme go, and [`docs/show.md`](docs/show.md) for the verb's
targeting rule, the terminal you have to name, and its limitations. The
rest of the roadmap — the scriptorium, the editor contract — is still
design record; start with [`docs/vision.md`](docs/vision.md).

## Relation to Castle Turing

A real dependency, not a fork: the castle-turing flake will consume
Dovetail as an input and re-export its module, so a resident gets it
through their own pin. It is also meant to be independently adoptable —
someone running Sway and Neovim who has never heard of Castle Turing
should be able to use Dovetail's verbs on their own. Design Principle
01 (public mechanism, private configuration) applies in full.

## Layout

```
flake.nix        Inputs, the exported nixvim module, the runnable
                 packages, and the checks.
nix/module.nix   The Dovetail nixvim module itself.
nix/packages/    Nix expressions for the verbs.
nix/checks/      What `nix flake check` runs.
tools/           The verbs themselves, one directory each.
docs/module.md   Reference documentation for the module.
docs/show.md     Reference documentation for the `show` verb.
docs/vision.md   The founding context. Read it first.
docs/backlog/    Deferred work, one plain-text file per item.
docs/tasks/      Numbered briefs — the spec and reasoning for each
                 piece of implementation work.
docs/research/   Full point-in-time research reports, when any exist.
AGENTS.md        The operator contract for agents working here.
```

## License

Everything in this repo is [MIT-licensed](LICENSE).
