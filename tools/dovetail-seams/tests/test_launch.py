"""The private-layer slots — which terminal, which editor, which REPL —
and the liveness watch that stands in for a window tree when there is no
compositor to ask."""

from __future__ import annotations

import pytest

from dovetail_seams.defaults import DEFAULT_EDITOR, DEFAULT_REPL
from dovetail_seams.errors import DovetailError
from dovetail_seams import launch as launch_module
from dovetail_seams.launch import editor_command, repl_argv, terminal_argv


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
        with pytest.raises(DovetailError) as caught:
            terminal_argv(None, {})
        message = str(caught.value)
        assert "DOVETAIL_TERMINAL" in message
        assert "TERMINAL" in message
        # An example, so the reader does not have to guess the shape.
        assert "foot -e" in message

    def test_an_empty_setting_is_not_a_terminal(self):
        with pytest.raises(DovetailError):
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
        # shlex.split raises ValueError, which is not a DovetailError and
        # would reach the user as a traceback.
        with pytest.raises(DovetailError) as caught:
            terminal_argv(None, {"DOVETAIL_TERMINAL": 'foot -e "unclosed'})
        assert "$DOVETAIL_TERMINAL" in str(caught.value)

    def test_the_flag_is_named_when_the_flag_is_at_fault(self):
        with pytest.raises(DovetailError) as caught:
            terminal_argv('foot -e "unclosed', {})
        assert "--terminal" in str(caught.value)

class TestReplArgv:
    """The REPL slot has a default, unlike the terminal slot."""

    def test_the_command_line_wins(self):
        assert repl_argv("ipython --no-banner", {"DOVETAIL_REPL": "python3 -q"}) == [
            "ipython",
            "--no-banner",
        ]

    def test_then_dovetail_repl(self):
        assert repl_argv(None, {"DOVETAIL_REPL": "python3 -q"}) == ["python3", "-q"]

    def test_nothing_set_is_the_build_time_default(self):
        # Unlike the terminal, this slot does not refuse: Dovetail builds
        # a Python and can hand the resident one hermetically.
        assert repl_argv(None, {}) == [DEFAULT_REPL]

    def test_an_empty_setting_falls_through_to_the_default(self):
        assert repl_argv(None, {"DOVETAIL_REPL": "   "}) == [DEFAULT_REPL]

    def test_an_unmatched_quote_names_the_setting(self):
        with pytest.raises(DovetailError) as caught:
            repl_argv(None, {"DOVETAIL_REPL": 'python3 -c "unclosed'})
        assert "$DOVETAIL_REPL" in str(caught.value)


class TestNoCompositorLivenessWatch:
    """A short, driven-clock watch of the child when there is no tree to poll."""

    def test_a_child_that_exits_within_budget_is_reported(self):
        class DyingChild:
            pid = 1
            _polls = iter([None, None, 5])

            def poll(self):
                return next(self._polls)

        clock = _Clock(step=0.5)
        with pytest.raises(DovetailError) as caught:
            launch_module.watch_liveness(
                DyingChild(),
                ["broken-terminal"],
                "nothing was started",
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
        launch_module.watch_liveness(
            AliveChild(),
            ["some-terminal"],
            "nothing was started",
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
        launch_module.watch_liveness(
            CleanExitChild(),
            ["some-terminal"],
            "nothing was started",
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
        launch_module.watch_liveness(
            NeverDies(),
            ["some-terminal"],
            "nothing was started",
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
