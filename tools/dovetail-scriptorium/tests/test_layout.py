"""The layout rule, tested with no compositor.

Every case is a Sway tree as parsed JSON and a verdict about it: the
room came out right, or it did not and the resident is told what
actually happened.
"""

from __future__ import annotations

from dovetail_scriptorium.layout import assess, locate

EDITOR = 101
REPL = 102


def window(con_id, *, name="window"):
    return {
        "id": con_id,
        "type": "con",
        "name": name,
        "layout": "none",
        "nodes": [],
        "floating_nodes": [],
    }


def container(con_id, layout, children):
    return {
        "id": con_id,
        "type": "con",
        "layout": layout,
        "nodes": list(children),
        "floating_nodes": [],
    }


def workspace(name, children, floating=()):
    return {
        "id": 3,
        "type": "workspace",
        "name": name,
        "layout": "splith",
        "nodes": list(children),
        "floating_nodes": list(floating),
    }


def tree(*workspaces):
    """A tree shaped like a real one: root, output, workspaces, windows."""

    return {
        "id": 1,
        "type": "root",
        "layout": "splith",
        "nodes": [
            {
                "id": 2,
                "type": "output",
                "name": "HEADLESS-1",
                "layout": "output",
                "nodes": list(workspaces),
                "floating_nodes": [],
            }
        ],
        "floating_nodes": [],
    }


def side_by_side():
    """What `split_beside` is expected to have produced."""

    return tree(
        workspace("1", [container(50, "splith", [window(EDITOR), window(REPL)])])
    )


class TestLocate:
    def test_it_reports_the_enclosing_workspace_and_parent(self):
        place = locate(side_by_side(), EDITOR)
        assert place.workspace == "1"
        assert place.parent_id == 50
        assert place.parent_layout == "splith"
        assert place.index == 0
        assert place.floating is False

    def test_a_window_that_is_not_there_is_not_located(self):
        assert locate(side_by_side(), 999) is None

    def test_a_floating_window_is_reported_as_floating(self):
        root = tree(workspace("1", [], floating=[window(EDITOR)]))
        assert locate(root, EDITOR).floating is True

    def test_no_tree_at_all_locates_nothing(self):
        assert locate(None, EDITOR) is None


class TestTheRoomCameOutRight:
    def test_two_tiles_in_one_horizontal_split_editor_first(self):
        assert assess(side_by_side(), EDITOR, REPL).ok

    def test_other_windows_on_the_workspace_do_not_matter(self):
        # `split_beside` wraps the editor in a split of its own; whatever
        # else the resident had open keeps the space it had.
        root = tree(
            workspace(
                "1",
                [
                    window(900),
                    container(50, "splith", [window(EDITOR), window(REPL)]),
                ],
            )
        )
        assert assess(root, EDITOR, REPL).ok


class TestTheRoomDidNot:
    def test_a_window_the_compositor_has_lost(self):
        root = tree(workspace("1", [container(50, "splith", [window(EDITOR)])]))
        verdict = assess(root, EDITOR, REPL)
        assert not verdict.ok
        assert "REPL" in verdict.complaint
        assert not verdict.swap

    def test_a_floating_tile_is_named_as_floating(self):
        root = tree(
            workspace("1", [container(50, "splith", [window(EDITOR)])],
                      floating=[window(REPL)])
        )
        verdict = assess(root, EDITOR, REPL)
        assert not verdict.ok
        assert "floating" in verdict.complaint

    def test_different_workspaces_are_named(self):
        root = tree(
            workspace("1", [window(EDITOR)]),
            {**workspace("2", [window(REPL)]), "id": 4},
        )
        verdict = assess(root, EDITOR, REPL)
        assert not verdict.ok
        assert "different workspaces" in verdict.complaint
        assert "1" in verdict.complaint and "2" in verdict.complaint

    def test_tiles_that_are_not_siblings(self):
        root = tree(
            workspace(
                "1",
                [
                    container(50, "splith", [window(EDITOR)]),
                    container(51, "splith", [window(REPL)]),
                ],
            )
        )
        verdict = assess(root, EDITOR, REPL)
        assert not verdict.ok
        assert "one container" in verdict.complaint

    def test_a_vertical_or_tabbed_split_is_not_side_by_side(self):
        for layout in ("splitv", "tabbed", "stacked"):
            root = tree(
                workspace("1", [container(50, layout, [window(EDITOR), window(REPL)])])
            )
            verdict = assess(root, EDITOR, REPL)
            assert not verdict.ok
            assert layout in verdict.complaint
            # None of these is fixed by swapping: the tiles are in the
            # right container, laid out the wrong way.
            assert not verdict.swap


class TestTheOneCorrectionWorthMaking:
    def test_the_repl_on_the_left_asks_for_a_swap(self):
        root = tree(
            workspace("1", [container(50, "splith", [window(REPL), window(EDITOR)])])
        )
        verdict = assess(root, EDITOR, REPL)
        assert not verdict.ok
        assert verdict.swap
        assert "left of the editor" in verdict.complaint

    def test_and_the_swapped_tree_passes(self):
        # The swap is only worth attempting because its result is exactly
        # the tree the rule wants; this is that tree.
        assert assess(side_by_side(), EDITOR, REPL).ok
