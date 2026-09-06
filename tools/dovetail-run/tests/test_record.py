"""The record: its one dict shape, the path refusal, and the atomic write."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from dovetail_seams.errors import DovetailError

from dovetail_run import record


def test_check_record_path_refuses_a_missing_parent_directory(tmp_path):
    missing = tmp_path / "nonexistent" / "record.json"
    with pytest.raises(DovetailError) as caught:
        record.check_record_path(str(missing))
    assert str(missing) in str(caught.value)


def test_check_record_path_accepts_an_existing_parent_directory(tmp_path):
    path = tmp_path / "record.json"
    assert record.check_record_path(str(path)) == path


def test_build_record_has_exactly_the_documented_fields():
    built = record.build_record(
        proposed="echo hi",
        executed="echo hi",
        declined=False,
        exit_status=0,
        from_="a seat",
        why="because",
        proposed_at="2026-09-06T00:00:00Z",
        finished_at="2026-09-06T00:00:01Z",
    )
    assert built == {
        "proposed": "echo hi",
        "executed": "echo hi",
        "declined": False,
        "exit_status": 0,
        "from": "a seat",
        "why": "because",
        "proposed_at": "2026-09-06T00:00:00Z",
        "finished_at": "2026-09-06T00:00:01Z",
    }


def test_build_record_allows_a_zero_exit_status_to_survive():
    built = record.build_record(
        proposed="true",
        executed="true",
        declined=False,
        exit_status=0,
        from_=None,
        why=None,
        proposed_at="t0",
        finished_at="t1",
    )
    assert built["exit_status"] == 0
    assert built["exit_status"] is not None


def test_build_record_a_decline_has_null_executed_and_exit_status():
    built = record.build_record(
        proposed="echo hi",
        executed=None,
        declined=True,
        exit_status=None,
        from_=None,
        why=None,
        proposed_at="t0",
        finished_at="t1",
    )
    assert built["executed"] is None
    assert built["exit_status"] is None
    assert built["declined"] is True


def test_write_produces_valid_json_readable_at_the_target_path(tmp_path):
    path = tmp_path / "record.json"
    built = record.build_record(
        proposed="echo hi",
        executed="echo hi",
        declined=False,
        exit_status=0,
        from_="a seat",
        why="because",
        proposed_at="t0",
        finished_at="t1",
    )
    record.write(path, built)
    assert json.loads(path.read_text()) == built


def test_write_leaves_no_temp_file_behind(tmp_path):
    path = tmp_path / "record.json"
    record.write(path, {"proposed": "echo hi"})
    assert sorted(p.name for p in tmp_path.iterdir()) == ["record.json"]


def test_write_is_atomic_via_rename_in_the_same_directory(tmp_path, monkeypatch):
    path = tmp_path / "record.json"
    seen_replace_args = []
    real_replace = record.os.replace

    def spying_replace(src, dst):
        # The temp file must already exist, in the same directory, at
        # the moment of rename — that is what makes the rename atomic
        # rather than a second, separate write.
        assert Path(src).parent == path.parent
        seen_replace_args.append((src, dst))
        return real_replace(src, dst)

    monkeypatch.setattr(record.os, "replace", spying_replace)
    record.write(path, {"proposed": "echo hi"})
    assert seen_replace_args == [(seen_replace_args[0][0], path)]


def test_main_writes_the_accepted_case(tmp_path):
    path = tmp_path / "record.json"
    status = record.main(
        [
            str(path),
            "false",
            "echo hi",
            "echo hi",
            "0",
            "a seat",
            "because",
            "t0",
            "t1",
        ]
    )
    assert status == 0
    assert json.loads(path.read_text()) == {
        "proposed": "echo hi",
        "executed": "echo hi",
        "declined": False,
        "exit_status": 0,
        "from": "a seat",
        "why": "because",
        "proposed_at": "t0",
        "finished_at": "t1",
    }


def test_main_writes_the_declined_case_with_nulls(tmp_path):
    path = tmp_path / "record.json"
    status = record.main(
        [str(path), "true", "echo hi", "", "", "", "", "t0", "t1"]
    )
    assert status == 0
    written = json.loads(path.read_text())
    assert written["declined"] is True
    assert written["executed"] is None
    assert written["exit_status"] is None
    assert written["from"] is None
    assert written["why"] is None


def test_main_treats_blank_from_and_why_as_absent(tmp_path):
    path = tmp_path / "record.json"
    record.main([str(path), "false", "echo hi", "echo hi", "0", "", "", "t0", "t1"])
    written = json.loads(path.read_text())
    assert written["from"] is None
    assert written["why"] is None


def test_main_rejects_the_wrong_number_of_arguments(capsys):
    assert record.main(["only", "one"]) == 2
    assert "expected" in capsys.readouterr().err
