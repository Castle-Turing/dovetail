# docs/state — what is true now

The documents in this directory are the repo's current truth:
maintained, authoritative, and safe to build on. Everything else under
`docs/` — task briefs, backlog entries, research reports — is
**record**: what was decided, found, or considered, and when. The
split exists because the two kinds age differently: a record is
finished the day it lands and only gains value by staying exactly as
written, while current truth is only worth reading if something keeps
it current.

This convention is adopted from Castle Turing task 0061 ("a
current-state layer, and the milestone document as its first page"),
which built the same split for the framework repo and did the reading
behind it; nothing here re-derives that argument. The evidence is
Castle Turing's `docs/research/inter-task-handoff.md` and
`docs/research/elicitation-papers.md`, and — for the reporting
discipline below — `docs/research/operator-handover.md`, all three
full research reports, not reproduced here.

## The rules

1. **Authority is a link; history is a name.** When work needs a
   *current* fact, it links into this directory. When it cites how a
   decision was reached, it names the record ("task 0009") and never
   links a path — records move to `done/`, and a path citation rots the
   day that happens. When later work finds itself citing a brief *as
   authority*, that is the signal to extract the load-bearing content
   into this directory in the same PR.
2. **The same-PR patch.** A pull request that changes what is true —
   completes milestone work, makes a design decision, retires a
   constraint — updates this directory in the same PR, and the
   reviewer reads the state diff as part of the review. A deletion here
   gets explicit review attention: premature deletion is the measured
   dominant failure of machine-maintained state.
3. **Deriving work cites clauses.** Documents here carry bracketed
   clause keys (`[m3-intent]`). A task derived from a clause cites its
   key, so a revision to the clause identifies exactly the tasks it
   invalidates. A task file's `Milestone:` header carries the citation —
   see `docs/tasks/README.md` for the header's form, ruled by the
   resident 2026-09-08.
4. **Deliberate accommodation.** Adding a document or a top-level
   section here is a deliberate act, recorded with one line of why in
   the PR that does it. Automatic schema induction is explicitly out of
   scope: an agent that repeatedly finds content with no slot may
   *propose* one, citing the recurring instances — only the resident
   closes that question.

## The public/private line, drawn explicitly

AGENTS.md's hard rules already ban personal data and resident-specific
defaults from this repo, and a milestone document is exactly the kind
of file that could drift across that line, so it is worth stating
explicitly rather than assumed: what belongs here is Dovetail's own
direction as a public framework component — what the project is
building next, which is mechanism anyone independently adopting
Dovetail inherits and every worker must read. What must never appear
here is the resident's private layer — editor cosmetics, keymap taste,
scratch-directory locations, credentials, or anything AGENTS.md already
reserves for a private-layer slot. The test for a milestone clause is
the same as for any file here: would this sentence be true and
appropriate for a stranger's independent deployment of Dovetail to
contain about *its* development? "The editor contract gets extracted
from what M1 and M2 actually called" passes; anything about the
resident's own editor setup or working habits does not.

## How state documents are written

Small structured prose — headings and clause keys, never an invented
schema language. Constraints that bind carry four fields in prose:
what must hold (prerequisite), who may waive it (authority), what to
do when it cannot hold (fallback), and what breaks when violated
(consequence). Constraint language is explicit, never hedged. Clauses
distinguish `[stated <date>]` — the resident's own words, naming where
they were said — from `[inferred]` — the system's reading, held until
confirmed or corrected, naming the basis for the inference. An
unresolved ambiguity is tagged in place, cleared only by a cited
answer, and never resolved by silent choice.

## How status is reported

Any generated report that reads this directory — a handover, a
digest, a summary posted somewhere the resident will read it — carries
the same discipline Castle Turing's operator-handover research
(`docs/research/operator-handover.md`, and task 0062 which built the
generator against it) established for that repo, adopted here without
re-deriving it:

- **No completeness claims.** Completion vocabulary — "done,"
  "complete," "finished," "successfully" — is a defect in generated
  reporting outside a directly quoted resident verdict. A derived line
  may report a receipt ("PR #13 merged, checks green"); it may never
  assert that the underlying work is complete, because completeness is
  a verdict and only the resident renders verdicts.
- **Every claim carries a citation.** A line in a generated report
  names the artifact it is derived from — a PR number, a commit, a
  file path with a state — so the claim is cheaper to check than to
  re-derive.
- **Anything ungrounded is marked `[unverified]` in place**, never
  omitted and never smoothed into confident prose.
- **Threats and drift come before accomplishments.** What could go
  wrong next, and what has drifted from the stated milestone, lead the
  report; a status surface that opens with a victory list is the
  failure mode this ordering exists to prevent.

This repo has no generator yet that reads `docs/state/` — the rule is
recorded here so the first one that gets built is built against it,
rather than the discipline being re-derived, or skipped, later.
