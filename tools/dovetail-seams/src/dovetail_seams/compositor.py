"""The compositor seam. Sway is the only compositor implemented.

Six things are asked of a compositor, and they are the whole of the
interface. Two are questions — which window has focus, which window
belongs to a process we just started — and four are instructions: float
this window, focus this window, split this window horizontally so the
next one opens beside it, and swap these two windows. A stranger on
Hyprland or River adds a class beside `Sway` answering those six, and
teaches `detect()` to return it; nothing outside this file needs to
change, and in particular no verb ever writes a line of Sway command
syntax.

Not reaching a compositor is never an error here. `$SWAYSOCK` unset or
`swaymsg` missing means "no focused editor was found", and the targeting
rule falls through to launching one.

The second question is answered by asking repeatedly rather than by
subscribing to events. That is not a simplification for its own sake:
`swaymsg -t subscribe` never reports the subscription being
established — it consumes Sway's reply and prints only events, in both
raw and pretty modes — so there is no moment at which a caller can know
it is listening, and a window mapped in the gap is simply never seen. A
state that is polled has no such gap: the window is either in the tree
or it is not yet, and asking again costs one local socket round trip.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import time
from typing import Callable, Container

# How long to wait for the compositor to report the window belonging to
# a terminal we just spawned. A terminal that maps a window at all does
# it in well under a second; five seconds is slow-machine headroom, and
# the cost of overrunning it is a tiled window rather than a failure.
NEW_WINDOW_TIMEOUT = 5.0

# How often to ask, while waiting for that window. Each ask is one
# `swaymsg -t get_tree` over a local socket; a tenth of a second is far
# below the threshold at which a person notices a window being placed.
POLL_INTERVAL = 0.1

# A single swaymsg query. It talks to a socket on the same machine.
QUERY_TIMEOUT = 5.0


class Sway:
    """The Sway compositor, driven over `swaymsg`."""

    name = "sway"

    def __init__(self, swaymsg: str) -> None:
        self._swaymsg = swaymsg

    def get_tree(self, timeout: float = QUERY_TIMEOUT) -> object | None:
        """The window tree as parsed JSON, or None if it cannot be had.

        `timeout` is settable so that a caller working to a deadline of
        its own can hand down what is left of it rather than granting a
        fresh allowance to every query.
        """

        try:
            done = subprocess.run(
                [self._swaymsg, "-t", "get_tree", "-r"],
                capture_output=True,
                text=True,
                timeout=timeout,
            )
        except (OSError, subprocess.SubprocessError):
            return None
        if done.returncode != 0:
            return None
        try:
            return json.loads(done.stdout)
        except json.JSONDecodeError:
            return None

    def wait_for_window(
        self,
        pids: Callable[[], Container[int]],
        timeout: float,
        *,
        interval: float = POLL_INTERVAL,
        monotonic=time.monotonic,
        sleep=time.sleep,
        alive: Callable[[], bool] | None = None,
    ) -> int | None:
        """The container id of a window owned by one of `pids()`, or None.

        `pids` is called afresh on every attempt, and returns a set
        rather than one process id, because a terminal is free to fork
        or re-exec before it maps anything: the window can belong to a
        descendant that did not exist when the wait began.

        None means the window never appeared within `timeout`, which
        costs a window in the wrong place and nothing else.

        `timeout` bounds the whole wait, not each attempt. Every query
        and every sleep is clamped to what is left of it, because a
        query that hangs is exactly the case where a per-attempt
        allowance would let this run to twice its documented budget
        while the caller waits for a window it was promised in five
        seconds.

        `alive`, when given, ends the wait the moment it reports false,
        rather than at the full timeout. A spawned process that has
        already exited cannot go on to map a window under `pids()` — a
        dead process is not a parent descendants get discovered through
        — so once the caller confirms it is gone, more polling only
        delays the answer, it cannot change it.
        """

        deadline = monotonic() + timeout
        while True:
            remaining = deadline - monotonic()
            if remaining <= 0:
                return None
            con_id = window_for_pids(
                self.get_tree(timeout=min(QUERY_TIMEOUT, remaining)), pids()
            )
            if con_id is not None:
                return con_id
            if alive is not None and not alive():
                return None
            remaining = deadline - monotonic()
            if remaining <= 0:
                return None
            sleep(min(interval, remaining))

    def _command(self, *argv: str) -> bool:
        """Issue one command. True if the compositor said it succeeded.

        Never raises: every caller of a compositor instruction treats
        failure as "the window is where the compositor left it", which
        is a warning at worst and never a reason to fail an invocation
        that has already put something on screen.
        """

        try:
            done = subprocess.run(
                [self._swaymsg, "-r", *argv],
                capture_output=True,
                text=True,
                timeout=QUERY_TIMEOUT,
            )
        except (OSError, subprocess.SubprocessError):
            return False
        return done.returncode == 0

    def float_window(self, con_id: int) -> bool:
        """Make one container float."""

        return self._command(f"[con_id={con_id}]", "floating", "enable")

    def focus_window(self, con_id: int) -> bool:
        """Give one container focus."""

        return self._command(f"[con_id={con_id}]", "focus")

    def split_beside(self, con_id: int) -> bool:
        """Arrange for the next new window to open to the right of this one.

        Sway opens a new window as a sibling of the focused container, in
        the direction that container's parent is split. So this focuses
        the container and sets a horizontal split on it: the container is
        wrapped in a split of its own, and the next window to map becomes
        its right-hand sibling. Any other windows already on the
        workspace keep the space they had.

        This is placement by asking the compositor to do what it already
        does, rather than by moving a window after the fact — there is no
        `move` command whose result does not depend on where the window
        happened to land first.
        """

        return self.focus_window(con_id) and self._command("splith")

    def swap_windows(self, first: int, second: int) -> bool:
        """Exchange the positions of two containers."""

        return self._command(
            f"[con_id={first}]", "swap", "container", "with", "con_id", str(second)
        )


def window_for_pids(tree: object, pids: Container[int]) -> int | None:
    """The container id of the first window owned by one of `pids`.

    Pure: it walks a tree it is handed and reads nothing else, so every
    shape a real tree can take — a window nested under workspaces, a
    window already floating, a tree with no windows at all — is testable
    without a compositor.
    """

    stack = [tree]
    while stack:
        node = stack.pop()
        if not isinstance(node, dict):
            continue
        pid = node.get("pid")
        con_id = node.get("id")
        if isinstance(pid, int) and pid in pids and isinstance(con_id, int):
            return con_id
        for key in ("nodes", "floating_nodes"):
            children = node.get(key)
            if isinstance(children, list):
                stack.extend(children)
    return None


def detect(environ: os._Environ | dict = os.environ) -> Sway | None:
    """The compositor we are running under, or None.

    None is an ordinary answer, not a failure: it means the tool cannot
    tell what has focus and cannot place a window, so it opens the file
    in a new instance and lets the resident put it where she likes.
    """

    if not environ.get("SWAYSOCK"):
        return None
    swaymsg = shutil.which("swaymsg")
    if swaymsg is None:
        return None
    return Sway(swaymsg)
