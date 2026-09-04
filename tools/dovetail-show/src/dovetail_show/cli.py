"""`dovetail-show` — put a named file in front of the resident.

This file is the order the steps run in, and nothing else. The rule
lives in `targeting`, the compositor in `compositor`, and everything
Neovim-shaped in `editor`.
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from . import compositor as compositor_module
from . import editor as editor_module
from . import launch as launch_module
from . import processes
from .errors import ShowError
from .targeting import LaunchNew, OpenIn, choose_target

_DESCRIPTION = """\
Open FILE in an editor: the one in the focused window if there is one,
otherwise a new floating instance."""

_EPILOGUE = """\
environment:
  DOVETAIL_SOCKET    the instance to use, as if --socket had been given
  DOVETAIL_TERMINAL  argv prefix that runs a command in a new terminal
                     window, for example "foot -e"; $TERMINAL is the
                     fallback and there is no hardcoded default
  DOVETAIL_EDITOR    the editor to launch, overriding the build default

See docs/show.md for the targeting rule and its known limitations."""


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="dovetail-show",
        description=_DESCRIPTION,
        epilog=_EPILOGUE,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("file", metavar="FILE", help="the file to show")
    parser.add_argument(
        "--line",
        metavar="N",
        type=int,
        help="put the cursor on line N",
    )
    parser.add_argument(
        "--socket",
        metavar="PATH",
        help="use the instance listening on PATH, rather than discovering one",
    )
    parser.add_argument(
        "--terminal",
        metavar="COMMAND",
        help="terminal argv prefix for a launch, overriding $DOVETAIL_TERMINAL",
    )
    parser.add_argument(
        "--no-float",
        dest="float_window",
        action="store_false",
        help="leave a launched window wherever the compositor puts it",
    )
    parser.add_argument(
        "--print-socket",
        action="store_true",
        help="print the socket of the instance the file was shown in",
    )
    return parser


def run(argv: list[str] | None = None, environ: os._Environ | dict = os.environ) -> int:
    args = _parser().parse_args(argv)

    if args.line is not None and args.line < 1:
        raise ShowError(f"--line must be 1 or greater, not {args.line}")

    # Absolute, because the instance's working directory is its own
    # business and is rarely the caller's.
    path = Path(args.file).expanduser().absolute()

    compositor = compositor_module.detect(environ)
    sway_tree = compositor.get_tree() if compositor is not None else None

    target = choose_target(
        explicit_socket=args.socket or environ.get("DOVETAIL_SOCKET") or None,
        sway_tree=sway_tree,
        process_table=processes.read_process_table(),
        instances=editor_module.list_instances(environ),
        verify=editor_module.is_reachable,
    )

    if isinstance(target, OpenIn):
        editor_module.open_file(target.socket, path, args.line)
        socket = target.socket
    else:
        assert isinstance(target, LaunchNew)
        socket = launch_module.launch(
            path,
            args.line,
            terminal=args.terminal,
            float_window=args.float_window,
            want_socket=args.print_socket,
            compositor=compositor,
            environ=environ,
        )

    if args.print_socket:
        if socket is None:
            raise ShowError(
                "the file was opened in a new editor, but it published no "
                f"socket within {launch_module.SOCKET_TIMEOUT:.0f} seconds, so "
                "there is nothing to print"
            )
        print(socket)
    return 0


def main(argv: list[str] | None = None) -> int:
    try:
        return run(argv)
    except ShowError as exc:
        print(f"dovetail-show: {exc}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        return 130


if __name__ == "__main__":
    sys.exit(main())
