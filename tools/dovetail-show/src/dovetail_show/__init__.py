"""dovetail-show — put a named file in front of the resident.

The package is split so that the parts a stranger has to replace are
each behind one seam:

  targeting.py   the decision rule, pure and testable without a machine
  processes.py   the local process table, read from /proc
  compositor.py  the compositor seam — Sway is the only one implemented
  editor.py      the editor seam — Neovim is the reference provider
  launch.py      spawning a terminal and floating its window
  cli.py         argument parsing and the order the steps run in
"""

__all__ = ["__version__"]

__version__ = "0.1.0"
