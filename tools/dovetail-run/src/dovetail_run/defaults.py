"""The one build-time default this verb has of its own: bash.

`dovetail-seams` bakes in the editor, the RPC client and the REPL; the
prompt wrapper needs one thing none of those covers, which is a bash new
enough for `read -e -i`. It is baked in as an absolute store path so
that the prompt does not depend on what happens to be on the resident's
`$PATH` inside whatever terminal she has named.

There is deliberately no runtime override. The wrapper is written in
bash and uses bash's readline binding; a shell slot would be a slot for
shells that cannot hold this script.
"""

from __future__ import annotations

_BASH = "@dovetailBash@"

# The placeholder survives verbatim in a source checkout, which is how
# running from a git working tree falls back to whatever is on $PATH.
BASH = "bash" if _BASH.startswith("@") else _BASH
