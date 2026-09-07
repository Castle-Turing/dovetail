# A killed prompt leaves no record

**What.** The proposed `dovetail run` verb (backlog:
`an-agent-cannot-hand-the-resident-a-command.md`) is meant to record
how a handed-off command was resolved — accepted, edited, or declined
— so the proposing agent can close the loop from artifact state rather
than say-so. That design does not yet account for the resident's most
abrupt refusal: killing the window (Ctrl-C, or the window dying
outright) leaves no record at all. A caller polling for the record
cannot tell "the resident is still deciding" from "the prompt is gone",
and would be left guessing at a human's pace with a timeout.

**Why it matters.** The whole point of the record is to make the
outcome verifiable from disk, never from a claim. A resolution path
that produces no record on the most common form of refusal silently
reopens the gap the verb was built to close, before the verb is even
built.

**What we already know.** Nothing yet — `dovetail run` has no task
brief, no wrapper, and no record writer in this tree; this entry
exists so the gap is designed for rather than discovered after the
fact. Whoever specs the verb should decide its signal handling (a bash
`trap` on INT is dependable; what a compositor-closed window actually
delivers to a child process is terminal-emulator-dependent and should
be verified against the reference terminal rather than assumed), and
should consider making the record writer atomic (temp-and-rename) from
the start, so a trap-written record cannot be read half-written.

**Open questions.** Is a killed prompt a fourth outcome in the record,
alongside accepted/edited/declined, or is `declined` the honest word
for every silent refusal — does the correction signal care how the no
was said? Should the wrapper also write an opened marker when the
prompt appears, so a poller can tell "never appeared" from "still
open", or is that scope creep past what the record is for? And what
does the reference terminal actually send its child when its window is
closed?
