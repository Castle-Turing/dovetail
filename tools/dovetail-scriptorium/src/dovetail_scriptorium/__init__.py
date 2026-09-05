"""dovetail-scriptorium — build the room for working through an idea.

One invocation produces an editor tile holding a durable scratch file, a
REPL tile beside it, and a socket an agent can co-edit through. Three
files are the verb's own:

  scratch.py  where the file lives and what it is called, pure
  layout.py   what "side by side" means, read off a window tree, pure
  cli.py      argument parsing and the order the steps run in

Everything else — the compositor seam, the editor seam, the process
table, spawning a terminal and confirming it started — is in
`dovetail_seams`, shared with Dovetail's other verbs.
"""

__all__ = ["__version__"]

__version__ = "0.1.0"
