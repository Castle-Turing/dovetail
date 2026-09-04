"""The private-layer slots: which terminal, and which editor."""

from __future__ import annotations

import pytest

from dovetail_show.defaults import DEFAULT_EDITOR
from dovetail_show.errors import ShowError
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
