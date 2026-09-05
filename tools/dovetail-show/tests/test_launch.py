"""The show verb's launch step: floating, and failing loudly.

The slots themselves and the spawn/wait machinery belong to
`dovetail_seams` and are tested there. What is asserted here is only
show's own composition of them.
"""

from __future__ import annotations

import subprocess

import pytest

from dovetail_seams import launch as seams_launch
from dovetail_seams.errors import DovetailError

from dovetail_show import launch as launch_module


class TestTheEditorGetsAWindowNotThePipes:
    """A launched terminal must not inherit the caller's stdio.

    Measured on a real desktop before this was fixed: a caller that read
    the tool's output blocked until the editor window was closed, because
    the terminal held the write end of the pipe; and when the reader gave
    up first, the editor died with it. The primary consumer is an agent
    session capturing output, so both failures are the normal case rather
    than the exotic one.
    """

    def _spawn(self, monkeypatch, tmp_path):
        recorded = {}

        class FakeChild:
            pid = 4321

            def poll(self):
                return None

        class ImmediateWindow:
            """A compositor that finds the window at once.

            What this test cares about is the child's stdio and session,
            not the wait for a window; a compositor that answers
            instantly keeps it that way without sleeping in real time.
            """

            def wait_for_window(self, pids, timeout, **kwargs):
                return 1

            def float_window(self, con_id):
                return True

        def fake_popen(argv, **kwargs):
            recorded["argv"] = argv
            recorded["kwargs"] = kwargs
            return FakeChild()

        monkeypatch.setattr(seams_launch.subprocess, "Popen", fake_popen)
        launch_module.launch(
            tmp_path / "note.md",
            None,
            terminal="foot -e",
            float_window=False,
            compositor=ImmediateWindow(),
            environ={"DOVETAIL_TERMINAL": "foot -e"},
        )
        return recorded

    def test_stdio_goes_to_devnull(self, monkeypatch, tmp_path):
        recorded = self._spawn(monkeypatch, tmp_path)
        for stream in ("stdin", "stdout", "stderr"):
            assert recorded["kwargs"][stream] == subprocess.DEVNULL

    def test_it_gets_its_own_session(self, monkeypatch, tmp_path):
        recorded = self._spawn(monkeypatch, tmp_path)
        assert recorded["kwargs"]["start_new_session"] is True


class TestATerminalThatNeverOpensAWindow:
    def test_a_terminal_that_exits_is_an_error_not_a_placement_note(
        self, monkeypatch, tmp_path
    ):
        # Nothing opened at all. Reporting only "could not float" would
        # describe a file the resident cannot see as a cosmetic problem.
        class DeadChild:
            pid = 4321

            def poll(self):
                return 2

        monkeypatch.setattr(
            seams_launch.subprocess, "Popen", lambda argv, **kw: DeadChild()
        )

        class NoWindows:
            def wait_for_window(self, pids, timeout, **kwargs):
                return None

        with pytest.raises(DovetailError) as caught:
            launch_module.launch(
                tmp_path / "note.md",
                None,
                terminal="foot -e",
                compositor=NoWindows(),
                environ={"DOVETAIL_TERMINAL": "foot -e"},
            )
        assert "status 2" in str(caught.value)


class TestNoFloatStillWaitsForWindow:
    """`--no-float` skips the `floating enable` call, never the wait.

    Before this fix, a reachable compositor plus `--no-float` meant the
    whole float step was skipped, so a terminal that started and then
    died left no diagnostic at all on this path.
    """

    def test_a_vanished_terminal_is_still_reported(self, monkeypatch, tmp_path):
        class DeadChild:
            pid = 4321

            def poll(self):
                return 7

        monkeypatch.setattr(
            seams_launch.subprocess, "Popen", lambda argv, **kw: DeadChild()
        )

        class NoWindows:
            def wait_for_window(self, pids, timeout, **kwargs):
                return None

            def float_window(self, con_id):
                raise AssertionError("floating was never asked for")

        with pytest.raises(DovetailError) as caught:
            launch_module.launch(
                tmp_path / "note.md",
                None,
                terminal="foot -e",
                float_window=False,
                compositor=NoWindows(),
                environ={"DOVETAIL_TERMINAL": "foot -e"},
            )
        assert "status 7" in str(caught.value)

    def test_a_window_that_appears_is_never_floated(self, monkeypatch, tmp_path):
        class AliveChild:
            pid = 4321

            def poll(self):
                return None

        monkeypatch.setattr(
            seams_launch.subprocess, "Popen", lambda argv, **kw: AliveChild()
        )

        class FoundWindow:
            def wait_for_window(self, pids, timeout, **kwargs):
                return 1

            def float_window(self, con_id):
                raise AssertionError("floating was never asked for")

        launch_module.launch(
            tmp_path / "note.md",
            None,
            terminal="foot -e",
            float_window=False,
            compositor=FoundWindow(),
            environ={"DOVETAIL_TERMINAL": "foot -e"},
        )

    def test_a_window_not_yet_seen_is_a_warning_not_a_failure(
        self, monkeypatch, tmp_path, capsys
    ):
        class AliveChild:
            pid = 4321

            def poll(self):
                return None

        monkeypatch.setattr(
            seams_launch.subprocess, "Popen", lambda argv, **kw: AliveChild()
        )

        class NoWindowYet:
            def wait_for_window(self, pids, timeout, **kwargs):
                return None

        launch_module.launch(
            tmp_path / "note.md",
            None,
            terminal="foot -e",
            float_window=False,
            compositor=NoWindowYet(),
            environ={"DOVETAIL_TERMINAL": "foot -e"},
        )
        assert "no window was seen" in capsys.readouterr().err

    def test_a_daemonizing_terminal_does_not_run_the_wait_to_its_budget(
        self, monkeypatch, tmp_path
    ):
        # footclient et al. exit 0 immediately, handing the real window
        # to an already-running server that is no descendant of the
        # spawned child. The window wait cannot ever see that window, so
        # it must stop as soon as the child is confirmed dead rather than
        # running the compositor's whole timeout for a launch that
        # already succeeded.
        class CleanlyExitedChild:
            pid = 4321

            def poll(self):
                return 0

        monkeypatch.setattr(
            seams_launch.subprocess, "Popen", lambda argv, **kw: CleanlyExitedChild()
        )

        class RecordingCompositor:
            def wait_for_window(self, pids, timeout, **kwargs):
                assert "alive" in kwargs
                assert kwargs["alive"]() is False
                return None

        launch_module.launch(
            tmp_path / "note.md",
            None,
            terminal="foot -e",
            float_window=False,
            compositor=RecordingCompositor(),
            environ={"DOVETAIL_TERMINAL": "foot -e"},
        )
