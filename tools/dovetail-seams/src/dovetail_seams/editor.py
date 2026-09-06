"""This is how the Neovim provider implements the verbs.

Every line of this file is Neovim-specific, and it is the only file
in Dovetail's tooling that is. Nothing else knows that the editor speaks msgpack-RPC,
that its sockets are called `nvim-<pid>.sock`, or that a line number is
spelled `+N` on its command line. The vision's fourth starting position
makes the editor a slot rather than a hardcode, and M4 extracts the
contract from the verbs M1 and M2 actually called; that extraction is a
great deal easier if the provider-shaped code already sits behind one
seam.

The client is plain unwrapped Neovim driven over `--server`, exactly as
`nix/checks/headless-socket.nix` drives it, so a verb does not depend
on the configuration whose files it is opening.
"""

from __future__ import annotations

import os
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path

from .defaults import NVIM_CLIENT
from .errors import DovetailError

_SOCKET_NAME = re.compile(r"^nvim-(\d+)\.sock$")


@dataclass(frozen=True)
class Instance:
    """A live editor instance: where to reach it, and what pid it runs as."""

    socket: str
    pid: int


# How long a single RPC call may take before the instance is presumed
# dead. Generous for a local Unix socket, where an answer is a
# round-trip on tmpfs; short enough that ranking through a directory of
# stale sockets stays interactive.
RPC_TIMEOUT = 5.0


def socket_directory(environ: os._Environ | dict = os.environ) -> Path | None:
    """`$XDG_RUNTIME_DIR/dovetail`, or None if there is no runtime dir.

    The scheme is `docs/module.md`'s: one socket per instance, in one
    directory, so discovering instances is "list one directory".
    """

    runtime_dir = environ.get("XDG_RUNTIME_DIR")
    if not runtime_dir:
        return None
    return Path(runtime_dir) / "dovetail"


def list_instances(environ: os._Environ | dict = os.environ) -> list[Instance]:
    """Every socket in the directory, with the pid its name claims.

    Claims, not facts: the listing is never trusted. Each entry is
    connect-and-verified before it is used.
    """

    directory = socket_directory(environ)
    if directory is None:
        return []
    try:
        entries = sorted(directory.iterdir())
    except OSError:
        return []

    instances = []
    for entry in entries:
        match = _SOCKET_NAME.match(entry.name)
        if match:
            instances.append(Instance(socket=str(entry), pid=int(match.group(1))))
    return instances


def _client(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [NVIM_CLIENT, "--clean", "--headless", *args],
        capture_output=True,
        text=True,
        timeout=RPC_TIMEOUT,
    )


def is_reachable(socket: str) -> bool:
    """Connect and ask the instance for something. The verify half of the
    connect-and-verify rule `docs/module.md` requires of every consumer."""

    try:
        done = _client("--server", socket, "--remote-expr", "1 + 1")
    except (OSError, subprocess.SubprocessError):
        return False
    return done.returncode == 0 and done.stdout.strip() == "2"


def open_file(socket: str, path: Path, line: int | None) -> None:
    """Show `path` in the instance listening on `socket`.

    The path must already be absolute: the instance's working directory
    is its own business and is rarely the caller's.
    """

    try:
        done = _client("--server", socket, "--remote", str(path))
    except (OSError, subprocess.SubprocessError) as exc:
        raise DovetailError(f"could not open {path} in the editor at {socket}: {exc}")
    if done.returncode != 0:
        raise DovetailError(
            f"could not open {path} in the editor at {socket}: "
            f"{done.stderr.strip() or 'the editor reported an error'}"
        )

    if line is None:
        return

    try:
        done = _client("--server", socket, "--remote-expr", f"cursor({line}, 1)")
    except (OSError, subprocess.SubprocessError) as exc:
        raise DovetailError(f"opened {path}, but could not move to line {line}: {exc}")
    if done.returncode != 0:
        raise DovetailError(
            f"opened {path}, but could not move to line {line}: "
            f"{done.stderr.strip() or 'the editor reported an error'}"
        )


def launch_argv(editor: str, path: Path, line: int | None) -> list[str]:
    """The editor's own command line, appended to the terminal's."""

    argv = [editor]
    if line is not None:
        argv.append(f"+{line}")
    argv.append(str(path))
    return argv
