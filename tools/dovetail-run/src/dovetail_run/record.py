"""The record: what was proposed, and what the resident actually ran.

Two things live here, and they are pure on purpose so both are checkable
without a terminal: `check_record_path`, which is `cli.py`'s refusal for
a `--record` PATH whose parent directory does not exist, and
`build_record`, which is the one dict shape the JSON file ever takes.

The third thing, `main`, is not pure — it is a standalone script, shipped
as package data beside `prompt.bash` rather than imported by it, because
the wrapper outlives `dovetail-run` itself. The verb returns as soon as
the prompt is on screen; only the wrapper is still running when the
resident finally presses Enter, so the wrapper is what has to call this
file, by an absolute interpreter path baked in the same way `bash` is
substituted into `defaults.py` — the resident's terminal may put no
Python at all, or a different one, on its `$PATH`.

`main` takes its nine fields positionally rather than as `--flags`,
because a proposed or executed command is free to start with a dash
("`-rf /tmp/x`" is a plausible whole line to propose), and argparse's
option-matching would rather guess than take that literally.
"""

from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path

from dovetail_seams.errors import DovetailError

_FIELD_COUNT = 9


def check_record_path(path: str) -> Path:
    """`path`, or a refusal naming it, if its parent directory is missing.

    Checked before the terminal is spawned, alongside the other things
    this verb can know without starting a process. Creating the
    directory instead would be a guess about the caller's layout that
    `dovetail-run` has no business making.
    """

    record_path = Path(path)
    if not record_path.parent.is_dir():
        raise DovetailError(
            f"--record {path}: the parent directory does not exist; "
            "dovetail-run will not create it for you"
        )
    return record_path


def build_record(
    *,
    proposed: str,
    executed: str | None,
    declined: bool,
    exit_status: int | None,
    from_: str | None,
    why: str | None,
    proposed_at: str,
    finished_at: str,
) -> dict:
    """The one JSON object this verb ever writes, as a plain dict.

    Field order here is the field order in `docs/run.md` and in the
    file on disk — not load-bearing to a JSON parser, but a human
    reading the record with their eyes gets the story in the order it
    happened: what was proposed, what ran, whether it was declined, and
    how it went.
    """

    return {
        "proposed": proposed,
        "executed": executed,
        "declined": declined,
        "exit_status": exit_status,
        "from": from_,
        "why": why,
        "proposed_at": proposed_at,
        "finished_at": finished_at,
    }


def write(path: Path, record: dict) -> None:
    """Write `record` to `path` via a same-directory temp file and rename.

    The rename is what makes the write atomic: a poller opening `path`
    either does not find it yet, or finds it complete. It never finds a
    file that is still being written, because it is never looking at
    that file — `os.replace` swaps the whole name over in one step.
    """

    directory = path.parent
    fd, temp_name = tempfile.mkstemp(dir=directory, prefix=f".{path.name}.", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(json.dumps(record, ensure_ascii=False, indent=2))
            handle.write("\n")
        os.replace(temp_name, path)
    except BaseException:
        os.unlink(temp_name)
        raise


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    if len(argv) != _FIELD_COUNT:
        print(
            f"record.py: expected {_FIELD_COUNT} arguments, got {len(argv)}",
            file=sys.stderr,
        )
        return 2

    (
        path,
        declined_flag,
        proposed,
        executed,
        exit_status,
        from_,
        why,
        proposed_at,
        finished_at,
    ) = argv

    declined = declined_flag == "true"
    record = build_record(
        proposed=proposed,
        executed=None if declined else executed,
        declined=declined,
        exit_status=None if declined else int(exit_status),
        from_=from_ or None,
        why=why or None,
        proposed_at=proposed_at,
        finished_at=finished_at,
    )

    try:
        write(Path(path), record)
    except OSError as exc:
        print(f"record.py: could not write {path}: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
