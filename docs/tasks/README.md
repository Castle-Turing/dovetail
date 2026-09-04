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

Tidying is worth doing promptly rather than eventually. A harness that
runs this directory as a queue reads the top level and not `done/`, and
decides what has already been built from the branch names its own runs
produced — so a brief that merged by some other route looks like
unstarted work and gets built a second time. Moving a merged brief into
`done/` is what makes it unambiguously finished to a reader that was not
there.
