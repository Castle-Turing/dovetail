"""The provenance block, and the argv that puts the prompt on screen.

Two pure functions and a path. `provenance` renders the comment lines
the resident reads above the pre-filled line; `wrapper_argv` assembles
the trailing arguments the resolved terminal is handed. Neither starts
anything, so both are checkable without a terminal.

The block is rendered here rather than in the wrapper on purpose. It is
the part of this verb a resident is asked to *read* before pressing
Enter, so it is worth having under unit test in the language the rest
of the verb is written in, and the wrapper is left with one job it
cannot get wrong: print what it was handed.
"""

from __future__ import annotations

from pathlib import Path

from .defaults import BASH

# The wrapper lives beside this file and is shipped as package data. It
# is handed to bash by path rather than executed by its shebang: an
# installed package's data files carry no execute bit, and naming the
# interpreter is what makes the store path of *this* flake's bash the
# one that runs.
WRAPPER = Path(__file__).with_name("prompt.bash")

_UNATTRIBUTED = "unattributed — nothing named the proposer"
_NO_REASON = "not stated"

_HEADING = "a command has been proposed for you. Nothing has run yet."
_INSTRUCTIONS = (
    "Press Enter to run it, edit the line first, or clear it to decline."
)


def provenance(proposer: str | None = None, why: str | None = None) -> str:
    """The comment lines shown above the prompt, as one block of text.

    Always four lines, whether or not `--from` and `--why` were given.
    A caller that named neither gets a block saying so, because the
    absence is the thing the resident most needs to see: a command from
    nobody, for no stated reason, is exactly the one to read twice. An
    honest nag beats a blank.
    """

    return "\n".join(
        (
            f"# dovetail-run: {_HEADING}",
            f"# Proposed by: {_text(proposer, _UNATTRIBUTED)}",
            f"# Why: {_text(why, _NO_REASON)}",
            f"# {_INSTRUCTIONS}",
        )
    )


def _text(value: str | None, absent: str) -> str:
    if value is None or not value.strip():
        return absent
    return value.strip()


def wrapper_argv(
    block: str,
    command: str,
    *,
    record_path: str = "",
    proposer: str = "",
    why: str = "",
) -> list[str]:
    """The trailing arguments the terminal runs: bash, wrapper, five strings.

    Every argument is a genuine argv element rather than anything a shell
    parses. There is no `sh -c` between the verb and the wrapper, so
    nothing the caller passed is ever interpreted as syntax on the way
    in; the one place the command is interpreted as a shell line is the
    wrapper's `eval`, after the resident has read it and pressed Enter.

    `record_path`, `proposer` and `why` are always passed, empty string
    standing in for "not given" — the wrapper's own arity never changes,
    whether or not `--record` was asked for. It is the wrapper that
    decides an empty `record_path` means "write nothing", since it is
    the wrapper, not this process, that is still running when the
    interaction ends.
    """

    return [BASH, str(WRAPPER), block, command, record_path, proposer, why]
