"""What "side by side" means, read off a window tree.

Pure: it takes a Sway tree as already-parsed JSON and two container ids
and says whether the room came out right, so the rule is testable on a
machine with no compositor at all.

The rule is written down rather than judged, per the vision's placement
position. Two tiles on the focused workspace, the editor on the left and
the REPL on the right, sharing a horizontal split. No workspace numbers,
no floating, no sizes: the resident moves and resizes as she likes, and
the rule only puts two tiles somewhere predictable.

Placement is asked of the compositor rather than imposed afterwards —
the editor's window is focused and split horizontally, so the REPL's
window maps into the space beside it. This module is the check that it
did, and the decision about the one correction worth attempting.
"""

from __future__ import annotations

from dataclasses import dataclass

# The one Sway layout that means "these containers sit beside each
# other, left to right". Named here rather than inline so the check
# reads as the rule it implements.
SIDE_BY_SIDE = "splith"


@dataclass(frozen=True)
class Placement:
    """Where one window ended up, in the terms the rule is written in."""

    workspace: str | None
    parent_id: int | None
    parent_layout: str | None
    index: int | None
    floating: bool


@dataclass(frozen=True)
class Verdict:
    """Whether the room came out right, and what to do if it did not.

    `complaint` is stderr-shaped: it is what the resident is told when
    the arrangement did not work, and it names what actually happened
    rather than saying "arrangement failed".

    `swap` marks the single case worth correcting automatically — the
    two tiles are siblings in a horizontal split, but the wrong way
    round. Every other way of going wrong needs a container moved, and a
    move whose result depends on where the window happened to land is
    exactly what this design avoids; those are reported and left alone.
    """

    ok: bool
    complaint: str | None = None
    swap: bool = False


def locate(tree: object, con_id: int) -> Placement | None:
    """Where `con_id` sits in `tree`, or None if it is not in it.

    Walks from the root carrying the enclosing workspace's name and the
    immediate parent's identity, so a single pass answers every question
    the rule asks.
    """

    return _walk(tree, con_id, workspace=None, parent=None, index=None, floating=False)


def _walk(
    node: object,
    con_id: int,
    *,
    workspace: str | None,
    parent: dict | None,
    index: int | None,
    floating: bool,
) -> Placement | None:
    if not isinstance(node, dict):
        return None

    if node.get("type") == "workspace":
        name = node.get("name")
        workspace = name if isinstance(name, str) else workspace

    if node.get("id") == con_id:
        layout = None if parent is None else parent.get("layout")
        return Placement(
            workspace=workspace,
            parent_id=None if parent is None else parent.get("id"),
            parent_layout=layout if isinstance(layout, str) else None,
            index=index,
            floating=floating,
        )

    for key, is_floating in (("nodes", floating), ("floating_nodes", True)):
        children = node.get(key)
        if not isinstance(children, list):
            continue
        for position, child in enumerate(children):
            found = _walk(
                child,
                con_id,
                workspace=workspace,
                parent=node,
                index=position,
                floating=is_floating,
            )
            if found is not None:
                return found
    return None


def assess(tree: object, editor: int, repl: int) -> Verdict:
    """Did the two windows come out side by side, editor on the left?

    Checked in the order a reader would check it: could the tree be read
    at all, are both windows still there, are they tiled, are they on one
    workspace, are they siblings in a horizontal split, and only then is
    the editor the left-hand one.
    """

    if tree is None:
        return Verdict(
            ok=False,
            complaint="the compositor could not be asked for its window tree",
        )

    editor_place = locate(tree, editor)
    repl_place = locate(tree, repl)

    if editor_place is None or repl_place is None:
        missing = "editor" if editor_place is None else "REPL"
        return Verdict(
            ok=False,
            complaint=f"the compositor no longer reports a window for the {missing}",
        )

    for name, place in (("editor", editor_place), ("REPL", repl_place)):
        if place.floating:
            return Verdict(
                ok=False, complaint=f"the {name} window is floating rather than tiled"
            )

    if editor_place.workspace != repl_place.workspace:
        return Verdict(
            ok=False,
            complaint=(
                "the two tiles ended up on different workspaces "
                f"({editor_place.workspace} and {repl_place.workspace})"
            ),
        )

    if editor_place.parent_id != repl_place.parent_id:
        return Verdict(
            ok=False,
            complaint="the two tiles are not side by side in one container",
        )

    if editor_place.parent_layout != SIDE_BY_SIDE:
        return Verdict(
            ok=False,
            complaint=(
                "the two tiles share a container laid out "
                f"{editor_place.parent_layout!r} rather than {SIDE_BY_SIDE!r}"
            ),
        )

    if editor_place.index is None or repl_place.index is None:
        return Verdict(ok=False, complaint="the compositor reported no tile order")

    if editor_place.index > repl_place.index:
        # Siblings in the right container, the wrong way round. One
        # unambiguous command fixes it.
        return Verdict(
            ok=False,
            complaint="the REPL came out to the left of the editor",
            swap=True,
        )

    return Verdict(ok=True)
