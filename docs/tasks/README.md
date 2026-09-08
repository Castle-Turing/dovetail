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
queue. Keep every harness-read key (`Title:`, `Model:`, `Requires:`,
`Milestone:`) *above* any header value that wraps onto a continuation
line — a parser that stops reading headers at the first wrapped line
will silently treat a key below one as absent (a review finding in the
Castle Turing repo this convention is adopted from).

## The `Milestone:` header

`Milestone:` names a clause key from `docs/state/MILESTONE.md` (see
`docs/state/README.md`), or the explicit value `none — hygiene` for a
task that serves nothing there — adopted from Castle Turing task 0061.
A task derived from a state clause cites its key (e.g. `m3-done`) so a
clause revision identifies exactly which queued tasks it invalidates.

**Ruled by the resident, 2026-09-08:** this is the single form. Task
files had already been using a `Milestone:` header since task 0001,
with values that were a bare roadmap-milestone name from
`docs/vision.md` (`M1`, `M2`, `M3`) or the explicit phrase `none —
repository mechanism` (task 0004) — that form is now retired, and the
tracked queue was retrofitted to the clause-key form in the same PR
that made this ruling (task 0014), except for two files flagged there
rather than forced (0006, 0007 — see that brief). Six files still carry
a retired value and were deliberately left untouched, since their
values are the resident's to assign, not a migration's to overwrite:
0001, 0002, 0005, 0006 and 0007 carry the retired roadmap-name form,
and 0004 carries the retired `none —` phrase. A reader meeting one of
these in `done/` or in history should read it as the pre-2026-09-08
convention, not the current one.

Numbers are allocated by checking this directory at write time —
**including `done/`**. The sequence never restarts and a number is never
reused: an archived brief is still the brief that owns its number, and
after a sweep the top level can be empty of numbered files while `0001`
and `0003` sit in `done/`. An allocator that reads only the top level
would hand out `0001` again and collide with a merged piece of work.

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
