"""dovetail-show — put a named file in front of the resident.

Only two files here are the verb's own:

  targeting.py   the decision rule, pure and testable without a machine
  launch.py      what *show* does with a launched window: float it
  cli.py         argument parsing and the order the steps run in

Everything else it needs — the compositor seam, the editor seam, the
process table, spawning a terminal and confirming it started — is in
`dovetail_seams`, shared with Dovetail's other verbs.
"""

__all__ = ["__version__"]

__version__ = "0.1.0"
