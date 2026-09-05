"""The show verb's launch step: a new editor, floating, in a terminal.

The machinery — resolving the terminal slot, spawning, waiting for a
window, waiting for a socket — is shared with every other verb and lives
in `dovetail_seams.launch`. What is here is only what *show* does with
it: float the window if asked, and never fail an invocation over
placement when the file is open regardless.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

from dovetail_seams import compositor as compositor_module
from dovetail_seams import launch as seams

# Re-exported so `docs/show.md`'s timeout table has one place to point at
# and the verb's diagnostics can quote the number they waited.
SOCKET_TIMEOUT = seams.SOCKET_TIMEOUT
NO_COMPOSITOR_LIVENESS_BUDGET = seams.NO_COMPOSITOR_LIVENESS_BUDGET

_NOT_SHOWN = "the file was not shown"


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

    Only `--print-socket` needs the socket, and only there is it waited
    for.
    """

    argv = seams.terminal_argv(terminal, environ) + seams.editor_argv(
        path, line, environ
    )
    child = seams.spawn(argv)

    if compositor is not None:
        # The wait is the launch confirmation, not the floating: it runs
        # whether or not `--no-float` was given, because it is the only
        # thing that distinguishes "the terminal died" from "the window
        # just hasn't mapped yet". `--no-float` skips only the
        # `floating enable` call once a window has been found.
        con_id = seams.wait_for_window(compositor, child)
        if con_id is None:
            seams.raise_if_terminal_died(child, argv, _NOT_SHOWN)
            if float_window:
                _report_unplaced()
            else:
                _report_window_not_seen()
        elif float_window and not compositor.float_window(con_id):
            _report_unplaced()
    else:
        # No tree to poll at all, so the child's own liveness is the only
        # signal available.
        seams.watch_liveness(child, argv, _NOT_SHOWN)

    if not want_socket:
        return None
    return seams.await_socket(child.pid, environ)


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
