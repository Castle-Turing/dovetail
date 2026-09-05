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

# How long to watch a spawned terminal for a quick death when there is no
# compositor to ask about a window at all. There is no window tree to
# poll on this path, only the child's own exit status, so this is a much
# shorter budget than the float step's window wait: it exists to catch a
# terminal that fails immediately — a broken $DOVETAIL_TERMINAL, bad
# arguments — not to prove that a window will eventually appear. A
# terminal still alive when the budget expires is presumed fine, the same
# way a terminal that daemonizes and hands off to an already-running
# server is presumed fine on the float path.
NO_COMPOSITOR_LIVENESS_BUDGET = 2.0

_LIVENESS_POLL_INTERVAL = 0.05

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

    if compositor is not None:
        # The wait is the launch confirmation, not the floating: it runs
        # whether or not `--no-float` was given, because it is the only
        # thing that distinguishes "the terminal died" from "the window
        # just hasn't mapped yet". `--no-float` skips only the
        # `floating enable` call once a window has been found. `alive`
        # cuts the wait short once the child has exited: a terminal that
        # hands off to an already-running server exits 0 right away, and
        # without this the wait would burn its whole budget on a launch
        # that already succeeded, purely because the window it should
        # have found belongs to a process this pid tree will never reach.
        con_id = compositor.wait_for_window(
            lambda: _spawned_pids(child.pid),
            compositor_module.NEW_WINDOW_TIMEOUT,
            alive=lambda: child.poll() is None,
        )
        if con_id is None:
            _report_no_window(child, argv, float_window=float_window)
        elif float_window and not compositor.float_window(con_id):
            _report_unplaced()
    else:
        # No tree to poll at all, so the child's own liveness is the only
        # signal available.
        _watch_liveness(child, argv)

    if not want_socket:
        return None
    return _await_socket(child.pid, environ)


def _spawned_pids(pid: int) -> set[int]:
    """The spawned process and everything descended from it, right now.

    A terminal may fork or re-exec before it maps a window, so the
    window's process is not necessarily the one we started.
    """

    return {pid} | set(descendant_depths(processes.read_process_table(), pid))


def _report_no_window(
    child: subprocess.Popen, argv: list[str], *, float_window: bool
) -> None:
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
    if float_window:
        _report_unplaced()
    else:
        _report_window_not_seen()


def _report_unplaced() -> None:
    # The file is open, which is what the caller asked for. Failing the
    # whole invocation over placement would be worse than a window in
    # the wrong place.
    print(
        "dovetail-show: could not float the new window; "
        "it has been left where the compositor put it",
        file=sys.stderr,
    )


def _report_window_not_seen() -> None:
    # --no-float never asked for the window to be floated, so the file is
    # exactly where the caller told the tool to leave it; this is worth a
    # word on stderr only because the window taking this long is unusual.
    print(
        "dovetail-show: no window was seen for the new terminal within "
        f"{compositor_module.NEW_WINDOW_TIMEOUT:.0f} seconds",
        file=sys.stderr,
    )


def _watch_liveness(
    child: subprocess.Popen,
    argv: list[str],
    budget: float = NO_COMPOSITOR_LIVENESS_BUDGET,
    *,
    interval: float = _LIVENESS_POLL_INTERVAL,
    monotonic=time.monotonic,
    sleep=time.sleep,
) -> None:
    """Fail loudly if `child` dies within `budget`; otherwise say nothing.

    There is no compositor to ask about a window, so the child process is
    the only signal available. A clean exit (status 0) is not treated as
    a failure here, for the same reason `_report_no_window` does not
    treat one as a failure: a terminal that hands off to an
    already-running server and exits 0 immediately is a documented,
    harmless case, indistinguishable from this vantage point from a
    terminal that quietly failed without setting an exit status.
    """

    deadline = monotonic() + budget
    while True:
        status = child.poll()
        if status is not None:
            if status != 0:
                raise ShowError(
                    f"the terminal command {argv[0]!r} exited with status "
                    f"{status} within {budget:g}s of being started; the "
                    "file was not shown"
                )
            return
        remaining = deadline - monotonic()
        if remaining <= 0:
            return
        sleep(min(interval, remaining))


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
