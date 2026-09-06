"""Starting a program in a terminal, and confirming that it started.

Everything here is shared between Dovetail's verbs and none of it
decides anything: it resolves the slots (which terminal, which editor,
which REPL), spawns a process, and answers the one question that is
genuinely hard — did that terminal actually put a window on screen, or
did it die? What a verb *does* with the answer is the verb's own
business, and stays in the verb.

The terminal is private configuration and Dovetail never guesses one:
it is an argv prefix the resident supplies, and the program invocation
is appended to it as trailing arguments, so `foot -e` and
`wezterm start --` both work without Dovetail knowing either exists.
"""

from __future__ import annotations

import os
import shlex
import subprocess
import time
from pathlib import Path

from . import compositor as compositor_module
from . import editor as editor_module
from . import processes
from .defaults import DEFAULT_EDITOR, DEFAULT_REPL
from .errors import DovetailError
from .processes import descendant_depths

# How long to wait for a launched instance to publish its socket, when a
# caller asked for it. The socket appears asynchronously, some way into
# Neovim's startup, and a cold start off a spinning disk is the case this
# has to cover; ten seconds is well past a warm start's fraction of a
# second.
SOCKET_TIMEOUT = 10.0

_SOCKET_POLL_INTERVAL = 0.1

# How long to watch a spawned terminal for a quick death when there is no
# compositor to ask about a window at all. There is no window tree to
# poll on this path, only the child's own exit status, so this is a much
# shorter budget than the window wait: it exists to catch a terminal that
# fails immediately — a broken $DOVETAIL_TERMINAL, bad arguments — not to
# prove that a window will eventually appear. A terminal still alive when
# the budget expires is presumed fine, the same way a terminal that
# daemonizes and hands off to an already-running server is presumed fine
# on the compositor path.
NO_COMPOSITOR_LIVENESS_BUDGET = 2.0

_LIVENESS_POLL_INTERVAL = 0.05

_TERMINAL_CONFIG_UNDER_XDG_CONFIG_HOME = ("dovetail", "terminal")
_TERMINAL_CONFIG_UNDER_HOME = (".config", "dovetail", "terminal")

# Shown when neither $XDG_CONFIG_HOME nor $HOME can be resolved, which in
# practice means the environment is missing something POSIX guarantees;
# the doc-form path is still useful to a reader diagnosing that.
_TERMINAL_CONFIG_DOC_PATH = "$XDG_CONFIG_HOME/dovetail/terminal (or ~/.config/dovetail/terminal)"


def _no_terminal_message(config_path: Path | None) -> str:
    path_text = str(config_path) if config_path is not None else _TERMINAL_CONFIG_DOC_PATH
    return f"""no terminal is configured, and Dovetail will not guess one

Set $DOVETAIL_TERMINAL (or $TERMINAL) to the command that runs a program
in a new terminal window, as an argv prefix, or write it once to
{path_text}. For example:

    export DOVETAIL_TERMINAL="foot -e"
    export DOVETAIL_TERMINAL="wezterm start --"

or pass it for one invocation with --terminal."""


def split_argv(source: str, name: str) -> list[str]:
    """Parse a setting the way a shell would, naming it if it is malformed.

    Naming the setting matters: several places can supply one of these,
    and a traceback would say which line of Python failed rather than
    which of them has the unmatched quote.
    """

    try:
        return shlex.split(source)
    except ValueError as exc:
        raise DovetailError(
            f"{name} is not valid shell quoting ({exc}): {source}"
        ) from exc


def _terminal_config_path(environ: os._Environ | dict) -> Path | None:
    """Where the declarative terminal file lives, or None if unlocatable.

    `$XDG_CONFIG_HOME/dovetail/terminal`, falling back to
    `~/.config/dovetail/terminal` when `$XDG_CONFIG_HOME` is unset. None
    only when neither it nor `$HOME` is set, in which case there is no
    path to look at and the caller treats that the same as a file that
    turned out not to exist.
    """

    config_home = environ.get("XDG_CONFIG_HOME")
    if config_home and config_home.strip():
        return Path(config_home.strip(), *_TERMINAL_CONFIG_UNDER_XDG_CONFIG_HOME)
    home = environ.get("HOME")
    if home and home.strip():
        return Path(home.strip(), *_TERMINAL_CONFIG_UNDER_HOME)
    return None


def _terminal_config_argv(path: Path) -> list[str] | None:
    """The argv prefix written in the terminal config file, or None.

    None for a missing or blank file, mirroring how an unset or blank
    environment variable is treated. A file that exists but cannot be
    read is a refusal rather than a fall-through: a present-but-broken
    configuration is a fact the resident wants to hear, not skip past.
    """

    try:
        content = path.read_text()
    except FileNotFoundError:
        return None
    except OSError as exc:
        raise DovetailError(f"could not read {path}: {exc}") from exc
    if not content.strip():
        return None
    return split_argv(content, str(path))


def terminal_argv(
    explicit: str | None, environ: os._Environ | dict = os.environ
) -> list[str]:
    """The argv prefix that runs a command in a new terminal window.

    `--terminal`, then `$DOVETAIL_TERMINAL`, then the declarative
    terminal file (`$XDG_CONFIG_HOME/dovetail/terminal`, or
    `~/.config/dovetail/terminal`), then `$TERMINAL`. Never a hardcoded
    fallback: a wrong terminal is worse than a clear refusal, and there
    is no terminal every reader of this file has installed.

    The file sits below `$DOVETAIL_TERMINAL` but above `$TERMINAL`: it
    is a deliberately written, Dovetail-specific setting, so it beats an
    ambient, generic `$TERMINAL` a desktop environment may have set to
    something that is not an argv prefix; but `$DOVETAIL_TERMINAL` is a
    session-scoped choice made over the resident's own standing
    configuration, so it wins when both are set.
    """

    names = ("--terminal", "$DOVETAIL_TERMINAL")
    values = (explicit, environ.get("DOVETAIL_TERMINAL"))
    for name, source in zip(names, values):
        if source and source.strip():
            argv = split_argv(source, name)
            if argv:
                return argv

    config_path = _terminal_config_path(environ)
    if config_path is not None:
        argv = _terminal_config_argv(config_path)
        if argv:
            return argv

    source = environ.get("TERMINAL")
    if source and source.strip():
        argv = split_argv(source, "$TERMINAL")
        if argv:
            return argv

    raise DovetailError(_no_terminal_message(config_path))


def editor_command(environ: os._Environ | dict = os.environ) -> str:
    """The editor to launch: the build-time default, or the override."""

    override = environ.get("DOVETAIL_EDITOR")
    if override and override.strip():
        return override.strip()
    return DEFAULT_EDITOR


def repl_argv(
    explicit: str | None, environ: os._Environ | dict = os.environ
) -> list[str]:
    """The REPL to run beside the editor, as an argv.

    `--repl`, then `$DOVETAIL_REPL`, then the build-time default. Unlike
    the terminal, this slot has a default: Dovetail builds a Python and
    can hand the resident one hermetically, so refusing would be
    withholding something it is already holding.

    An argv rather than a bare command, because a REPL worth overriding
    to is often a command with arguments — `ipython --no-banner`,
    `python3 -q`, `ghci`.
    """

    names = ("--repl", "$DOVETAIL_REPL")
    values = (explicit, environ.get("DOVETAIL_REPL"))
    for name, source in zip(names, values):
        if source and source.strip():
            argv = split_argv(source, name)
            if argv:
                return argv
    return [DEFAULT_REPL]


def spawn(argv: list[str]) -> subprocess.Popen:
    """Start `argv` detached from the caller, with no pipes to the caller.

    The terminal gets a window, not the caller's pipes. Inheriting them
    makes a verb unusable from anything that reads its output: the reader
    blocks until the window is closed, because the terminal is still
    holding the write end, and a reader that gives up first can kill the
    editor. A new session on top of that keeps the terminal from taking a
    signal meant for whoever invoked us.
    """

    try:
        return subprocess.Popen(
            argv,
            start_new_session=True,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except OSError as exc:
        raise DovetailError(f"could not run the terminal command {argv[0]!r}: {exc}")


def spawned_pids(pid: int) -> set[int]:
    """The spawned process and everything descended from it, right now.

    A terminal may fork or re-exec before it maps a window, so the
    window's process is not necessarily the one we started.
    """

    return {pid} | set(descendant_depths(processes.read_process_table(), pid))


def wait_for_window(
    compositor: object,
    child: subprocess.Popen,
    timeout: float = compositor_module.NEW_WINDOW_TIMEOUT,
) -> int | None:
    """The container id of the window `child` produced, or None.

    The wait ends early once `child` has exited: a terminal that hands
    off to an already-running server exits 0 right away, and without
    the cutoff the wait would burn its whole budget on a launch that
    already succeeded, because the window it should have found belongs
    to a process outside this pid tree.
    """

    return compositor.wait_for_window(
        lambda: spawned_pids(child.pid),
        timeout,
        alive=lambda: child.poll() is None,
    )


def raise_if_terminal_died(
    child: subprocess.Popen, argv: list[str], consequence: str
) -> None:
    """Fail if the terminal exited instead of mapping a window.

    A terminal that exits rather than mapping a window is the case worth
    distinguishing from a slow one: nothing opened at all, and reporting
    that only as a placement problem would describe an empty screen as
    cosmetic. A clean exit is not treated as a failure — see
    `watch_liveness` for why.
    """

    status = child.poll()
    if status is not None and status != 0:
        raise DovetailError(
            f"the terminal command {argv[0]!r} exited with status {status} "
            f"without opening a window; {consequence}"
        )


def watch_liveness(
    child: subprocess.Popen,
    argv: list[str],
    consequence: str,
    budget: float = NO_COMPOSITOR_LIVENESS_BUDGET,
    *,
    interval: float = _LIVENESS_POLL_INTERVAL,
    monotonic=time.monotonic,
    sleep=time.sleep,
) -> None:
    """Fail loudly if `child` dies within `budget`; otherwise say nothing.

    For the case where there is no compositor to ask about a window, so
    the child process is the only signal available. A clean exit (status
    0) is not treated as a failure, for the same reason
    `raise_if_terminal_died` does not treat one as a failure: a terminal
    that hands off to an already-running server and exits 0 immediately
    is a documented, harmless case, indistinguishable from this vantage
    point from a terminal that quietly failed without setting an exit
    status.
    """

    deadline = monotonic() + budget
    while True:
        status = child.poll()
        if status is not None:
            if status != 0:
                raise DovetailError(
                    f"the terminal command {argv[0]!r} exited with status "
                    f"{status} within {budget:g}s of being started; "
                    f"{consequence}"
                )
            return
        remaining = deadline - monotonic()
        if remaining <= 0:
            return
        sleep(min(interval, remaining))


def await_socket(
    terminal_pid: int,
    environ: os._Environ | dict = os.environ,
    timeout: float = SOCKET_TIMEOUT,
) -> str | None:
    """Poll for a reachable instance running under the spawned terminal.

    Matching on descent rather than on "a socket that was not there
    before" keeps the answer right when another instance happens to
    start at the same moment.
    """

    deadline = time.monotonic() + timeout
    while True:
        depths = descendant_depths(processes.read_process_table(), terminal_pid)
        for instance in editor_module.list_instances(environ):
            if instance.pid in depths and editor_module.is_reachable(instance.socket):
                return instance.socket
        if time.monotonic() >= deadline:
            return None
        time.sleep(_SOCKET_POLL_INTERVAL)


def editor_argv(
    path: Path, line: int | None, environ: os._Environ | dict = os.environ
) -> list[str]:
    """The editor's own command line, to append to a terminal's.

    The filename goes on the editor's command line rather than being
    sent over RPC after the fact. The socket appears asynchronously some
    way into startup — a listing taken immediately after spawning finds
    no directory at all — so a spawn-then-connect implementation would
    race for no benefit.
    """

    return editor_module.launch_argv(editor_command(environ), path, line)
