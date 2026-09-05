"""Build-time defaults, substituted by Nix when the tool is packaged.

Two absolute store paths are baked in at build time: the editor to
launch when nothing overrides it, and the client binary used to talk to
an instance. Both placeholders survive verbatim in a source checkout,
which is how running from a git working tree falls back to whatever is
on $PATH.

Neither is a taste decision the resident is stuck with: `$DOVETAIL_EDITOR`
overrides the editor at runtime, because a resident whose private layer
builds its own nixvim wants her build launched, not ours.
"""

from __future__ import annotations

_EDITOR = "@dovetailEditor@"
_NVIM_CLIENT = "@dovetailNvimClient@"


def _substituted(value: str, fallback: str) -> str:
    return fallback if value.startswith("@") else value


DEFAULT_EDITOR = _substituted(_EDITOR, "nvim")
NVIM_CLIENT = _substituted(_NVIM_CLIENT, "nvim")
