"""The compositor seam. Sway is the only compositor implemented.

Three questions are asked of a compositor, and they are the whole of the
interface: which window has focus, tell me when a new window appears,
and make that window float. A stranger on Hyprland or River adds a class
beside `Sway` answering those three, and teaches `detect()` to return
it; nothing outside this file needs to change.

Not reaching a compositor is never an error here. `$SWAYSOCK` unset or
`swaymsg` missing means "no focused editor was found", and the targeting
rule falls through to launching one.
"""

from __future__ import annotations

import json
import os
import select
import shutil
import subprocess
import time

# How long to wait for the compositor to report the window belonging to
# a terminal we just spawned. A terminal that maps a window at all does
# it in well under a second; five seconds is slow-machine headroom, and
# the cost of overrunning it is a tiled window rather than a failure.
NEW_WINDOW_TIMEOUT = 5.0

# A single swaymsg query. It talks to a socket on the same machine.
QUERY_TIMEOUT = 5.0

# How long to wait for Sway to acknowledge a subscription. This is one
# round trip over a local socket; a second is already generous, and
# overrunning it costs a tiled window rather than a failure.
SUBSCRIBE_TIMEOUT = 1.0


class Sway:
    """The Sway compositor, driven over `swaymsg`."""

    name = "sway"

    def __init__(self, swaymsg: str) -> None:
        self._swaymsg = swaymsg

    def get_tree(self) -> object | None:
        """The window tree as parsed JSON, or None if it cannot be had."""

        try:
            done = subprocess.run(
                [self._swaymsg, "-t", "get_tree", "-r"],
                capture_output=True,
                text=True,
                timeout=QUERY_TIMEOUT,
            )
        except (OSError, subprocess.SubprocessError):
            return None
        if done.returncode != 0:
            return None
        try:
            return json.loads(done.stdout)
        except json.JSONDecodeError:
            return None

    def watch_new_windows(self) -> "_SwayWindowWatch":
        """Start listening for window events.

        Used as a context manager, and entered *before* the terminal is
        spawned: a window can be mapped before a subscription started
        afterwards would have been established.
        """

        return _SwayWindowWatch(self._swaymsg)

    def float_window(self, con_id: int) -> bool:
        """Make one container float. True if the compositor said it did."""

        try:
            done = subprocess.run(
                [self._swaymsg, "-r", f"[con_id={con_id}]", "floating", "enable"],
                capture_output=True,
                text=True,
                timeout=QUERY_TIMEOUT,
            )
        except (OSError, subprocess.SubprocessError):
            return False
        return done.returncode == 0


class _SwayWindowWatch:
    """A live `swaymsg -t subscribe -m '["window"]'`."""

    def __init__(self, swaymsg: str) -> None:
        self._swaymsg = swaymsg
        self._process: subprocess.Popen | None = None
        self._buffer = ""
        self._pending: list[dict] = []

    def __enter__(self) -> "_SwayWindowWatch":
        """Start the subscription, and wait until Sway has acknowledged it.

        Starting the process is not the same as being subscribed: until
        Sway has processed the request it is not sending us anything, and
        a window that maps in that gap is never reported. Sway answers a
        subscription with `{"success": true}` before any event, so
        waiting for that reply closes the window in which a terminal we
        are about to spawn could map unseen.
        """

        try:
            self._process = subprocess.Popen(
                [self._swaymsg, "-t", "subscribe", "-m", "-r", '["window"]'],
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                text=False,
            )
        except OSError:
            self._process = None
            return self

        if not self._await_acknowledgement(SUBSCRIBE_TIMEOUT):
            # No acknowledgement means we cannot claim to be watching.
            # Tear the subscription down and let the caller carry on
            # unplaced, exactly as it does when there is no compositor.
            self.__exit__()
            self._process = None
        return self

    def _await_acknowledgement(self, timeout: float) -> bool:
        """True once Sway has confirmed the subscription."""

        deadline = time.monotonic() + timeout
        while True:
            # What has already arrived is answered before the stream is
            # consulted, so a reply that came in with the first read is
            # not waited on a second time.
            replies = self._drain()
            if replies:
                acknowledgement, rest = replies[0], replies[1:]
                # Anything that arrived alongside the reply is already an
                # event, and dropping it here would reintroduce the race
                # this method exists to close.
                self._pending.extend(rest)
                return acknowledgement.get("success") is True

            if self._process is None or self._process.stdout is None:
                return False
            stream = self._process.stdout

            remaining = deadline - time.monotonic()
            if remaining <= 0:
                return False
            ready, _, _ = select.select([stream], [], [], remaining)
            if not ready:
                return False
            chunk = os.read(stream.fileno(), 1 << 16)
            if not chunk:
                return False
            self._buffer += chunk.decode("utf-8", errors="replace")

    def __exit__(self, *exc_info: object) -> None:
        if self._process is None:
            return
        self._process.terminate()
        try:
            self._process.wait(timeout=QUERY_TIMEOUT)
        except subprocess.TimeoutExpired:
            self._process.kill()

    def wait_for_pid(self, pid: int, timeout: float) -> int | None:
        """The container id of the first new window belonging to `pid`.

        None on timeout, on a subscription that never started, or on a
        compositor that hung up.
        """

        if self._process is None or self._process.stdout is None:
            return None

        deadline = time.monotonic() + timeout
        stream = self._process.stdout
        while True:
            queued, self._pending = self._pending, []
            for event in queued + self._drain():
                if event.get("change") != "new":
                    continue
                container = event.get("container")
                if isinstance(container, dict) and container.get("pid") == pid:
                    con_id = container.get("id")
                    if isinstance(con_id, int):
                        return con_id

            remaining = deadline - time.monotonic()
            if remaining <= 0:
                return None
            ready, _, _ = select.select([stream], [], [], remaining)
            if not ready:
                return None
            chunk = os.read(stream.fileno(), 1 << 16)
            if not chunk:
                return None
            self._buffer += chunk.decode("utf-8", errors="replace")

    def _drain(self) -> list[dict]:
        """Every complete JSON object in the buffer so far.

        Decoded with `raw_decode` rather than split on newlines, so that
        it does not matter whether this swaymsg pretty-prints its events
        or emits one per line.
        """

        decoder = json.JSONDecoder()
        events = []
        while True:
            self._buffer = self._buffer.lstrip()
            if not self._buffer:
                break
            try:
                value, end = decoder.raw_decode(self._buffer)
            except json.JSONDecodeError:
                break
            self._buffer = self._buffer[end:]
            if isinstance(value, dict):
                events.append(value)
        return events


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
