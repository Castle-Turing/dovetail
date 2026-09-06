"""What is refused, and what the refusal says.

These are the rules the verb's one promise rests on — the line that is
displayed is the line that runs — so each class of character gets its
own case, and every case asserts that the refusal names the character
and where it is rather than only that it happened.
"""

import pytest

from dovetail_seams.errors import DovetailError

from dovetail_run import sanitize


def refusal(text, what="the command"):
    with pytest.raises(DovetailError) as caught:
        sanitize.check(text, what)
    return str(caught.value)


@pytest.mark.parametrize(
    "character, code",
    [
        ("\n", "U+000A"),
        ("\t", "U+0009"),
        ("\r", "U+000D"),
        ("\x1b", "U+001B"),
        ("\x00", "U+0000"),
        ("\x7f", "U+007F"),
        ("\x85", "U+0085"),
        ("‮", "U+202E"),
        ("⁦", "U+2066"),
        ("‏", "U+200F"),
        ("؜", "U+061C"),
        (" ", "U+2028"),
        ("​", "U+200B"),
        ("﻿", "U+FEFF"),
        ("­", "U+00AD"),
    ],
)
def test_every_refused_class_is_refused_by_code_point(character, code):
    message = refusal(f"echo hi{character}")
    assert code in message


def test_the_refusal_names_the_offset():
    message = refusal("echo\thi")
    assert "at offset 4" in message


def test_the_offset_is_counted_in_characters_not_bytes():
    # The heart is three bytes and one character, so the tab after it is
    # at offset 6 for a caller slicing the string it passed in.
    message = refusal("echo ♥ ‮hi")
    assert "at offset 7" in message


def test_the_refusal_names_the_argument_it_is_about():
    assert "--why" in refusal("because\nof this", "--why")


def test_the_first_refused_character_is_the_one_reported():
    message = refusal("a\tb\nc")
    assert "U+0009" in message
    assert "U+000A" not in message


def test_a_tab_is_named_as_a_tab():
    assert "tab" in refusal("echo\thi")


@pytest.mark.parametrize(
    "command",
    [
        "nixos-rebuild switch --flake .#castle",
        "git log --oneline -5",
        'printf "%s\\n" "quotes and \\\\ backslashes"',
        "echo ♥ é 👩‍💻",  # non-ASCII text, including a joined emoji
        "  leading and trailing spaces  ",
    ],
)
def test_ordinary_commands_pass_through_unchanged(command):
    assert sanitize.check_command(command) == command


@pytest.mark.parametrize("command", ["", " ", " " * 3])
def test_an_empty_or_whitespace_only_command_is_refused(command):
    with pytest.raises(DovetailError) as caught:
        sanitize.check_command(command)
    assert "empty" in str(caught.value)


def test_the_zero_width_joiner_is_allowed():
    # Load-bearing inside ordinary text — an emoji sequence in a commit
    # message — and it hides nothing that is not visible beside it.
    assert sanitize.check("git commit -m '👩‍💻'", "the command")


def test_describe_names_a_character_with_a_unicode_name():
    assert sanitize.describe("‮") == "U+202E RIGHT-TO-LEFT OVERRIDE"
