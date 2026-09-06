"""The run verb's launch step: a terminal holding the prompt, floating.

The machinery — resolving the terminal slot, spawning, waiting for a
window, watching a terminal that dies — is shared with every other verb
and lives in `dovetail_seams.launch`. What is here is only what *run*
does with it, and that is nearly what *show* does: float the window if
asked, never fail an invocation over placement, and fail loudly when the
terminal died instead of opening anything.

The difference from `show` is what the failure means. A show that does
not open leaves a file unread; a run that does not open leaves a command
nobody was asked about — so the diagnostic says the command was not
proposed, and the caller is expected to notice that the answer it is
waiting for will never come.
"""

from __future__ import annotations

import sys

from dovetail_seams import compositor as compositor_module
from dovetail_seams import launch as seams

NO_COMPOSITOR_LIVENESS_BUDGET = seams.NO_COMPOSITOR_LIVENESS_BUDGET

_NOT_PROPOSED = "the command was not put in front of anyone"


def launch(
    terminal: list[str],
    wrapper: list[str],
    *,
    float_window: bool = True,
    compositor: object | None = None,
) -> None:
    """Open a terminal running `wrapper`, and confirm that it opened.

    `terminal` is the resident's argv prefix, already resolved (`foot
    -e`, `wezterm start --`), and the wrapper is appended to it as
    further argv elements, so no shell parses anything on this path. It
    arrives resolved because an unset terminal is refused before any of
    this runs.
    """

    argv = terminal + wrapper
    child = seams.spawn(argv)

    if compositor is not None:
        # The wait is the launch confirmation, not the floating: it runs
        # whether or not `--no-float` was given, because it is the only
        # thing that distinguishes "the terminal died" from "the window
        # just hasn't mapped yet".
        con_id = seams.wait_for_window(compositor, child)
        if con_id is None:
            seams.raise_if_terminal_died(child, argv, _NOT_PROPOSED)
            if float_window:
                _report_unplaced()
            else:
                _report_window_not_seen()
        elif float_window and not compositor.float_window(con_id):
            _report_unplaced()
    else:
        # No tree to poll at all, so the child's own liveness is the only
        # signal available.
        seams.watch_liveness(child, argv, _NOT_PROPOSED)


def _report_unplaced() -> None:
    # The prompt is up, which is what the caller asked for. Failing the
    # whole invocation over placement would be worse than a window in
    # the wrong place.
    print(
        "dovetail-run: could not float the new window; "
        "it has been left where the compositor put it",
        file=sys.stderr,
    )


def _report_window_not_seen() -> None:
    print(
        "dovetail-run: no window was seen for the new terminal within "
        f"{compositor_module.NEW_WINDOW_TIMEOUT:.0f} seconds",
        file=sys.stderr,
    )
