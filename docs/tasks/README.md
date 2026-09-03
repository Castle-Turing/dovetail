# docs/tasks — numbered briefs

One numbered brief (`0001-`, `0002-`, …) per piece of implementation
work: the spec, the reasoning, what was considered and rejected, and a
verification plan. A brief is committed on the branch that implements
it, never separately — spec and implementation merge and get audited
together. If the design shifts during implementation, the same PR
updates the brief; a brief confidently describing an abandoned design
is worse than none.

Format: a header of `Key: value` lines (`Title:` at minimum), a blank
line, then a markdown body that becomes the working agent's prompt —
boring on purpose, so any harness that reads files can consume the
queue. Numbers are allocated by checking this directory at write time.

This directory is the log a future agent reads cold to learn why the
code is shaped the way it is; git history records only what changed.
Move a merged task's file to `done/` when tidying.
