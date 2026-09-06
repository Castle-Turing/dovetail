"""What is refused, so that what is displayed is what runs.

The whole hazard this verb is built around is a resident pressing Enter
on a line she has read. That is only safe if the line she read is the
line the shell gets — and a handful of characters break exactly that
correspondence. A terminal shows a tab as whitespace, hides a bidi
override entirely while reordering everything after it, and treats a
newline as the end of the line, which is to say as an Enter nobody
pressed. Any of them makes the displayed line and the executed line two
different things, which is the paste-jacking class in one sentence.

Every function here is pure and takes its text as an argument: the
rules are the part of this verb most worth testing, and none of them
needs a terminal, a compositor or a process to be checked.

Refusal is never repair. Stripping the offending character would leave
the caller with a command they never wrote, running with the resident's
privileges, and the resident with no way to tell that happened. Naming
the character and its offset lets the caller fix their own string.
"""

from __future__ import annotations

import unicodedata

from dovetail_seams.errors import DovetailError

# The C0 controls, including tab and newline, plus DEL. A terminal
# renders none of them as themselves: tab is whitespace of unpredictable
# width, escape starts a sequence that can rewrite anything already on
# screen, carriage return puts the cursor back over what it just drew,
# and a newline ends the line — the one keystroke this verb exists to
# leave to the resident.
_C0_AND_DEL = frozenset(range(0x00, 0x20)) | {0x7F}

# The C1 range. Rarely typed on purpose, and in some terminal encodings
# still parsed as control functions rather than shown.
_C1 = frozenset(range(0x80, 0xA0))

# Unicode's bidirectional controls, in full: the embeddings, overrides
# and isolates named in the brief, and also the three directional marks
# (U+061C, U+200E, U+200F), which the brief did not name and which
# belong to the same class — the Bidi_Control property is exactly these
# nine code points. They reorder what is drawn without changing a byte
# of what runs, which is the definition of the hazard.
_BIDI = frozenset(
    {0x061C, 0x200E, 0x200F} | set(range(0x202A, 0x202F)) | set(range(0x2066, 0x206A))
)

# Line and paragraph separators. Not C0, but a terminal or a pager may
# break the line at one, so half the command can be drawn where the
# resident is not looking. Same failure as a newline, different code
# point.
_SEPARATORS = frozenset({0x2028, 0x2029})

# Characters that occupy no width at all: a soft hyphen, a zero-width
# space, a byte-order mark in the middle of a line. `rm /tmp<ZWSP>x`
# reads as one path and runs as another, which is the hazard with no
# escape sequence involved.
#
# The zero-width joiner and non-joiner (U+200D, U+200C) are deliberately
# *not* here. They are load-bearing inside ordinary text — an emoji
# sequence in a commit message is the obvious case — so refusing them
# would reject commands a resident legitimately means to run, and they
# do not hide anything that is not already visible beside them.
_INVISIBLE = frozenset({0x00AD, 0x200B, 0xFEFF})

_REFUSED = _C0_AND_DEL | _C1 | _BIDI | _SEPARATORS | _INVISIBLE

# The C0 and C1 code points have no Unicode names, so the ones a caller
# is most likely to have typed by accident are named here. Anything else
# in those ranges is described by its range rather than guessed at.
_CONTROL_NAMES = {
    0x00: "NULL",
    0x07: "BELL",
    0x08: "BACKSPACE",
    0x09: "CHARACTER TABULATION (tab)",
    0x0A: "LINE FEED (newline)",
    0x0B: "LINE TABULATION",
    0x0C: "FORM FEED",
    0x0D: "CARRIAGE RETURN",
    0x1B: "ESCAPE",
    0x7F: "DELETE",
}

_REFUSAL = """{what} contains {description}, at offset {offset}

Dovetail refuses it rather than repairing it. This verb's one promise is
that the line you read is the line that runs, and that character can
make those two things differ — it is drawn as something other than
itself, or not drawn at all. Stripping it would hand you a command
nobody wrote.

Send the command without it. If you meant several commands, they are
several invocations: a newline is refused with the rest of the control
characters, so there are no multi-line proposals."""

_EMPTY_REFUSAL = """the command is empty, and there is nothing to propose

COMMAND is the exact shell line the resident would type. A blank line
would open a terminal showing a provenance comment above an empty
prompt, which tells her nothing about what you wanted."""


def describe(character: str) -> str:
    """`U+0009 CHARACTER TABULATION (tab)`, for a refusal to quote."""

    point = ord(character)
    name = _CONTROL_NAMES.get(point) or unicodedata.name(character, "")
    if not name:
        name = "a C1 control character" if point in _C1 else "an unnamed character"
    return f"U+{point:04X} {name}"


def check(text: str, what: str) -> str:
    """`text` unchanged, or a refusal naming the first character refused.

    `what` names the thing being checked — "the command", "--from" — so
    that a caller passing three strings through here learns which of
    them to fix. The offset is counted in characters from zero, which is
    what a caller slicing the string it just built needs.
    """

    for offset, character in enumerate(text):
        if ord(character) in _REFUSED:
            raise DovetailError(
                _REFUSAL.format(
                    what=what, description=describe(character), offset=offset
                )
            )
    return text


def check_command(command: str) -> str:
    """The proposed command, or a refusal.

    Empty and whitespace-only are refused before the character rules,
    because "the command is empty" is the more useful thing to say about
    a command that is a single space.
    """

    if not command.strip():
        raise DovetailError(_EMPTY_REFUSAL)
    return check(command, "the command")
