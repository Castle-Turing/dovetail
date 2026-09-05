"""The one exception a verb's command line turns into a diagnostic."""

from __future__ import annotations


class DovetailError(Exception):
    """Something the caller can act on: a dead socket, no terminal set.

    Every verb catches this at its outermost frame, prints it prefixed
    with its own program name, and exits 1. Anything else is a bug and
    is allowed to produce a traceback.
    """
