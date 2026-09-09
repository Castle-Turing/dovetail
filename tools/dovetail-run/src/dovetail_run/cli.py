"""`dovetail-run` — hand the resident a command; do not run it.

This file is the order the steps run in, and nothing else. What is
refused lives in `sanitize`, the provenance block and the wrapper argv
in `prompt`, and the compositor and launch machinery in
`dovetail_seams`.

The order matters and is the same order the scriptorium uses:
everything that can be refused is refused before anything is started. A
command with a newline in it and an unset terminal are both knowable
without spawning a process, and a message is a better diagnostic than a
window that has to be closed.
"""

from __future__ import annotations

import argparse
import os
import sys

from dovetail_seams import compositor as compositor_module
from dovetail_seams import launch as seams
from dovetail_seams.errors import DovetailError

from . import launch as launch_module
from . import prompt as prompt_module
from . import record as record_module
from . import sanitize

_DESCRIPTION = """\
Open a terminal showing COMMAND, pre-filled and editable, above a
provenance comment. Nothing runs until the resident presses Enter."""

_EPILOGUE = """\
environment:
  DOVETAIL_TERMINAL  argv prefix that runs a command in a new terminal
                     window, for example "foot -e"; the file
                     $XDG_CONFIG_HOME/dovetail/terminal and then
                     $TERMINAL are the fallbacks, and there is no
                     hardcoded default

There is no --just-run and no auto-execute of any kind. See docs/run.md
for the prompt contract, what is refused and why."""


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="dovetail-run",
        description=_DESCRIPTION,
        epilog=_EPILOGUE,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "command",
        metavar="COMMAND",
        help="the exact shell line the resident would type, as one argument",
    )
    parser.add_argument(
        "--from",
        dest="proposer",
        metavar="NAME",
        help="who is proposing this command; shown above the prompt",
    )
    parser.add_argument(
        "--why",
        metavar="TEXT",
        help="why it is being proposed; shown above the prompt",
    )
    parser.add_argument(
        "--terminal",
        metavar="COMMAND",
        help="terminal argv prefix for this invocation, overriding $DOVETAIL_TERMINAL",
    )
    parser.add_argument(
        "--no-float",
        dest="float_window",
        action="store_false",
        help="leave the new window wherever the compositor puts it",
    )
    parser.add_argument(
        "--record",
        metavar="PATH",
        help=(
            "write a JSON record of what was proposed and what actually "
            "ran to PATH once the interaction ends; omit to write nothing"
        ),
    )
    return parser


def run(argv: list[str] | None = None, environ: os._Environ | dict = os.environ) -> int:
    args = _parser().parse_args(argv)

    # All three strings are echoed into the same terminal the command is
    # displayed in, so all three are held to the same rule.
    command = sanitize.check_command(args.command)
    proposer = sanitize.check(args.proposer, "--from") if args.proposer else None
    why = sanitize.check(args.why, "--why") if args.why else None

    # Also before spawning: a --record whose parent directory does not
    # exist is a refusal, not a guess about where to create one.
    record_path = record_module.check_record_path(args.record) if args.record else None

    # The transcript lives beside the record and exists for no other
    # reason, so it is only ever computed alongside a record path.
    transcript_path = (
        record_module.transcript_path_for(record_path) if record_path else None
    )

    # Before spawning: an unset terminal is a refusal, not a half-open
    # window.
    terminal = seams.terminal_argv(args.terminal, environ)

    wrapper = prompt_module.wrapper_argv(
        prompt_module.provenance(proposer, why, recording=record_path is not None),
        command,
        record_path=str(record_path) if record_path else "",
        proposer=proposer or "",
        why=why or "",
        transcript_path=str(transcript_path) if transcript_path else "",
    )

    launch_module.launch(
        terminal,
        wrapper,
        float_window=args.float_window,
        compositor=compositor_module.detect(environ),
    )

    # Deliberately not the command's exit status, which this verb never
    # learns: it returns as soon as the prompt is on screen, and whether
    # the resident runs it, edits it or declines it is hers to decide
    # afterwards. An agent closes the loop by looking at what the
    # command would have changed, never at this number.
    return 0


def main(argv: list[str] | None = None) -> int:
    try:
        return run(argv)
    except DovetailError as exc:
        print(f"dovetail-run: {exc}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        return 130


if __name__ == "__main__":
    sys.exit(main())
