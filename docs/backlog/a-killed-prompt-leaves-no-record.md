# A killed prompt leaves no record

**What.** `dovetail run --record` writes its record when the prompt
ends by acceptance, edit, or decline — but not when it ends by Ctrl-C
or the window dying. `prompt.bash` sets no traps, so SIGINT and SIGHUP
end the wrapper with nothing written. A caller polling the record path
cannot tell "the resident is still deciding" from "the prompt is gone",
and waits forever; a caller-side timeout is a guess about a human's
pace.

**Why it matters.** The record exists so the proposing agent closes the
loop from artifact state, never from say-so — the M3 reasoning in
`docs/vision.md`. The most abrupt refusal a resident can make, killing
the window, is also the one that leaves the agent blind. That silently
reopens the gap the record was built to close.

**What we already know.** This was chosen deliberately in task 0010 and
recorded in its judgment calls: the killed endings sit outside the
three the brief verified (accepted, edited, declined), and
`docs/run.md` documents Ctrl-C as closing "without a word". The
machinery a fix needs already exists — the wrapper holds the record
path before the read begins, and the record writer is atomic
(temp-and-rename), so a trap-written record cannot be half-read. A bash
`trap` on INT is dependable; what a compositor-closed window actually
delivers to the wrapper depends on the terminal emulator, and should be
verified against a real one rather than assumed.

**Open questions.** Is a killed prompt a third state in the record, or
is `declined` the honest word for both — does the correction signal
care how the no was said? Should the wrapper also write an opened
marker when the prompt appears, so a poller can tell "never appeared"
from "still open", or is that scope creep past what the record is for?
And what does the reference terminal actually send its child when its
window is closed?
