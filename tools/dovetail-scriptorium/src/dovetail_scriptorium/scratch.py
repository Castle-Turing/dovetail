"""Where the scratch file lives, and what it is called.

Pure: every function here takes its date, its environment and its
overrides as arguments and touches the filesystem only in `ensure`, so
the whole convention is testable without a home directory, a compositor
or an editor.

The convention, in one line: `<YYYY-MM-DD>-<topic>.md`, in a directory
the resident names. It is written down so that a resident can find
yesterday's thinking with `ls`, and so that an agent that is told a
topic can name the file without being told the path.
"""

from __future__ import annotations

import datetime
import os
import re
from pathlib import Path

from dovetail_seams.errors import DovetailError

# Lowercase letters and digits in hyphen-separated runs. Deliberately
# stricter than "the characters a-z0-9- only": `-notes`, `notes-` and
# `two--hyphens` are all typos rather than intentions, and a filename is
# cheap to get right at the moment it is typed and annoying to rename
# afterwards. Refusing is always safe here — nothing has been created
# yet — and the refusal names the rule.
_TOPIC = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")

_TOPIC_REFUSAL = """the topic {topic!r} is not a slug, and Dovetail will not guess one for you

A topic is lowercase letters and digits in hyphen-separated runs, so
that the file it names is predictable: `parser-rewrite`, `m2-layout`,
`0006`. Try:

    {suggestion}

It is not transformed for you on purpose. A caller who typed spaces
wants to know what the file will be called now, not to discover a guess
later."""

# The application's own directory under whichever data home applies, so
# that a resident who has never configured anything still gets her
# scratch files in one predictable place rather than scattered.
_UNDER_DATA_HOME = ("dovetail", "scratch")

_NO_HOME = """cannot work out where to put the scratch file

Set $DOVETAIL_SCRATCH_DIR to the directory scratch files belong in, or
pass --scratch-dir for one invocation. The default needs $XDG_DATA_HOME
or $HOME, and neither is set."""


def validate_topic(topic: str) -> str:
    """The topic, unchanged, or a refusal that says what a topic is."""

    if _TOPIC.match(topic):
        return topic
    raise DovetailError(
        _TOPIC_REFUSAL.format(topic=topic, suggestion=_suggest(topic) or "notes")
    )


def _suggest(topic: str) -> str:
    """What the caller probably meant, shown but never silently used."""

    slug = re.sub(r"[^a-z0-9]+", "-", topic.strip().lower()).strip("-")
    return slug


def file_name(date: datetime.date, topic: str) -> str:
    """`<YYYY-MM-DD>-<topic>.md`.

    The date leads so that a directory listing sorts chronologically,
    which is the order a resident looks for these in. Markdown because
    the room is for prose first: pseudocode and Python live in fenced
    blocks, and the REPL beside it is where code is actually run.
    """

    return f"{date.isoformat()}-{validate_topic(topic)}.md"


def directory(
    explicit: str | None = None, environ: os._Environ | dict = os.environ
) -> Path:
    """Where scratch files live, by the documented chain.

    `--scratch-dir`, then `$DOVETAIL_SCRATCH_DIR`, then
    `$XDG_DATA_HOME/dovetail/scratch`, then
    `~/.local/share/dovetail/scratch`.

    Unlike the terminal, this slot has a default rather than a refusal:
    a resident who has configured nothing should still be able to type
    one word and get a room. `$XDG_DATA_HOME` and not `$XDG_STATE_HOME`
    because the specification gives the state home logs-and-history
    semantics, and these are durable documents the resident is expected
    to come back to.
    """

    for source in (explicit, environ.get("DOVETAIL_SCRATCH_DIR")):
        if source and source.strip():
            return Path(source.strip()).expanduser()

    data_home = environ.get("XDG_DATA_HOME")
    # The specification says an $XDG_DATA_HOME that is unset, empty, or
    # not an absolute path must be treated as unset. Honouring that here
    # means a relative setting falls through to the home default rather
    # than creating a `dovetail/scratch` under whatever directory the
    # caller happened to be in.
    if data_home and data_home.strip().startswith("/"):
        return Path(data_home.strip(), *_UNDER_DATA_HOME)

    home = environ.get("HOME")
    if home and home.strip():
        return Path(home.strip(), ".local", "share", *_UNDER_DATA_HOME)

    raise DovetailError(_NO_HOME)


def ensure(path: Path) -> Path:
    """Make sure `path` exists, without ever changing what is in it.

    Reopening is the point of this verb, so the one thing that must not
    happen is a truncation: `O_CREAT` without `O_TRUNC` creates the file
    if it is absent and is a no-op if it is not — not even the
    modification time moves. The file is created empty and Dovetail
    never writes a line into it; the first line is the resident's.

    Directories are created 0700 and the file 0600. A scratch file is
    the resident's unfinished thinking, and the default umask on a
    multi-user machine is not a decision this should inherit silently.
    """

    parent = path.parent
    try:
        parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    except OSError as exc:
        raise DovetailError(f"could not create the scratch directory {parent}: {exc}")

    try:
        handle = os.open(path, os.O_CREAT | os.O_WRONLY, 0o600)
    except OSError as exc:
        raise DovetailError(f"could not create the scratch file {path}: {exc}")
    os.close(handle)
    return path


def scratch_file(
    topic: str,
    *,
    explicit_directory: str | None = None,
    today: datetime.date | None = None,
    environ: os._Environ | dict = os.environ,
) -> Path:
    """The absolute path of the scratch file for `topic`, today.

    Absolute, because the editor instance's working directory is its own
    business and is rarely the caller's.
    """

    date = today if today is not None else datetime.date.today()
    return (directory(explicit_directory, environ) / file_name(date, topic)).absolute()
