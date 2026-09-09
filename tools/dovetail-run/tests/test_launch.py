"""How the verb composes the shared machinery: argv, and the order.

The slots and the spawn/wait machinery belong to `dovetail_seams` and
are tested there. What is asserted here is only run's own composition of
them — what ends up on the terminal's command line, and that everything
refusable is refused before anything is spawned.
"""

from __future__ import annotations

import pytest

from dovetail_seams import launch as seams_launch
from dovetail_seams.errors import DovetailError

from dovetail_run import cli
from dovetail_run import prompt as prompt_module


class FakeChild:
    pid = 4321

    def poll(self):
        return None


@pytest.fixture
def spawned(monkeypatch):
    """Record what would have been spawned, and spawn nothing."""

    recorded = []

    def fake_popen(argv, **kwargs):
        recorded.append(argv)
        return FakeChild()

    monkeypatch.setattr(seams_launch.subprocess, "Popen", fake_popen)
    # No compositor, and a liveness watch that returns at once: a fake
    # child that never exits is fine either way, and this keeps the
    # tests off the wall clock.
    monkeypatch.setattr(seams_launch, "watch_liveness", lambda *a, **k: None)
    return recorded


ENV = {"DOVETAIL_TERMINAL": "foot -e"}


def test_the_wrapper_is_appended_to_the_terminal_argv_prefix(spawned):
    assert cli.run(["echo hi"], environ=ENV) == 0
    argv = spawned[0]
    assert argv[:2] == ["foot", "-e"]
    assert argv[2].endswith("bash")
    assert argv[3] == str(prompt_module.WRAPPER)


def test_the_command_reaches_the_wrapper_as_one_untouched_argument(spawned):
    command = "nixos-rebuild switch --flake .#castle  # note the spaces"
    cli.run([command, "--from", "an agent"], environ=ENV)
    assert spawned[0][5] == command


def test_the_provenance_block_is_the_argument_before_the_command(spawned):
    cli.run(["echo hi", "--from", "a seat", "--why", "because"], environ=ENV)
    block = spawned[0][4]
    assert "# Proposed by: a seat" in block
    assert "# Why: because" in block


def test_without_record_the_trailing_record_argument_is_empty(spawned):
    cli.run(["echo hi"], environ=ENV)
    assert spawned[0][6:] == ["", "", ""]


def test_record_reaches_the_wrapper_as_the_argument_after_the_command(
    spawned, tmp_path
):
    record_path = tmp_path / "record.json"
    cli.run(["echo hi", "--record", str(record_path)], environ=ENV)
    assert spawned[0][6] == str(record_path)


def test_from_and_why_reach_the_wrapper_raw_alongside_the_record_path(
    spawned, tmp_path
):
    record_path = tmp_path / "record.json"
    cli.run(
        ["echo hi", "--record", str(record_path), "--from", "a seat", "--why", "because"],
        environ=ENV,
    )
    assert spawned[0][6:9] == [str(record_path), "a seat", "because"]


def test_a_record_path_grows_a_transcript_path_and_the_baked_recorder(
    spawned, tmp_path
):
    record_path = tmp_path / "record.json"
    cli.run(["echo hi", "--record", str(record_path)], environ=ENV)
    argv = spawned[0]
    assert len(argv) == 11
    assert argv[9].endswith("script")
    assert argv[10] == str(record_path) + ".transcript"


def test_recording_is_announced_in_the_provenance_block(spawned, tmp_path):
    record_path = tmp_path / "record.json"
    cli.run(["echo hi", "--record", str(record_path)], environ=ENV)
    assert "recorded" in spawned[0][4]


def test_a_record_path_whose_parent_directory_is_missing_is_refused_before_spawning(
    spawned, tmp_path
):
    record_path = tmp_path / "nonexistent" / "record.json"
    with pytest.raises(DovetailError) as caught:
        cli.run(["echo hi", "--record", str(record_path)], environ=ENV)
    assert str(record_path) in str(caught.value)
    assert spawned == []


def test_a_prefix_with_more_than_two_words_is_kept_whole(spawned):
    cli.run(["echo hi"], environ={"DOVETAIL_TERMINAL": "wezterm start --"})
    assert spawned[0][:3] == ["wezterm", "start", "--"]


def test_the_terminal_flag_beats_the_environment(spawned):
    cli.run(["echo hi", "--terminal", "kitty --"], environ=ENV)
    assert spawned[0][:2] == ["kitty", "--"]


@pytest.mark.parametrize(
    "argv",
    [
        ["echo\thi"],
        [""],
        ["   "],
        ["echo hi", "--from", "a\nseat"],
        ["echo hi", "--why", "because\x1b[2Kof this"],
    ],
)
def test_a_refused_argument_spawns_nothing_at_all(spawned, argv):
    with pytest.raises(DovetailError):
        cli.run(argv, environ=ENV)
    assert spawned == []


def test_an_unset_terminal_is_refused_before_anything_is_spawned(spawned):
    with pytest.raises(DovetailError) as caught:
        cli.run(["echo hi"], environ={"HOME": "/nonexistent"})
    assert "no terminal is configured" in str(caught.value)
    assert spawned == []


def test_main_turns_a_refusal_into_a_diagnostic_and_exit_one(spawned, capsys):
    assert cli.main(["echo\thi"]) == 1
    assert "dovetail-run:" in capsys.readouterr().err
    assert spawned == []
