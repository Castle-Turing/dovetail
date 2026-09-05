"""Reading the process table out of /proc."""

from __future__ import annotations

import os
import sys

import pytest

from dovetail_seams.processes import (
    descendant_depths,
    parse_ppid,
    read_process_table,
)


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


class TestUnusualProcessNames:
    def test_a_comm_with_invalid_utf8_does_not_break_discovery(self, tmp_path):
        # `comm` is whatever bytes a process chose for itself, so invalid
        # UTF-8 is legal. Decoding strictly would raise UnicodeDecodeError
        # — not an OSError — and one such process anywhere on the machine
        # would take down all of discovery rather than being skipped.
        proc = tmp_path / "proc"
        (proc / "111").mkdir(parents=True)
        (proc / "111" / "stat").write_bytes(b"111 (od\xffd) S 100 111 0\n")
        (proc / "222").mkdir(parents=True)
        (proc / "222" / "stat").write_bytes(b"222 (nvim) S 111 222 0\n")

        assert read_process_table(str(proc)) == {111: 100, 222: 111}


class TestDescendantDepths:
    def test_counts_distance_from_the_root(self):
        table = {10: 1, 20: 10, 30: 20, 40: 1}
        assert descendant_depths(table, 10) == {10: 0, 20: 1, 30: 2}

    def test_a_cycle_in_a_torn_snapshot_terminates(self):
        table = {10: 20, 20: 10}
        assert descendant_depths(table, 10) == {10: 0, 20: 1}
