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


def test_the_wrapper_argv_is_bash_the_script_and_two_strings():
    argv = prompt.wrapper_argv("# block", "echo hi")
    assert len(argv) == 4
    assert argv[0].endswith("bash")
    assert argv[1] == str(prompt.WRAPPER)
    assert argv[2:] == ["# block", "echo hi"]


def test_the_wrapper_is_shipped_beside_the_module():
    assert Path(prompt.WRAPPER).is_file()
