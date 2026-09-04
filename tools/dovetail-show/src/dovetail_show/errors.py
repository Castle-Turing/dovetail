"""The one exception the command line turns into a diagnostic and exit 1."""

from __future__ import annotations


class ShowError(Exception):
    """Something the caller can act on: a dead socket, no terminal set."""
