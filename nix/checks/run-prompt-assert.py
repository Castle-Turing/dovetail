"""Assert that the line drawn on the pty is the line that was expected.

`python3 assert.py <capture> <expected>` reads a pty transcript, strips
the escape sequences a terminal would have consumed rather than shown,
finds the prompt line, and compares what was drawn after the `$ ` with
the command the check expects — byte for byte, no normalisation. That
comparison is the whole point of the check: the side effect proves a
command ran, and this proves it is the one the resident could read.
"""

from __future__ import annotations

import re
import sys

# CSI and OSC sequences, plus the two-character escapes readline emits.
# What is left is what a terminal would have put on the screen.
ESCAPES = re.compile(rb"\x1b\][^\x07\x1b]*(?:\x07|\x1b\\)|\x1b\[[0-9;?]*[A-Za-z]|\x1b.")

PROMPT = b"$ "


def drawn_command(transcript: bytes) -> bytes:
    """What the resident saw after the prompt, at the moment she pressed Enter."""

    visible = ESCAPES.sub(b"", transcript)
    for line in visible.replace(b"\r\n", b"\n").split(b"\n"):
        # A carriage return redraws the line in place, so what was on
        # screen is what came after the last one.
        line = line.split(b"\r")[-1]
        if line.startswith(PROMPT):
            return line[len(PROMPT) :]
    raise SystemExit(f"no prompt line in the transcript:\n{transcript!r}")


def main() -> int:
    capture, expected = sys.argv[1], sys.argv[2].encode("utf-8")
    with open(capture, "rb") as handle:
        transcript = handle.read()
    drawn = drawn_command(transcript)
    if drawn != expected:
        print(f"FAIL: the line drawn was {drawn!r}, expected {expected!r}")
        return 1
    print(f"--- drawn and run: {drawn.decode('utf-8', 'replace')}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
