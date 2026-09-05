"""Starting a new editor, in a terminal, as a floating window.

The terminal is private configuration and Dovetail never guesses one:
it is an argv prefix the resident supplies, and the editor invocation is
appended to it as trailing arguments, so `foot -e` and `wezterm start --`
both work without Dovetail knowing either exists.
"""

from __future__ import annotations

import os
import shlex
import subprocess
import sys
import time
from pathlib import Path

from . import compositor as compositor_module
from . import editor as editor_module
from . import processes
from .defaults import DEFAULT_EDITOR
from .errors import ShowError
from .targeting import descendant_depths

# How long to wait for a launched instance to publish its socket, when
# --print-socket asked for it. The socket appears asynchronously, some
# way into Neovim's startup, and a cold start off a spinning disk is the
# case this has to cover; ten seconds is well past a warm start's
# fraction of a second.
SOCKET_TIMEOUT = 10.0

_SOCKET_POLL_INTERVAL = 0.1

_NO_TERMINAL = """no terminal is configured, and Dovetail will not guess one

Set $DOVETAIL_TERMINAL (or $TERMINAL) to the command that runs a program
in a new terminal window, as an argv prefix. For example:

    export DOVETAIL_TERMINAL="foot -e"
    export DOVETAIL_TERMINAL="wezterm start --"

or pass it for one invocation with --terminal."""


def terminal_argv(
    explicit: str | None, environ: os._Environ | dict = os.environ
) -> list[str]:
    """The argv prefix that runs a command in a new terminal window.

    `--terminal`, then `$DOVETAIL_TERMINAL`, then `$TERMINAL`. Never a
    hardcoded fallback: a wrong terminal is worse than a clear refusal,
    and there is no terminal every reader of this file has installed.
    """

    names = ("--terminal", "$DOVETAIL_TERMINAL", "$TERMINAL")
    values = (explicit, environ.get("DOVETAIL_TERMINAL"), environ.get("TERMINAL"))
    for name, source in zip(names, values):
        if source and source.strip():
            try:
                argv = shlex.split(source)
            except ValueError as exc:
                # An unmatched quote. Naming the setting matters: three
                # places can supply this, and a traceback would say which
                # line of Python failed rather than which of them is
                # malformed.
                raise ShowError(
                    f"{name} is not valid shell quoting ({exc}): {source}"
                ) from exc
            if argv:
                return argv
    raise ShowError(_NO_TERMINAL)


def editor_command(environ: os._Environ | dict = os.environ) -> str:
    """The editor to launch: the build-time default, or the override."""

    override = environ.get("DOVETAIL_EDITOR")
    if override and override.strip():
        return override.strip()
    return DEFAULT_EDITOR


def launch(
    path: Path,
    line: int | None,
    *,
    terminal: str | None = None,
    float_window: bool = True,
    want_socket: bool = False,
    compositor: object | None = None,
    environ: os._Environ | dict = os.environ,
) -> str | None:
    """Open `path` in a new editor. Returns its socket if one was wanted.

    The filename goes on the editor's command line rather than being
    sent over RPC after the fact. The socket appears asynchronously some
    way into startup — a listing taken immediately after spawning finds
    no directory at all — so a spawn-then-connect implementation would
    race for no benefit. Only --print-socket needs the socket, and only
    there is it waited for.
    """

    argv = terminal_argv(terminal, environ) + editor_module.launch_argv(
        editor_command(environ), path, line
    )

    # The editor gets a window, not the caller's pipes. Inheriting them
    # makes this tool unusable from anything that reads its output: the
    # reader blocks until the window is closed, because the terminal is
    # still holding the write end, and a reader that gives up first can
    # kill the editor. A new session on top of that keeps the terminal
    # from taking a signal meant for whoever invoked us.
    try:
        child = subprocess.Popen(
            argv,
            start_new_session=True,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except OSError as exc:
        raise ShowError(f"could not run the terminal command {argv[0]!r}: {exc}")

    if float_window and compositor is not None:
        con_id = compositor.wait_for_window(
            lambda: _spawned_pids(child.pid),
            compositor_module.NEW_WINDOW_TIMEOUT,
        )
        if con_id is None:
            _report_no_window(child, argv)
        elif not compositor.float_window(con_id):
            _report_unplaced()

    if not want_socket:
        return None
    return _await_socket(child.pid, environ)


def _spawned_pids(pid: int) -> set[int]:
    """The spawned process and everything descended from it, right now.

    A terminal may fork or re-exec before it maps a window, so the
    window's process is not necessarily the one we started.
    """

    return {pid} | set(descendant_depths(processes.read_process_table(), pid))


def _report_no_window(child: subprocess.Popen, argv: list[str]) -> None:
    """Say what happened when no window ever appeared.

    A terminal that exits instead of mapping a window is the case worth
    distinguishing: nothing opened at all, and reporting only that the
    window could not be placed would describe a file the resident cannot
    see as a cosmetic problem.
    """

    status = child.poll()
    if status is not None and status != 0:
        raise ShowError(
            f"the terminal command {argv[0]!r} exited with status {status} "
            f"without opening a window; the file was not shown"
        )
    _report_unplaced()


def _report_unplaced() -> None:
    # The file is open, which is what the caller asked for. Failing the
    # whole invocation over placement would be worse than a window in
    # the wrong place.
    print(
        "dovetail-show: could not float the new window; "
        "it has been left where the compositor put it",
        file=sys.stderr,
    )


def _await_socket(
    terminal_pid: int, environ: os._Environ | dict = os.environ
) -> str | None:
    """Poll for a reachable instance running under the spawned terminal.

    Matching on descent rather than on "a socket that was not there
    before" keeps the answer right when another instance happens to
    start at the same moment.
    """

    deadline = time.monotonic() + SOCKET_TIMEOUT
    while True:
        depths = descendant_depths(processes.read_process_table(), terminal_pid)
        for instance in editor_module.list_instances(environ):
            if instance.pid in depths and editor_module.is_reachable(instance.socket):
                return instance.socket
        if time.monotonic() >= deadline:
            return None
        time.sleep(_SOCKET_POLL_INTERVAL)
