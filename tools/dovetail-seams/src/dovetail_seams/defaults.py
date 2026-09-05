"""Build-time defaults, substituted by Nix when the tool is packaged.

Three absolute store paths are baked in at build time: the editor to
launch when nothing overrides it, the client binary used to talk to an
instance, and the REPL the scriptorium puts beside the editor. All three
placeholders survive verbatim in a source checkout, which is how running
from a git working tree falls back to whatever is on $PATH.

None of them is a taste decision the resident is stuck with:
`$DOVETAIL_EDITOR` overrides the editor at runtime and `$DOVETAIL_REPL`
the REPL, because a resident whose private layer builds its own nixvim —
or who thinks in IPython — wants her build launched, not ours.

The terminal is deliberately absent from this file. Dovetail can build
an editor and a Python; it cannot build the resident's terminal emulator
and will not guess one, so that slot refuses rather than defaults. See
`terminal_argv` in `launch.py`.
"""

from __future__ import annotations

_EDITOR = "@dovetailEditor@"
_NVIM_CLIENT = "@dovetailNvimClient@"
_REPL = "@dovetailRepl@"


def _substituted(value: str, fallback: str) -> str:
    return fallback if value.startswith("@") else value


DEFAULT_EDITOR = _substituted(_EDITOR, "nvim")
NVIM_CLIENT = _substituted(_NVIM_CLIENT, "nvim")
DEFAULT_REPL = _substituted(_REPL, "python3")
