"""`dovetail-scriptorium` — build the room for working through an idea.

This file is the order the steps run in, and nothing else. The scratch
file convention lives in `scratch`, the layout rule in `layout`, and the
compositor, editor and launch machinery in `dovetail_seams`.
"""

from __future__ import annotations

import argparse
import os
import sys
from dataclasses import dataclass

from dovetail_seams import compositor as compositor_module
from dovetail_seams import launch as seams
from dovetail_seams.errors import DovetailError

from . import layout, scratch

_DESCRIPTION = """\
Open a worksession on TOPIC: a durable scratch file in an editor tile,
a REPL tile beside it, and the editor's socket printed for an agent to
co-edit through."""

_EPILOGUE = """\
output:
  Two lines on stdout, and nothing else:

    socket <path>   the editor instance's control socket
    file <path>     the scratch file it has open

environment:
  DOVETAIL_SCRATCH_DIR  where scratch files live; defaults to
                        $XDG_DATA_HOME/dovetail/scratch, or
                        ~/.local/share/dovetail/scratch
  DOVETAIL_TERMINAL     argv prefix that runs a command in a new terminal
                        window, for example "foot -e"; falls back to the
                        declarative file at $XDG_CONFIG_HOME/dovetail/terminal
                        (or ~/.config/dovetail/terminal), then to $TERMINAL,
                        and there is no hardcoded default
  DOVETAIL_REPL         the REPL to run beside the editor, overriding the
                        build default
  DOVETAIL_EDITOR       the editor to launch, overriding the build default

See docs/scriptorium.md for the scratch file convention, the layout rule
and the co-editing recipe."""

# What the caller loses when a terminal dies instead of opening a window.
# Named per tile, because "the room was not built" is true of both and
# tells the resident nothing about which half failed.
_NO_EDITOR = "the worksession has no editor, so it was not opened"
_NO_REPL = "the editor is open, but the worksession has no REPL beside it"


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="dovetail-scriptorium",
        description=_DESCRIPTION,
        epilog=_EPILOGUE,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "topic",
        metavar="TOPIC",
        help="what the session is about, as a slug: lowercase, digits, hyphens",
    )
    parser.add_argument(
        "--scratch-dir",
        metavar="DIR",
        help="where the scratch file lives, overriding $DOVETAIL_SCRATCH_DIR",
    )
    parser.add_argument(
        "--repl",
        metavar="COMMAND",
        help="the REPL to run beside the editor, overriding $DOVETAIL_REPL",
    )
    parser.add_argument(
        "--terminal",
        metavar="COMMAND",
        help=(
            "terminal argv prefix, overriding $DOVETAIL_TERMINAL and the "
            "declarative terminal file"
        ),
    )
    return parser


def run(argv: list[str] | None = None, environ: os._Environ | dict = os.environ) -> int:
    args = _parser().parse_args(argv)

    # Everything that can be refused is refused before anything is
    # started: a bad topic, an unset terminal and an unquotable REPL are
    # all knowable without spawning a process, and half a room left on
    # screen is a worse diagnostic than a message.
    path = scratch.scratch_file(
        args.topic, explicit_directory=args.scratch_dir, environ=environ
    )
    terminal = seams.terminal_argv(args.terminal, environ)
    repl = seams.repl_argv(args.repl, environ)
    scratch.ensure(path)

    compositor = compositor_module.detect(environ)

    editor_tile = _open_tile(
        terminal + seams.editor_argv(path, None, environ),
        compositor,
        consequence=_NO_EDITOR,
        what="editor",
    )

    # Ask the compositor to put the next window beside this one, rather
    # than moving it afterwards. See `Sway.split_beside`.
    if compositor is not None and editor_tile.con_id is not None:
        compositor.split_beside(editor_tile.con_id)

    repl_tile = _open_tile(
        terminal + repl, compositor, consequence=_NO_REPL, what="REPL"
    )

    if compositor is None:
        _warn(
            "no compositor was reachable, so the two windows were opened but "
            "not arranged; they are wherever your window manager put them"
        )
    else:
        _arrange(compositor, editor_tile.con_id, repl_tile.con_id)

    # Waited for last, because it is the longest of the waits and the
    # room is already on screen and usable while it happens.
    socket = seams.await_socket(editor_tile.pid, environ)
    if socket is None:
        raise DovetailError(
            "the room is open, but the editor published no socket within "
            f"{seams.SOCKET_TIMEOUT:.0f} seconds, so there is nothing for an "
            "agent to co-edit through. The scratch file is at "
            f"{path} and the windows are yours to close."
        )

    print(f"socket {socket}")
    print(f"file {path}")
    return 0


@dataclass(frozen=True)
class Tile:
    """One half of the room: the process started, and the window it got.

    `con_id` is None when there is no compositor to ask, which is the
    only case in which the room is built without knowing where anything
    is.
    """

    pid: int
    con_id: int | None


def _open_tile(
    argv: list[str], compositor: object | None, *, consequence: str, what: str
) -> Tile:
    """Start one tile and confirm it produced a window.

    Fails loudly if the window never appears while a compositor is
    watching: half a room is not a room, and the caller asked for a
    worksession rather than for whichever half happened to start.
    """

    child = seams.spawn(argv)

    if compositor is None:
        # No window tree to poll, so the child's own liveness is the only
        # signal there is. The layout cannot be built on this path
        # either; `run` says so once, rather than once per tile.
        seams.watch_liveness(child, argv, consequence)
        return Tile(pid=child.pid, con_id=None)

    con_id = seams.wait_for_window(compositor, child)
    if con_id is None:
        seams.raise_if_terminal_died(child, argv, consequence)
        raise DovetailError(
            f"no window appeared for the {what} within "
            f"{compositor_module.NEW_WINDOW_TIMEOUT:.0f} seconds; {consequence}"
        )
    return Tile(pid=child.pid, con_id=con_id)


def _arrange(compositor: object, editor: int | None, repl: int | None) -> None:
    """Check the two tiles came out side by side, and correct what can be.

    Never fails the invocation. The room is usable either way, which is
    what the caller asked for, and a tile in the wrong place is worth a
    line on stderr and nothing more.
    """

    if editor is None or repl is None:
        return

    verdict = layout.assess(compositor.get_tree(), editor, repl)
    if verdict.ok:
        return

    if verdict.swap and compositor.swap_windows(editor, repl):
        verdict = layout.assess(compositor.get_tree(), editor, repl)
        if verdict.ok:
            return

    _warn(
        f"the two tiles are not side by side: {verdict.complaint}. "
        "They are both open; move them as you like."
    )


def _warn(message: str) -> None:
    print(f"dovetail-scriptorium: {message}", file=sys.stderr)


def main(argv: list[str] | None = None) -> int:
    try:
        return run(argv)
    except DovetailError as exc:
        print(f"dovetail-scriptorium: {exc}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        return 130


if __name__ == "__main__":
    sys.exit(main())
