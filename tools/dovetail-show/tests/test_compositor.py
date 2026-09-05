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

    def _sway(self, trees, clock=None):
        sway = Sway("swaymsg")
        remaining = list(trees)
        self.queries = []

        def get_tree(timeout=None):
            self.queries.append(timeout)
            if clock is not None:
                clock.advance(clock.per_query)
            return remaining.pop(0) if remaining else None

        sway.get_tree = get_tree
        return sway

    def test_a_window_already_there_is_returned_without_sleeping(self):
        sway = self._sway([_tree({"id": 42, "pid": 1000})])
        slept = []
        assert (
            sway.wait_for_window(
                lambda: {1000}, 5.0, sleep=slept.append, monotonic=_Clock().read
            )
            == 42
        )
        assert slept == []

    def test_a_window_that_appears_later_is_waited_for(self):
        sway = self._sway([_tree(), _tree(), _tree({"id": 42, "pid": 1000})])
        assert (
            sway.wait_for_window(
                lambda: {1000}, 5.0, sleep=lambda _: None, monotonic=_Clock().read
            )
            == 42
        )

    def test_the_pids_are_re_read_on_every_attempt(self):
        # The terminal's child does not exist when the wait begins, so a
        # set captured once would never match it.
        sway = self._sway([_tree({"id": 42, "pid": 2000})] * 3)
        seen = iter([{1000}, {1000, 2000}])
        assert (
            sway.wait_for_window(
                lambda: next(seen), 5.0, sleep=lambda _: None, monotonic=_Clock().read
            )
            == 42
        )

    def test_a_window_that_never_appears_times_out(self):
        sway = self._sway([_tree()] * 500)
        assert (
            sway.wait_for_window(
                lambda: {1000}, 5.0, sleep=lambda _: None, monotonic=_Clock().read
            )
            is None
        )

    def test_a_query_may_not_outlive_the_deadline(self):
        # A query that hangs near the deadline would otherwise get a
        # fresh five-second allowance of its own, and the whole wait
        # would take twice what the caller was promised.
        clock = _Clock(step=0.0)
        clock.per_query = 2.0
        sway = self._sway([_tree()] * 500, clock=clock)
        assert (
            sway.wait_for_window(
                lambda: {1000}, 5.0, sleep=lambda _: None, monotonic=clock.read
            )
            is None
        )
        assert max(self.queries) <= 5.0
        # Third query starts at t=4s with one second of budget left.
        assert self.queries[2] == 1.0
        assert clock.now <= 6.0


class _Clock:
    """A clock that advances on every reading, so no test really waits."""

    def __init__(self, step=0.1):
        self.now = 0.0
        self.step = step
        self.per_query = 0.0

    def read(self):
        self.now += self.step
        return self.now

    def advance(self, seconds):
        self.now += seconds
