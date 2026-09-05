"""dovetail-seams — the machinery Dovetail's verbs have in common.

Every verb Dovetail ships has to answer the same handful of questions:
where is the compositor and what will it tell me, how do I talk to an
editor instance, what is running inside which window, and how do I start
a program in a terminal the resident named. Those answers live here once,
behind one seam each, so that a verb is only its own rule plus the order
its steps run in:

  errors.py      the one exception a verb turns into a diagnostic
  processes.py   the local process table, read from /proc
  compositor.py  the compositor seam — Sway is the only one implemented
  editor.py      the editor seam — Neovim is the reference provider
  defaults.py    build-time defaults, substituted by Nix
  launch.py      starting a program in a terminal, and confirming it

This package installs no executables. It exists so that `dovetail-show`
and `dovetail-scriptorium` share one implementation of all of the above
rather than two copies that drift, and so that M3's extraction of the
editor contract has one file to read rather than several.
"""

__all__ = ["__version__"]

__version__ = "0.1.0"
