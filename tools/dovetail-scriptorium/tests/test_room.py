"""Building the room: what happens when a tile, or its placement, fails.

The compositor and the spawned terminals are fakes, so these assert the
verb's own composition — which failures are loud and which are a line on
stderr — without a Wayland session. The end-to-end path with a real
editor is `nix/checks/scriptorium-room.nix`.
"""

from __future__ import annotations

import pytest

from dovetail_scriptorium import cli
from dovetail_seams import launch as seams_launch
from dovetail_seams.errors import DovetailError

from test_layout import EDITOR, REPL, container, side_by_side, tree, window, workspace


class FakeChild:
    def __init__(self, pid=4321, status=None):
        self.pid = pid
        self._status = status

    def poll(self):
        return self._status


class FakeCompositor:
    """A compositor that hands out window ids in the order asked for."""

    def __init__(self, con_ids, trees=None):
        self._con_ids = list(con_ids)
        self._trees = list(trees or [side_by_side()])
        self.commands = []

    def wait_for_window(self, pids, timeout, **kwargs):
        return self._con_ids.pop(0)

    def get_tree(self, timeout=None):
        return self._trees[0] if len(self._trees) == 1 else self._trees.pop(0)

    def split_beside(self, con_id):
        self.commands.append(("split_beside", con_id))
        return True

    def swap_windows(self, first, second):
        self.commands.append(("swap", first, second))
        return True


@pytest.fixture
def room(monkeypatch, tmp_path):
    """Run the verb against fakes, returning the compositor it drove."""

    def build(compositor, *, spawn=None, socket="/run/dovetail/nvim-7.sock"):
        monkeypatch.setattr(
            seams_launch,
            "spawn",
            spawn or (lambda argv: FakeChild()),
        )
        monkeypatch.setattr(cli.compositor_module, "detect", lambda environ: compositor)
        monkeypatch.setattr(seams_launch, "await_socket", lambda pid, environ: socket)
        return cli.run(
            ["--scratch-dir", str(tmp_path), "notes"],
            {"DOVETAIL_TERMINAL": "foot -e", "DOVETAIL_EDITOR": "nvim"},
        )

    return build


class TestTheHappyRoom:
    def test_it_prints_a_socket_line_and_a_file_line_and_nothing_else(
        self, room, capsys, tmp_path
    ):
        assert room(FakeCompositor([EDITOR, REPL])) == 0
        out = capsys.readouterr()
        lines = out.out.splitlines()
        assert lines[0] == "socket /run/dovetail/nvim-7.sock"
        assert lines[1].startswith("file ") and lines[1].endswith("-notes.md")
        assert str(tmp_path) in lines[1]
        assert len(lines) == 2
        assert out.err == ""

    def test_the_editor_is_split_before_the_repl_is_started(self, room):
        compositor = FakeCompositor([EDITOR, REPL])
        room(compositor)
        # Placement is asked of the compositor, not imposed afterwards:
        # nothing is moved once the room is up.
        assert compositor.commands == [("split_beside", EDITOR)]


class TestArrangementIsNeverWorthFailingOver:
    def test_a_misplaced_tile_warns_and_still_exits_zero(self, room, capsys):
        elsewhere = tree(
            workspace("1", [container(50, "splitv", [window(EDITOR), window(REPL)])])
        )
        assert room(FakeCompositor([EDITOR, REPL], trees=[elsewhere])) == 0
        captured = capsys.readouterr()
        assert "not side by side" in captured.err
        assert "splitv" in captured.err
        # The room is still reported: it is open, which is what was asked.
        assert captured.out.splitlines()[0].startswith("socket ")

    def test_the_wrong_way_round_is_swapped_rather_than_reported(self, room, capsys):
        backwards = tree(
            workspace("1", [container(50, "splith", [window(REPL), window(EDITOR)])])
        )
        compositor = FakeCompositor(
            [EDITOR, REPL], trees=[backwards, side_by_side()]
        )
        assert room(compositor) == 0
        assert ("swap", EDITOR, REPL) in compositor.commands
        assert capsys.readouterr().err == ""


class TestHalfARoomIsNotARoom:
    def test_a_window_that_never_appears_fails_loudly(self, room):
        with pytest.raises(DovetailError) as caught:
            room(FakeCompositor([EDITOR, None]))
        assert "no window appeared for the REPL" in str(caught.value)

    def test_a_terminal_that_died_is_named_with_its_status(self, room):
        with pytest.raises(DovetailError) as caught:
            room(
                FakeCompositor([None]),
                spawn=lambda argv: FakeChild(status=3),
            )
        assert "status 3" in str(caught.value)

    def test_no_socket_is_a_failure_that_still_names_the_scratch_file(self, room):
        with pytest.raises(DovetailError) as caught:
            room(FakeCompositor([EDITOR, REPL]), socket=None)
        message = str(caught.value)
        assert "no socket" in message
        assert "-notes.md" in message


class TestWithoutACompositor:
    def test_the_room_is_built_unarranged_and_says_so(self, room, capsys):
        # A terminal that exits 0 at once — one that daemonizes and hands
        # off to a running server — is the documented harmless case, and
        # keeps this test from really waiting out the liveness budget.
        assert room(None, spawn=lambda argv: FakeChild(status=0)) == 0
        captured = capsys.readouterr()
        assert "not arranged" in captured.err
        assert captured.out.splitlines()[0].startswith("socket ")


class TestNothingIsStartedBeforeEverythingIsChecked:
    def test_a_bad_topic_spawns_nothing(self, monkeypatch, tmp_path):
        def refuse(argv):
            raise AssertionError("a process was started for a topic that is not a slug")

        monkeypatch.setattr(seams_launch, "spawn", refuse)
        with pytest.raises(DovetailError):
            cli.run(
                ["--scratch-dir", str(tmp_path), "Not A Slug"],
                {"DOVETAIL_TERMINAL": "foot -e"},
            )
        assert list(tmp_path.iterdir()) == []

    def test_an_unset_terminal_spawns_nothing_and_creates_no_file(
        self, monkeypatch, tmp_path
    ):
        def refuse(argv):
            raise AssertionError("a process was started with no terminal configured")

        monkeypatch.setattr(seams_launch, "spawn", refuse)
        with pytest.raises(DovetailError) as caught:
            cli.run(["--scratch-dir", str(tmp_path), "notes"], {})
        assert "DOVETAIL_TERMINAL" in str(caught.value)
        assert list(tmp_path.iterdir()) == []
