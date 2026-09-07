"""A stand-in terminal that allocates a pty, types, and writes it down.

This is what fills `dovetail-run`'s terminal slot in the `run-prompt`
check: it takes an argv the way `foot -e` does, runs it under a
pseudo-terminal, waits for the prompt to be drawn, types `$PTY_KEYS` at
it, and writes every byte the prompt drew to `$PTY_CAPTURE`.

It is deliberately not part of the shipped package. A resident's
terminal is hers; this exists so that a machine with no display can
still press Enter.
"""

from __future__ import annotations

import codecs
import fcntl
import os
import pty
import select
import struct
import sys
import termios
import time

# Wide enough that no line under test is wrapped by the pty, because the
# check compares the drawn line to the proposed one byte for byte.
COLUMNS = 400
ROWS = 50

TIMEOUT = 60.0

PROMPT = b"$ "
HOLD_OPEN = b"Press Enter to close"


def keys() -> bytes:
    """The keystrokes to type, as an escaped string in the environment."""

    raw = os.environ.get("PTY_KEYS", "")
    return codecs.decode(raw, "unicode_escape").encode("utf-8")


def main() -> int:
    argv = sys.argv[1:]
    if not argv:
        print("pty-terminal: nothing to run", file=sys.stderr)
        return 2

    capture = os.environ["PTY_CAPTURE"]
    pid, fd = pty.fork()
    if pid == 0:
        os.execvp(argv[0], argv)
        raise SystemExit(127)

    fcntl.ioctl(fd, termios.TIOCSWINSZ, struct.pack("HHHH", ROWS, COLUMNS, 0, 0))

    drawn = bytearray()
    typed = False
    closed = False
    deadline = time.monotonic() + TIMEOUT
    while time.monotonic() < deadline:
        ready, _, _ = select.select([fd], [], [], 0.2)
        if ready:
            try:
                block = os.read(fd, 4096)
            except OSError:
                break
            if not block:
                break
            drawn += block
        if not typed and PROMPT in drawn:
            # A moment for readline to finish drawing the pre-filled
            # line before anything is typed at it.
            time.sleep(0.2)
            os.write(fd, keys())
            typed = True
        elif typed and not closed and HOLD_OPEN in drawn:
            os.write(fd, b"\r")
            closed = True

    os.close(fd)
    _, status = os.waitpid(pid, 0)

    # Written last and in one go, so that the check can wait for the
    # file to exist and know the whole transcript is in it.
    with open(capture, "wb") as handle:
        handle.write(bytes(drawn))
    return os.waitstatus_to_exitcode(status)


if __name__ == "__main__":
    sys.exit(main())
