"""The build-time defaults this verb has of its own: bash and script.

`dovetail-seams` bakes in the editor, the RPC client and the REPL; the
prompt wrapper needs two things none of those covers. One is a bash new
enough for `read -e -i`; the other is the `script` binary that records a
pty transcript when `--record` is given. Both are baked in as absolute
store paths so that the prompt does not depend on what happens to be on
the resident's `$PATH` inside whatever terminal she has named.

There is deliberately no runtime override for either. The wrapper is
written in bash and uses bash's readline binding, so a shell slot would
be a slot for shells that cannot hold this script; the recorder is
`script -qec` specifically, per `docs/run.md`, not a pluggable choice of
pty-capture tool.
"""

from __future__ import annotations

_BASH = "@dovetailBash@"
_SCRIPT = "@dovetailScript@"

# The placeholders survive verbatim in a source checkout, which is how
# running from a git working tree falls back to whatever is on $PATH.
BASH = "bash" if _BASH.startswith("@") else _BASH
SCRIPT = "script" if _SCRIPT.startswith("@") else _SCRIPT
