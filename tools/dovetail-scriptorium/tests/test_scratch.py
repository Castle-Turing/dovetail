"""The scratch file convention, tested with no home directory of its own.

Every case here is the convention in `docs/scriptorium.md` written as an
assertion: what the file is called, where it lives, what a bad topic
does, and the one thing that must never happen to an existing file.
"""

from __future__ import annotations

import datetime
import os
import stat

import pytest

from dovetail_scriptorium.scratch import (
    directory,
    ensure,
    file_name,
    scratch_file,
    validate_topic,
)
from dovetail_seams.errors import DovetailError

DAY = datetime.date(2026, 9, 5)


class TestTheName:
    def test_the_date_leads_so_a_listing_sorts_chronologically(self):
        assert file_name(DAY, "parser-rewrite") == "2026-09-05-parser-rewrite.md"

    def test_digits_and_single_words_are_topics_too(self):
        assert file_name(DAY, "0006") == "2026-09-05-0006.md"
        assert file_name(DAY, "notes") == "2026-09-05-notes.md"


class TestTheTopicIsRefusedNotRepaired:
    """A caller who typed spaces wants to know what the file will be
    called now, not to discover a guess later."""

    @pytest.mark.parametrize(
        "topic",
        [
            "parser rewrite",  # spaces
            "Parser-Rewrite",  # capitals
            "parser_rewrite",  # underscores
            "parser.rewrite",  # dots
            "../escape",  # a path, not a topic
            "-leading",
            "trailing-",
            "two--hyphens",
            "",
        ],
    )
    def test_it_refuses(self, topic):
        with pytest.raises(DovetailError):
            validate_topic(topic)

    def test_the_refusal_says_what_a_topic_is_and_suggests_one(self):
        with pytest.raises(DovetailError) as caught:
            validate_topic("Parser Rewrite")
        message = str(caught.value)
        assert "lowercase" in message
        # Shown, never silently used.
        assert "parser-rewrite" in message

    def test_a_valid_topic_comes_back_unchanged(self):
        assert validate_topic("m2-layout-0006") == "m2-layout-0006"


class TestWhereItLives:
    HOME = {"HOME": "/home/resident"}

    def test_the_command_line_wins(self, tmp_path):
        environ = {"DOVETAIL_SCRATCH_DIR": "/from/env", **self.HOME}
        assert str(directory("/from/flag", environ)) == "/from/flag"

    def test_then_dovetail_scratch_dir(self):
        environ = {
            "DOVETAIL_SCRATCH_DIR": "/from/env",
            "XDG_DATA_HOME": "/from/xdg",
            **self.HOME,
        }
        assert str(directory(None, environ)) == "/from/env"

    def test_then_xdg_data_home(self):
        environ = {"XDG_DATA_HOME": "/from/xdg", **self.HOME}
        assert str(directory(None, environ)) == "/from/xdg/dovetail/scratch"

    def test_then_the_home_fallback(self):
        assert str(directory(None, self.HOME)) == (
            "/home/resident/.local/share/dovetail/scratch"
        )

    def test_a_tilde_is_expanded(self):
        assert str(directory("~/thinking", self.HOME)).endswith("/thinking")
        assert "~" not in str(directory("~/thinking", self.HOME))

    def test_a_relative_xdg_data_home_is_ignored_as_the_spec_requires(self):
        # The specification says a non-absolute $XDG_DATA_HOME must be
        # treated as unset; honouring it keeps a stray relative setting
        # from creating a scratch directory under the caller's cwd.
        environ = {"XDG_DATA_HOME": "relative/path", **self.HOME}
        assert str(directory(None, environ)) == (
            "/home/resident/.local/share/dovetail/scratch"
        )

    def test_an_empty_setting_is_not_a_directory(self):
        environ = {"DOVETAIL_SCRATCH_DIR": "   ", "XDG_DATA_HOME": "", **self.HOME}
        assert str(directory(None, environ)) == (
            "/home/resident/.local/share/dovetail/scratch"
        )

    def test_no_home_at_all_refuses_and_says_what_to_set(self):
        with pytest.raises(DovetailError) as caught:
            directory(None, {})
        assert "DOVETAIL_SCRATCH_DIR" in str(caught.value)

    def test_the_path_is_absolute_because_the_editors_cwd_is_not_ours(self):
        path = scratch_file("notes", explicit_directory="thinking", today=DAY)
        assert path.is_absolute()
        assert path.name == "2026-09-05-notes.md"


class TestReopeningIsAFeature:
    def test_an_existing_file_is_left_byte_identical(self, tmp_path):
        path = tmp_path / "scratch" / "2026-09-05-notes.md"
        path.parent.mkdir()
        path.write_text("# Yesterday's thinking\n\nStill here.\n")
        before = path.read_bytes()
        stamp = os.stat(path).st_mtime_ns

        ensure(path)

        assert path.read_bytes() == before
        # Not even the modification time moves: O_CREAT without O_TRUNC
        # on an existing file does nothing at all.
        assert os.stat(path).st_mtime_ns == stamp

    def test_a_missing_file_is_created_empty(self, tmp_path):
        path = tmp_path / "scratch" / "2026-09-05-notes.md"
        ensure(path)
        assert path.exists()
        # Dovetail never writes a line into it; the first line is the
        # resident's.
        assert path.read_bytes() == b""

    def test_missing_directories_are_created_private(self, tmp_path):
        path = tmp_path / "deep" / "scratch" / "2026-09-05-notes.md"
        ensure(path)
        assert path.parent.is_dir()
        mode = stat.S_IMODE(os.stat(path.parent).st_mode)
        assert mode == 0o700
        assert stat.S_IMODE(os.stat(path).st_mode) == 0o600

    def test_a_directory_that_cannot_be_made_is_a_diagnostic(self, tmp_path):
        blocker = tmp_path / "not-a-directory"
        blocker.write_text("")
        with pytest.raises(DovetailError) as caught:
            ensure(blocker / "scratch" / "notes.md")
        assert "scratch directory" in str(caught.value)
