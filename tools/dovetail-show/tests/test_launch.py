"""The private-layer slots: which terminal, and which editor."""

from __future__ import annotations

import subprocess

import pytest

from dovetail_show.defaults import DEFAULT_EDITOR
from dovetail_show.errors import ShowError
from dovetail_show import launch as launch_module
from dovetail_show.launch import editor_command, terminal_argv


class TestTerminalArgv:
    def test_the_command_line_wins(self):
        assert terminal_argv(
            "alacritty -e", {"DOVETAIL_TERMINAL": "foot -e", "TERMINAL": "xterm -e"}
        ) == ["alacritty", "-e"]

    def test_then_dovetail_terminal(self):
        assert terminal_argv(None, {"DOVETAIL_TERMINAL": "foot -e", "TERMINAL": "xterm"}) == [
            "foot",
            "-e",
        ]

    def test_then_terminal(self):
        assert terminal_argv(None, {"TERMINAL": "xterm -e"}) == ["xterm", "-e"]

    def test_it_is_an_argv_prefix_with_shell_quoting(self):
        # Dovetail knows nothing about any particular terminal: whatever
        # prefix the resident writes is appended to, verbatim.
        assert terminal_argv(None, {"DOVETAIL_TERMINAL": "wezterm start --"}) == [
            "wezterm",
            "start",
            "--",
        ]
        assert terminal_argv(
            None, {"DOVETAIL_TERMINAL": "'/opt/my terminal/bin/term' --run"}
        ) == ["/opt/my terminal/bin/term", "--run"]

    def test_no_terminal_fails_loudly_naming_both_variables(self):
        with pytest.raises(ShowError) as caught:
            terminal_argv(None, {})
        message = str(caught.value)
        assert "DOVETAIL_TERMINAL" in message
        assert "TERMINAL" in message
        # An example, so the reader does not have to guess the shape.
        assert "foot -e" in message

    def test_an_empty_setting_is_not_a_terminal(self):
        with pytest.raises(ShowError):
            terminal_argv(None, {"DOVETAIL_TERMINAL": "   ", "TERMINAL": ""})


class TestEditorCommand:
    def test_the_build_time_default(self):
        assert editor_command({}) == DEFAULT_EDITOR

    def test_the_runtime_override(self):
        # A resident whose private layer builds its own nixvim wants her
        # build launched, not ours.
        assert editor_command({"DOVETAIL_EDITOR": "/home/resident/bin/nvim"}) == (
            "/home/resident/bin/nvim"
        )


class TestMalformedTerminalQuoting:
    def test_an_unmatched_quote_is_a_show_error_naming_the_setting(self):
        # shlex.split raises ValueError, which is not a ShowError and
        # would reach the user as a traceback.
        with pytest.raises(ShowError) as caught:
            terminal_argv(None, {"DOVETAIL_TERMINAL": 'foot -e "unclosed'})
        assert "$DOVETAIL_TERMINAL" in str(caught.value)

    def test_the_flag_is_named_when_the_flag_is_at_fault(self):
        with pytest.raises(ShowError) as caught:
            terminal_argv('foot -e "unclosed', {})
        assert "--terminal" in str(caught.value)


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

        monkeypatch.setattr(launch_module.subprocess, "Popen", fake_popen)
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
            launch_module.subprocess, "Popen", lambda argv, **kw: DeadChild()
        )

        class NoWindows:
            def wait_for_window(self, pids, timeout, **kwargs):
                return None

        with pytest.raises(ShowError) as caught:
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
            launch_module.subprocess, "Popen", lambda argv, **kw: DeadChild()
        )

        class NoWindows:
            def wait_for_window(self, pids, timeout, **kwargs):
                return None

            def float_window(self, con_id):
                raise AssertionError("floating was never asked for")

        with pytest.raises(ShowError) as caught:
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
            launch_module.subprocess, "Popen", lambda argv, **kw: AliveChild()
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
            launch_module.subprocess, "Popen", lambda argv, **kw: AliveChild()
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
            launch_module.subprocess, "Popen", lambda argv, **kw: CleanlyExitedChild()
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


class TestNoCompositorLivenessWatch:
    """A short, driven-clock watch of the child when there is no tree to poll."""

    def test_a_child_that_exits_within_budget_is_reported(self):
        class DyingChild:
            pid = 1
            _polls = iter([None, None, 5])

            def poll(self):
                return next(self._polls)

        clock = _Clock(step=0.5)
        with pytest.raises(ShowError) as caught:
            launch_module._watch_liveness(
                DyingChild(),
                ["broken-terminal"],
                budget=2.0,
                monotonic=clock.read,
                sleep=lambda _: None,
            )
        assert "status 5" in str(caught.value)
        assert "broken-terminal" in str(caught.value)

    def test_a_child_alive_at_the_end_of_the_budget_passes(self):
        class AliveChild:
            pid = 1

            def poll(self):
                return None

        clock = _Clock(step=0.5)
        # Should return normally: no exception, no window to check.
        launch_module._watch_liveness(
            AliveChild(),
            ["some-terminal"],
            budget=2.0,
            monotonic=clock.read,
            sleep=lambda _: None,
        )

    def test_a_clean_exit_within_budget_is_not_a_failure(self):
        class CleanExitChild:
            pid = 1

            def poll(self):
                return 0

        clock = _Clock(step=0.5)
        # A clean exit (e.g. a terminal that daemonizes) is not reported.
        launch_module._watch_liveness(
            CleanExitChild(),
            ["some-terminal"],
            budget=2.0,
            monotonic=clock.read,
            sleep=lambda _: None,
        )

    def test_the_watch_never_outlives_its_budget(self):
        class NeverDies:
            pid = 1

            def poll(self):
                return None

        # `monotonic` only reports time; `sleep` is what advances it, the
        # same convention `TestWaitForWindow` in test_compositor.py uses,
        # so a sleep clamped correctly is the only way this clock moves
        # past the budget at all.
        clock = _Clock(step=0.0)
        launch_module._watch_liveness(
            NeverDies(),
            ["some-terminal"],
            budget=1.0,
            interval=0.3,
            monotonic=clock.read,
            sleep=clock.advance,
        )
        # Each sleep is clamped to what is left of the budget, so the
        # clock lands exactly on the deadline rather than overshooting it.
        assert clock.now == 1.0


class _Clock:
    """A clock that advances on every reading, so no test really waits."""

    def __init__(self, step=0.1):
        self.now = 0.0
        self.step = step

    def read(self):
        self.now += self.step
        return self.now

    def advance(self, seconds):
        self.now += seconds
