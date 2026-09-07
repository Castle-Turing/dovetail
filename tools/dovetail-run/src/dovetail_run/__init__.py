"""dovetail-run — put a command in front of the resident, without running it.

One invocation opens a terminal showing who proposed a command and why,
above a pre-filled, editable prompt line. Nothing runs until the
resident presses Enter, and editing the line first or declining it
outright are equal citizens.

  sanitize.py    what is refused, so that what is displayed is what runs
  prompt.py      the provenance block, and the argv that shows it
  prompt.bash    the prompt itself, run inside the resident's terminal
  launch.py      spawning that terminal, and confirming it opened
  cli.py         the order the steps run in

The compositor, the terminal slot and the launch machinery are
`dovetail-seams`, shared with `dovetail-show` and
`dovetail-scriptorium`.
"""

__all__ = ["__version__"]

__version__ = "0.1.0"
