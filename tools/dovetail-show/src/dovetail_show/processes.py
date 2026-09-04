"""The local process table, read from /proc.

Only two things are needed of it — every live pid, and each one's
parent — so that `targeting` can ask which processes are running inside
the focused window. Everything Linux-specific about that question lives
here.
"""

from __future__ import annotations

import os


def parse_ppid(stat: str) -> int | None:
    """The parent pid from the contents of /proc/<pid>/stat.

    Field 2 is the executable name in parentheses, and it can contain
    both spaces and parentheses — `(my (odd) program)` is a legal comm —
    so the fields are counted from after the *last* close paren, never
    by splitting the whole line. Field 3 is then the state and field 4
    the parent pid.
    """

    end = stat.rfind(")")
    if end == -1:
        return None
    fields = stat[end + 1 :].split()
    if len(fields) < 2:
        return None
    try:
        return int(fields[1])
    except ValueError:
        return None


def read_process_table(proc: str = "/proc") -> dict[int, int]:
    """A snapshot of pid -> parent pid for every process we can read.

    Processes that exit while the directory is being walked are skipped:
    a torn snapshot is normal and is not worth failing over, because the
    worst it can do is fail to find an editor that has just died.
    """

    table: dict[int, int] = {}
    try:
        entries = os.listdir(proc)
    except OSError:
        return table

    for entry in entries:
        if not entry.isdigit():
            continue
        try:
            # Read bytes and decode leniently. A process name is whatever
            # bytes its process chose, so a `comm` containing invalid
            # UTF-8 is unusual but entirely legal — and decoding strictly
            # would raise UnicodeDecodeError, which is not an OSError, so
            # one such process anywhere on the machine would take down all
            # of discovery rather than being skipped. Replacement
            # characters cannot hurt: the parse counts fields after the
            # last close paren and never looks at the name.
            with open(os.path.join(proc, entry, "stat"), "rb") as handle:
                ppid = parse_ppid(handle.read().decode("utf-8", errors="replace"))
        except OSError:
            continue
        if ppid is not None:
            table[int(entry)] = ppid
    return table
