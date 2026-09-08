"""The provenance block, and the argv that carries it to the terminal."""

from pathlib import Path

from dovetail_run import prompt


def lines(*args, **kwargs):
    return prompt.provenance(*args, **kwargs).splitlines()


def test_the_block_names_the_proposer_and_the_reason():
    block = prompt.provenance("castle-turing worker seat", "the deploy needs it")
    assert "# Proposed by: castle-turing worker seat" in block
    assert "# Why: the deploy needs it" in block


def test_the_block_still_prints_when_nothing_was_given():
    block = prompt.provenance()
    assert "unattributed" in block
    assert "not stated" in block


def test_a_missing_reason_is_named_without_hiding_the_proposer():
    block = prompt.provenance("an agent session", None)
    assert "# Proposed by: an agent session" in block
    assert "# Why: not stated" in block


def test_a_blank_argument_is_treated_as_absent():
    assert prompt.provenance("   ", "  ") == prompt.provenance()


def test_every_line_of_the_block_is_a_comment():
    assert all(line.startswith("# ") for line in lines("someone", "some reason"))


def test_the_block_says_nothing_has_run_and_how_to_decline():
    block = prompt.provenance()
    assert "Nothing has run yet" in block
    assert "clear it to decline" in block


def test_recording_is_silent_by_default():
    block = prompt.provenance("a seat", "because")
    assert "recorded" not in block
    assert len(lines("a seat", "because")) == 4


def test_recording_true_says_so_before_the_resident_decides():
    block = prompt.provenance("a seat", "because", recording=True)
    assert "recorded" in block
    assert len(lines("a seat", "because", recording=True)) == 5
    # Told before the instructions, not after — she reads it before
    # deciding whether to run anything.
    assert block.index("recorded") < block.index("Press Enter")


def test_the_wrapper_argv_is_bash_the_script_and_five_strings():
    argv = prompt.wrapper_argv("# block", "echo hi")
    assert len(argv) == 7
    assert argv[0].endswith("bash")
    assert argv[1] == str(prompt.WRAPPER)
    assert argv[2:] == ["# block", "echo hi", "", "", ""]


def test_the_record_path_and_raw_provenance_trail_the_command():
    argv = prompt.wrapper_argv(
        "# block", "echo hi", record_path="/tmp/r.json", proposer="a seat", why="because"
    )
    assert argv[2:] == ["# block", "echo hi", "/tmp/r.json", "a seat", "because"]


def test_without_a_transcript_path_the_argv_is_byte_identical_to_0010s():
    with_record = prompt.wrapper_argv(
        "# block", "echo hi", record_path="/tmp/r.json", proposer="a seat", why="because"
    )
    without_transcript = prompt.wrapper_argv(
        "# block",
        "echo hi",
        record_path="/tmp/r.json",
        proposer="a seat",
        why="because",
        transcript_path="",
    )
    assert with_record == without_transcript
    assert len(with_record) == 7


def test_a_transcript_path_appends_the_baked_recorder_and_its_own_path():
    argv = prompt.wrapper_argv(
        "# block",
        "echo hi",
        record_path="/tmp/r.json",
        proposer="a seat",
        why="because",
        transcript_path="/tmp/r.json.transcript",
    )
    assert len(argv) == 9
    assert argv[7].endswith("script")
    assert argv[8] == "/tmp/r.json.transcript"


def test_the_wrapper_is_shipped_beside_the_module():
    assert Path(prompt.WRAPPER).is_file()
