"""Finding the window a spawned terminal maps."""

from __future__ import annotations

from dovetail_show.compositor import Sway, detect, window_for_pids


class TestDetect:
    def test_no_swaysock_is_no_compositor(self):
        assert detect({}) is None


def _tree(*windows):
    """A tree shaped like Sway's: root, output, workspace, then windows."""

    return {
        "id": 1,
        "nodes": [
            {
                "id": 2,
                "nodes": [{"id": 3, "nodes": list(windows), "floating_nodes": []}],
                "floating_nodes": [],
            }
        ],
        "floating_nodes": [],
    }


class TestWindowForPids:
    def test_a_window_nested_under_workspaces_is_found(self):
        tree = _tree({"id": 42, "pid": 1000, "app_id": "foot"})
        assert window_for_pids(tree, {1000}) == 42

    def test_a_window_that_is_already_floating_is_found(self):
        tree = {
            "id": 1,
            "nodes": [],
            "floating_nodes": [{"id": 77, "pid": 1000, "app_id": "foot"}],
        }
        assert window_for_pids(tree, {1000}) == 77

    def test_any_of_the_pids_matches(self):
        # The window can belong to a descendant of the process we
        # started, because a terminal may fork or re-exec before mapping.
        tree = _tree({"id": 9, "pid": 1234, "app_id": "foot"})
        assert window_for_pids(tree, {1000, 1234}) == 9

    def test_no_matching_window_is_none(self):
        tree = _tree({"id": 9, "pid": 5555, "app_id": "firefox"})
        assert window_for_pids(tree, {1000}) is None

    def test_an_empty_tree_is_none(self):
        assert window_for_pids(_tree(), {1000}) is None

    def test_no_tree_at_all_is_none(self):
        # get_tree returns None when the compositor cannot be reached.
        assert window_for_pids(None, {1000}) is None


class TestWaitForWindow:
    """The wait is a poll, because a subscription cannot be confirmed.

    `swaymsg -t subscribe` consumes Sway's reply and prints only events,
    in both raw and pretty modes, so nothing tells a caller that it is
    listening — and a window mapped before it is has no second chance.
    Asking again has no such gap.
    """

    def _sway(self, trees):
        sway = Sway("swaymsg")
        remaining = list(trees)
        sway.get_tree = lambda: remaining.pop(0) if remaining else None
        return sway

    def test_a_window_already_there_is_returned_without_sleeping(self):
        sway = self._sway([_tree({"id": 42, "pid": 1000})])
        slept = []
        assert (
            sway.wait_for_window(
                lambda: {1000}, 5.0, sleep=slept.append, monotonic=lambda: 0.0
            )
            == 42
        )
        assert slept == []

    def test_a_window_that_appears_later_is_waited_for(self):
        sway = self._sway([_tree(), _tree(), _tree({"id": 42, "pid": 1000})])
        clock = iter([0.0, 0.1, 0.2, 0.3, 0.4])
        assert (
            sway.wait_for_window(
                lambda: {1000},
                5.0,
                sleep=lambda _: None,
                monotonic=lambda: next(clock),
            )
            == 42
        )

    def test_the_pids_are_re_read_on_every_attempt(self):
        # The terminal's child does not exist when the wait begins, so a
        # set captured once would never match it.
        sway = self._sway([_tree({"id": 42, "pid": 2000})] * 3)
        seen = iter([{1000}, {1000, 2000}])
        clock = iter([0.0, 0.1, 0.2, 0.3])
        assert (
            sway.wait_for_window(
                lambda: next(seen),
                5.0,
                sleep=lambda _: None,
                monotonic=lambda: next(clock),
            )
            == 42
        )

    def test_a_window_that_never_appears_times_out(self):
        sway = self._sway([_tree()] * 10)
        clock = iter([0.0, 6.0])
        assert (
            sway.wait_for_window(
                lambda: {1000},
                5.0,
                sleep=lambda _: None,
                monotonic=lambda: next(clock),
            )
            is None
        )
