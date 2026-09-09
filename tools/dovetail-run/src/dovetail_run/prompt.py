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

from .defaults import BASH, SCRIPT

# The wrapper lives beside this file and is shipped as package data. It
# is handed to bash by path rather than executed by its shebang: an
# installed package's data files carry no execute bit, and naming the
# interpreter is what makes the store path of *this* flake's bash the
# one that runs.
WRAPPER = Path(__file__).with_name("prompt.bash")

_UNATTRIBUTED = "unattributed — nothing named the proposer"
_NO_REASON = "not stated"

_HEADING = "a command has been proposed for you. Nothing has run yet."
_RECORDING = "This session's output is being recorded for the proposing agent."
_INSTRUCTIONS = (
    "Press Enter to run it, edit the line first, or clear it to decline."
)


def provenance(
    proposer: str | None = None, why: str | None = None, *, recording: bool = False
) -> str:
    """The comment lines shown above the prompt, as one block of text.

    Four lines, or five when `recording` is set — never fewer, whether or
    not `--from` and `--why` were given. A caller that named neither gets
    a block saying so, because the absence is the thing the resident
    most needs to see: a command from nobody, for no stated reason, is
    exactly the one to read twice. An honest nag beats a blank.

    `recording` is set exactly when `--record` was given: the resident
    must learn that her terminal's output is being captured before she
    decides whether to run anything, never discover it afterwards.
    """

    lines = [
        f"# dovetail-run: {_HEADING}",
        f"# Proposed by: {_text(proposer, _UNATTRIBUTED)}",
        f"# Why: {_text(why, _NO_REASON)}",
    ]
    if recording:
        lines.append(f"# {_RECORDING}")
    lines.append(f"# {_INSTRUCTIONS}")
    return "\n".join(lines)


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
    transcript_path: str = "",
) -> list[str]:
    """The trailing arguments the terminal runs: bash, wrapper, five or
    seven strings.

    Every argument is a genuine argv element rather than anything a shell
    parses. There is no `sh -c` between the verb and the wrapper, so
    nothing the caller passed is ever interpreted as syntax on the way
    in; the one place the command is interpreted as a shell line is the
    wrapper's `eval` (or, under `--record`, `script -qec`), after the
    resident has read it and pressed Enter.

    `record_path`, `proposer` and `why` are always passed, empty string
    standing in for "not given" — the wrapper's own arity never changes
    on their account, whether or not `--record` was asked for. It is the
    wrapper that decides an empty `record_path` means "write nothing",
    since it is the wrapper, not this process, that is still running
    when the interaction ends.

    `transcript_path` is different: it is passed, along with the baked
    `script` binary, only when set — which is only when `record_path` is
    also set, since the transcript exists for no other reason. Left out
    entirely rather than trailing as empty strings, so that an
    invocation with no `--record` produces an argv byte-identical to the
    one before this file learned about transcripts.
    """

    argv = [BASH, str(WRAPPER), block, command, record_path, proposer, why]
    if transcript_path:
        argv += [SCRIPT, transcript_path]
    return argv
