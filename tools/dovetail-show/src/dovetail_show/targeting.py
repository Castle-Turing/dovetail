"""The targeting rule: which editor instance should be shown a file.

This module is deliberately pure. It takes a Sway tree as already-parsed
JSON, a snapshot of the process table, a listing of live editor sockets,
and a predicate that says whether a socket answers — and it returns a
target. It runs no subprocesses, reads no files and consults no
environment, so the whole rule is testable on a machine with no
compositor and no editor.

It also knows nothing about what protocol an editor speaks or how its
sockets are named: instances arrive as (socket, pid) pairs from the
editor seam.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Iterable, Mapping, Sequence

from dovetail_seams.editor import Instance
from dovetail_seams.errors import DovetailError
from dovetail_seams.processes import descendant_depths

__all__ = [
    "ExplicitSocketUnreachable",
    "Instance",
    "LaunchNew",
    "OpenIn",
    "Target",
    "choose_target",
    "focused_pid",
    "rank_candidates",
]


@dataclass(frozen=True)
class OpenIn:
    """Show the file in this already-running instance."""

    socket: str


@dataclass(frozen=True)
class LaunchNew:
    """No instance was found inside the focused window; start one."""


Target = OpenIn | LaunchNew


class ExplicitSocketUnreachable(DovetailError):
    """The caller named a socket, and it did not answer.

    A caller that names a dead socket wants to hear about it, not to have
    a different editor silently substituted.
    """

    def __init__(self, socket: str) -> None:
        super().__init__(
            f"the socket named by --socket/$DOVETAIL_SOCKET does not answer: {socket}"
        )
        self.socket = socket


def focused_pid(sway_tree: object) -> int | None:
    """The process id of the focused window, or None.

    None covers every uninteresting case identically: no tree at all
    (the compositor could not be reached), a focused node that is a
    workspace rather than a window, or a window whose pid the compositor
    did not report.
    """

    node = _focused_node(sway_tree)
    if node is None:
        return None
    pid = node.get("pid")
    return pid if isinstance(pid, int) else None


def _focused_node(node: object) -> dict | None:
    if not isinstance(node, dict):
        return None
    if node.get("focused") is True:
        return node
    for key in ("nodes", "floating_nodes"):
        children = node.get(key)
        if isinstance(children, Iterable) and not isinstance(children, (str, bytes)):
            for child in children:
                found = _focused_node(child)
                if found is not None:
                    return found
    return None


def rank_candidates(
    sway_tree: object,
    process_table: Mapping[int, int],
    instances: Sequence[Instance],
) -> list[Instance]:
    """The instances running inside the focused window, best first.

    Deepest first, so a Neovim running inside another Neovim's
    `:terminal` wins over its host. Ties are broken by highest process
    id, so the order is total and documented rather than an accident of
    directory listing order.
    """

    root = focused_pid(sway_tree)
    if root is None:
        return []

    depths = descendant_depths(process_table, root)
    inside = [instance for instance in instances if instance.pid in depths]
    inside.sort(key=lambda instance: (-depths[instance.pid], -instance.pid))
    return inside


def choose_target(
    *,
    explicit_socket: str | None,
    sway_tree: object,
    process_table: Mapping[int, int],
    instances: Sequence[Instance],
    verify: Callable[[str], bool],
) -> Target:
    """Apply the three-step rule; the first step that yields wins.

    One: the caller said so. Two: the innermost live editor inside the
    focused window. Three: launch a new one.

    `verify` is the connect-and-verify that `docs/module.md` requires of
    every consumer — a socket file outlives its process, and the pid in
    its name may by then belong to something else entirely.
    """

    if explicit_socket:
        if not verify(explicit_socket):
            raise ExplicitSocketUnreachable(explicit_socket)
        return OpenIn(explicit_socket)

    for candidate in rank_candidates(sway_tree, process_table, instances):
        if verify(candidate.socket):
            return OpenIn(candidate.socket)

    return LaunchNew()
