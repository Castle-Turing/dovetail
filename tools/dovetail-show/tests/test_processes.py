"""Reading the process table out of /proc."""

from __future__ import annotations

import os
import sys

import pytest

from dovetail_show.processes import parse_ppid, read_process_table


class TestParsePpid:
    def test_an_ordinary_line(self):
        assert parse_ppid("1234 (nvim) S 1200 1234 1234 0 -1 4194304") == 1200

    def test_a_comm_containing_spaces_and_parentheses(self):
        # `comm` is the first 15 bytes of the executable name and is not
        # escaped, so counting fields from the left is wrong.
        line = "1234 (my (odd) program) S 77 1234 0"
        assert parse_ppid(line) == 77

    def test_a_truncated_line_is_no_answer(self):
        assert parse_ppid("1234 (nvim)") is None

    def test_a_line_with_no_parenthesis_is_no_answer(self):
        assert parse_ppid("gibberish") is None


class TestReadProcessTable:
    def test_reads_a_directory_shaped_like_proc(self, tmp_path):
        for pid, ppid in ((10, 1), (20, 10)):
            entry = tmp_path / str(pid)
            entry.mkdir()
            (entry / "stat").write_text(f"{pid} (sh) S {ppid} {pid} 0\n")
        # Non-numeric entries and unreadable ones are skipped, not fatal.
        (tmp_path / "self").mkdir()
        (tmp_path / "30").mkdir()

        assert read_process_table(str(tmp_path)) == {10: 1, 20: 10}

    def test_a_missing_directory_is_an_empty_table(self, tmp_path):
        assert read_process_table(str(tmp_path / "absent")) == {}

    @pytest.mark.skipif(
        sys.platform != "linux", reason="/proc is a Linux interface"
    )
    def test_the_real_proc_contains_this_process(self):
        table = read_process_table()
        assert table.get(os.getpid()) == os.getppid()
