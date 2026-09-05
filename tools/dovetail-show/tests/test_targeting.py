"""The targeting rule, tested with no compositor and no editor.

Every case here is the rule in `docs/show.md` written as an assertion:
a Sway tree as parsed JSON, a process table snapshot, a socket listing,
and a predicate standing in for connect-and-verify.
"""

from __future__ import annotations

import pytest

from dovetail_show.targeting import (
    ExplicitSocketUnreachable,
    Instance,
    LaunchNew,
    OpenIn,
    choose_target,
    descendant_depths,
    focused_pid,
    rank_candidates,
)


def window(pid, *, focused=False, name="window"):
    return {"type": "con", "name": name, "pid": pid, "focused": focused, "nodes": []}


def tree(*windows, focused_workspace=True):
    """A Sway tree shaped like a real one: root, output, workspace, windows."""

    return {
        "id": 1,
        "type": "root",
        "focused": False,
        "nodes": [
            {
                "id": 2,
                "type": "output",
                "name": "HEADLESS-1",
                "focused": False,
                "nodes": [
                    {
                        "id": 3,
                        "type": "workspace",
                        "name": "1",
                        "focused": not focused_workspace and False,
                        "nodes": list(windows),
                        "floating_nodes": [],
                    }
                ],
                "floating_nodes": [],
            }
        ],
        "floating_nodes": [],
    }


def alive(*sockets):
    live = set(sockets)
    return lambda socket: socket in live


NOTHING_ANSWERS = lambda socket: False  # noqa: E731


def decide(**kwargs):
    kwargs.setdefault("explicit_socket", None)
    kwargs.setdefault("sway_tree", None)
    kwargs.setdefault("process_table", {})
    kwargs.setdefault("instances", [])
    kwargs.setdefault("verify", NOTHING_ANSWERS)
    return choose_target(**kwargs)


class TestFocusedPid:
    def test_finds_the_focused_window(self):
        assert focused_pid(tree(window(100), window(200, focused=True))) == 200

    def test_looks_inside_floating_nodes(self):
        root = tree(window(100))
        root["nodes"][0]["nodes"][0]["floating_nodes"] = [window(300, focused=True)]
        assert focused_pid(root) == 300

    def test_no_tree_at_all_is_no_focus(self):
        assert focused_pid(None) is None

    def test_a_focused_node_with_no_pid_is_no_focus(self):
        empty_workspace = {"type": "workspace", "focused": True, "nodes": []}
        assert focused_pid(empty_workspace) is None


class TestDescendantDepths:
    def test_counts_distance_from_the_root(self):
        table = {10: 1, 20: 10, 30: 20, 40: 1}
        assert descendant_depths(table, 10) == {10: 0, 20: 1, 30: 2}

    def test_a_cycle_in_a_torn_snapshot_terminates(self):
        table = {10: 20, 20: 10}
        assert descendant_depths(table, 10) == {10: 0, 20: 1}


class TestTheRule:
    def test_the_editor_in_the_focused_terminal_wins(self):
        # foot (pid 100) is focused, with nvim (pid 140) inside it; a
        # second editor (pid 240) is running in an unfocused terminal.
        target = decide(
            sway_tree=tree(window(100, focused=True), window(200)),
            process_table={100: 1, 140: 100, 200: 1, 240: 200},
            instances=[
                Instance("/run/dovetail/nvim-140.sock", 140),
                Instance("/run/dovetail/nvim-240.sock", 240),
            ],
            verify=alive(
                "/run/dovetail/nvim-140.sock", "/run/dovetail/nvim-240.sock"
            ),
        )
        assert target == OpenIn("/run/dovetail/nvim-140.sock")

    def test_the_deeper_of_two_editors_wins(self):
        # nvim (150) running in the :terminal of nvim (140) beats its host.
        target = decide(
            sway_tree=tree(window(100, focused=True)),
            process_table={100: 1, 140: 100, 145: 140, 150: 145},
            instances=[
                Instance("/run/dovetail/nvim-140.sock", 140),
                Instance("/run/dovetail/nvim-150.sock", 150),
            ],
            verify=alive(
                "/run/dovetail/nvim-140.sock", "/run/dovetail/nvim-150.sock"
            ),
        )
        assert target == OpenIn("/run/dovetail/nvim-150.sock")

    def test_equal_depth_is_broken_by_highest_pid(self):
        target = decide(
            sway_tree=tree(window(100, focused=True)),
            process_table={100: 1, 140: 100, 141: 100},
            instances=[
                Instance("/run/dovetail/nvim-141.sock", 141),
                Instance("/run/dovetail/nvim-140.sock", 140),
            ],
            verify=alive(
                "/run/dovetail/nvim-140.sock", "/run/dovetail/nvim-141.sock"
            ),
        )
        assert target == OpenIn("/run/dovetail/nvim-141.sock")

    def test_a_stale_socket_naming_a_pid_outside_the_tree_is_ignored(self):
        # nvim-999.sock survived a SIGKILL; 999 is not running under the
        # focused window (or at all).
        target = decide(
            sway_tree=tree(window(100, focused=True)),
            process_table={100: 1, 140: 100},
            instances=[
                Instance("/run/dovetail/nvim-999.sock", 999),
                Instance("/run/dovetail/nvim-140.sock", 140),
            ],
            verify=alive("/run/dovetail/nvim-140.sock"),
        )
        assert target == OpenIn("/run/dovetail/nvim-140.sock")

    def test_a_stale_socket_whose_pid_was_reused_is_ranked_then_rejected(self):
        # 140 is now some other program that inherited the pid. The
        # socket ranks, fails connect-and-verify, and the next one wins.
        target = decide(
            sway_tree=tree(window(100, focused=True)),
            process_table={100: 1, 140: 100, 130: 100},
            instances=[
                Instance("/run/dovetail/nvim-140.sock", 140),
                Instance("/run/dovetail/nvim-130.sock", 130),
            ],
            verify=alive("/run/dovetail/nvim-130.sock"),
        )
        assert target == OpenIn("/run/dovetail/nvim-130.sock")

    def test_a_focused_window_with_no_editor_under_it_launches(self):
        target = decide(
            sway_tree=tree(window(100, focused=True), window(200)),
            process_table={100: 1, 200: 1, 240: 200},
            instances=[Instance("/run/dovetail/nvim-240.sock", 240)],
            verify=alive("/run/dovetail/nvim-240.sock"),
        )
        assert target == LaunchNew()

    def test_an_unreachable_compositor_launches(self):
        # $SWAYSOCK unset, or swaymsg missing: no tree, so no focus, so
        # nothing is discovered. Not an error.
        target = decide(
            sway_tree=None,
            process_table={100: 1, 140: 100},
            instances=[Instance("/run/dovetail/nvim-140.sock", 140)],
            verify=alive("/run/dovetail/nvim-140.sock"),
        )
        assert target == LaunchNew()

    def test_an_editor_under_a_multiplexer_is_not_found_and_launches(self):
        # The known limitation, asserted rather than hoped for: nvim
        # (500) is a child of the tmux *server* (400), which is not a
        # descendant of the focused terminal (100) that displays it.
        target = decide(
            sway_tree=tree(window(100, focused=True)),
            process_table={100: 1, 110: 100, 400: 1, 500: 400},
            instances=[Instance("/run/dovetail/nvim-500.sock", 500)],
            verify=alive("/run/dovetail/nvim-500.sock"),
        )
        assert target == LaunchNew()

    def test_no_instances_at_all_launches(self):
        target = decide(
            sway_tree=tree(window(100, focused=True)),
            process_table={100: 1},
        )
        assert target == LaunchNew()


class TestTheCallerSaidSo:
    def test_an_explicit_socket_beats_discovery(self):
        target = decide(
            explicit_socket="/run/dovetail/nvim-900.sock",
            sway_tree=tree(window(100, focused=True)),
            process_table={100: 1, 140: 100},
            instances=[Instance("/run/dovetail/nvim-140.sock", 140)],
            verify=alive(
                "/run/dovetail/nvim-900.sock", "/run/dovetail/nvim-140.sock"
            ),
        )
        assert target == OpenIn("/run/dovetail/nvim-900.sock")

    def test_a_dead_explicit_socket_fails_loudly_naming_it(self):
        # Never silently substituted: the caller holds a fact, and being
        # wrong about it is worth hearing.
        with pytest.raises(ExplicitSocketUnreachable) as caught:
            decide(
                explicit_socket="/run/dovetail/nvim-900.sock",
                sway_tree=tree(window(100, focused=True)),
                process_table={100: 1, 140: 100},
                instances=[Instance("/run/dovetail/nvim-140.sock", 140)],
                verify=alive("/run/dovetail/nvim-140.sock"),
            )
        assert "/run/dovetail/nvim-900.sock" in str(caught.value)


class TestRanking:
    def test_ranking_is_total_and_deepest_first(self):
        ranked = rank_candidates(
            tree(window(100, focused=True)),
            {100: 1, 140: 100, 141: 100, 150: 140},
            [
                Instance("a", 140),
                Instance("b", 141),
                Instance("c", 150),
            ],
        )
        assert [instance.socket for instance in ranked] == ["c", "b", "a"]
