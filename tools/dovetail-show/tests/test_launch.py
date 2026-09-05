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
