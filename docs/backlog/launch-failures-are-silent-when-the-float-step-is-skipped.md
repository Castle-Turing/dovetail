# Launch failures are silent when the float step is skipped

**What.** When `dovetail-show` launches an editor with `--no-float`, or
with no reachable compositor, a terminal that starts and then exits —
bad arguments in `$DOVETAIL_TERMINAL`, a broken configuration — produces
no window, no diagnostic, and a zero exit status unless `--print-socket`
was requested. The launch should notice the child died without a window
on these paths too, and say so.

**Why it matters.** The resident asked for a file and got nothing, and
the tool said everything went fine. Every other refusal and failure path
in `dovetail-show` is loud by design; this is the one place a real
failure is swallowed.

**What we already know.** Found by the cross-vendor gate on pull request
#6 (task 0005) as one of two P2 findings; the other was fixed there and
this one was left undispositioned, which is how it earned this entry.
The mechanism: `launch.py` deliberately detaches the spawned terminal
from the caller's pipes (stderr included — inheriting them blocks any
reader until the window closes), and `_report_no_window` — which already
distinguishes "the terminal exited" from "the window never mapped" — is
only reached from the float step's window wait. On the skipped paths
nothing ever checks the child. The fix cannot simply inherit stderr; the
detachment is there for a reason stated in the code.

**Open questions.** What to watch instead of the window tree on these
paths — a short bounded poll of the child's liveness, the same budget
the float step uses, or something cheaper. Whether `--print-socket`'s
existing socket wait already covers enough of this case that the fix is
only for the no-socket invocation. Whether a terminal that dies *after*
mapping its window is in scope, or out.
