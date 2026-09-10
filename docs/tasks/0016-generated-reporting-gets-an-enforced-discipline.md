Title: Task 0016 — generated reporting gets an enforced discipline
Milestone: none — hygiene
Model: standard
Model-because: the design below is settled in this file — the report
shape, the four rules, the block unit, the exemption grammar, the gate
and its named evasions are all specified here rather than left to the
implementing agent. What remains is a Python package with a fixture
corpus and two flake-check entries, following four packages already in
`tools/` as templates. The one place judgment is still required is the
exact membership of the completeness-word list and the false-positive
fixtures around it, and this brief names the starting list and the
cases that must be covered. A deep-tier pass would be spending the
frontier on boilerplate that follows mechanically from a written spec.

# 0016 — Generated reporting gets an enforced discipline

## What this promotes

This brief promotes the backlog entry
`docs/backlog/generated-reporting-has-no-enforced-discipline.md`,
deleted in the commit that adds this file. The entry stated the
problem: `docs/state/README.md` carries a reporting discipline for any
generated report that reads `docs/state/`, and nothing in this repo
checks it. There is no generator yet, so there is
also nothing to lint — and the entry named that as the trap rather
than the excuse, because "a stated rule with no mechanical check is
exactly the shape of defect the rule itself warns about: it looks
satisfied until something is built that could violate it silently."

The number was allocated by reading `docs/tasks/`, `docs/tasks/done/`
and the remote branch list at write time. `0015` is allocated to a
concurrent branch (`emcee/0015-a-killed-prompt-leaves-a-record`) that
has not merged; it is not a skipped number.

## What this brief decides, and what it refuses to decide

It decides that the enforcement lands **before** the first generator,
and specifies it: a report format, a lint over that format, a fixture
corpus, a registration gate that fails when an unregistered reader of
`docs/state/` appears, and a citation resolver that is specified here
and deliberately not built yet.

It refuses to decide whether Dovetail should have a generated status
report at all. That was the backlog entry's own open question and it
belongs to the resident. Nothing here obliges anyone to build a
generator; the order matters because the reverse order is the one that
fails. A generator built first arrives with its own habits, and the
discipline then has to be retrofitted onto output somebody is already
reading.

## The prior art, cited as record and not reproduced

Three records stand behind the discipline. None of their text is
reproduced or paraphrased here, and nothing below is derived from
them; everything this brief depends on is restated in full from
`docs/state/README.md`, which is in this tree.

- **Castle Turing's receipts-not-verdicts constraint**, and its task
  0062, which built a claim-checker for that repo's operator handover.
  What this repo already records about it, in the promoted backlog
  entry, is that the checker resolves each citation in a generated
  report against the artifact it claims and fails loudly on a
  mismatch, and that it carries a lint rejecting completion vocabulary
  outside quoted resident verdicts. That entry also records that the
  checker is bound to Castle Turing's own ledgers and is not directly
  portable — a template in shape, not code to copy.
- **Castle Turing's `docs/research/operator-handover.md`**, the full
  research report the discipline came out of. Not in this tree.
- **Mediatron's `AGENTS.md` reporting section.** Named as prior art by
  this task's dispatch. It is not in this checkout and this brief has
  not read it; it is cited as a record, and nothing here is derived
  from it. Whoever implements this may find it states the same
  discipline in different words, which would be corroboration and not
  a new requirement.

## The discipline, restated in full

From `docs/state/README.md`, "How status is reported", binding on any
generated report that reads `docs/state/`:

1. **No completeness claims.** Completion vocabulary — "done,"
   "complete," "finished," "successfully" — is a defect in generated
   reporting outside a directly quoted resident verdict. A derived line
   may report a receipt; it may never assert that the underlying work
   is complete, because completeness is a verdict and only the resident
   renders verdicts.
2. **Every claim carries a citation** naming the artifact it is derived
   from, so the claim is cheaper to check than to re-derive.
3. **Anything ungrounded is marked `[unverified]` in place**, never
   omitted and never smoothed into confident prose.
4. **Threats and drift come before accomplishments.**

## What a checker can enforce

Only the mechanical residue of those four rules, and it is smaller
than the rules are.

- **Rule 1, as a blocklist.** Whether a word from a fixed list appears
  outside an exempt span is decidable. Whether the report claims
  completeness is not — see the review section.
- **Rule 2, as shape.** Whether a block of prose carries a token
  matching the citation grammar is decidable. Whether the cited
  artifact exists and is in the claimed state is decidable *given the
  repo and the network*, which is the resolver below. Whether the
  citation supports the claim is not decidable at all.
- **Rule 3, as the contrapositive of rule 2.** A checker cannot detect
  an ungrounded line; groundedness is not a property of the text. What
  it can enforce is the pair: a block carries a citation, or it carries
  `[unverified]`. Rules 2 and 3 therefore collapse into one mechanical
  rule, and the collapse is the honest form of both.
- **Rule 4, only if the report has a declared shape.** Ordering is
  checkable over named sections and meaningless over free prose. This
  is why the report format below is part of the deliverable rather
  than left to the generator: without it, rule 4 is review-only.

## What only review can enforce

This section is load-bearing. A checker that claims the whole
discipline is the exact failure the discipline exists to prevent, and
the check must not be read as a verdict that a report is honest.

- **Whether a citation supports its claim.** `PR #13` resolving to a
  merged pull request proves the artifact exists in the claimed state.
  It says nothing about whether that pull request establishes the
  sentence attached to it. A report of confident, well-formed,
  irrelevant citations passes every rule below.
- **Omission.** The most dangerous failure is a truthful, fully cited,
  correctly ordered report that leaves out the bad news. A `## Threats`
  section that is honestly formatted and empty because the generator
  never looked is indistinguishable, to a lint, from one that is empty
  because there are none. The lint can require the section to be
  non-empty; it cannot require it to be *complete*, and requiring
  non-emptiness invites a generator to fill it with filler.
- **Synonym drift.** A blocklist is defeated by vocabulary. "Wrapped
  up," "all green," "nothing left," "shipped," "landed cleanly" all
  assert completeness and none is on the list. Extending the list
  chases the failure; it never catches it.
- **`[unverified]` as laundering.** Marking every block `[unverified]`
  passes rule 3 vacuously and produces a report that asserts nothing
  while reading like a status update. The lint reports the count and
  the ratio as a receipt; it must not fail on a threshold, because any
  threshold is invented precision. A reviewer reading "31 of 34 blocks
  unverified" learns something; a checker that failed at 90% would
  teach a generator to sit at 89%.
- **Tone and selection.** Which receipts were chosen, what the report
  leads with inside a correctly ordered section, and whether the prose
  is doing work the citations do not support.
- **Whether the report should exist at all**, and whether its audience
  is served by it.

## The report format enforcement requires

Boring on purpose, and deliberately the same shape as a task file — a
header of `Key: value` lines, a blank line, then a markdown body — so
the repo has one file convention rather than two.

```
Report: <generator name, e.g. dovetail-handover>
Generated: <ISO 8601 timestamp>
Source-revision: <commit sha of the tree whose docs/state/ was read>

## Threats
...

## Drift
...

## <anything else the generator wants>
```

All three header keys are required. `Source-revision:` is the citation
for the report as a whole: "drift from the stated milestone" has no
fixed referent without naming which revision of
`docs/state/MILESTONE.md` was read, and a report that cannot be
re-derived against a named tree is not checkable at all.

## The rules, precisely

**The unit is a block, not a line.** Every document in this repo is
hard-wrapped at roughly 72 columns, so a single claim routinely spans
three lines. A line-based lint would demand a citation on each of them
and would be unusable. A block is a run of consecutive non-blank body
lines forming a paragraph, or a single list item together with its
continuation lines. Rules 2 and 3 bind the block.

- **R1 — vocabulary.** No block outside an exempt span contains, on a
  word boundary and case-insensitively, a word from the list. The
  starting list is exactly the four families
  `docs/state/README.md` names and no more: `complete` (`completed`,
  `completes`, `completion`), `done`, `finished` (`finish`,
  `finishes`), `successful` (`successfully`, `success`). Growing the
  list is a review decision, recorded in the same PR that grows it.
- **R2/R3 — grounding.** Every claim block carries at least one
  citation token or the literal `[unverified]`. A claim block is a
  block of at least four words after list markers are stripped, which
  keeps bare labels and one-word bullets out of scope. The citation
  grammar is closed and small: `PR #<n>`; a hex commit sha of 7 to 40
  characters; `task <nnnn>`; a bracketed clause key such as
  `[m3-done]`; or a repo-relative path with a file extension. A token
  outside this grammar is not a citation, and the error message says
  so rather than guessing at intent.
- **R4 — ordering.** The first two `##` headings in the body are
  `## Threats` and then `## Drift`. Both are required, and each must
  have a non-empty body — the same non-emptiness rule that binds
  `Model-because:` in a task file. Everything after them is the
  generator's business and is not ordered by this rule.

**Exempt spans**, which exist for rule 1's "directly quoted resident
verdict" clause and for quoted artifact text:

- A markdown blockquote whose first line carries a `[stated
  YYYY-MM-DD]` provenance mark. This reuses `docs/state/README.md`'s
  existing provenance vocabulary rather than inventing a second marker
  for the same idea, and it makes the exemption cost something: a
  generator claiming the exemption must name a date and a source.
- A fenced code block, which is also excluded from being a claim block.
  This is a known evasion — a generator that wraps its prose in a fence
  passes R1 and R2 by disappearing — and it is stated here rather than
  closed, because closing it would mean lint-checking quoted command
  output, which is worse. Review catches it; the lint's own output
  reports how many blocks were skipped as fenced, so a report that is
  mostly fence is visible in the receipt.

**Output.** One `path:line: rule: message` per violation, non-zero
exit if any. On success, a receipt: blocks checked, citations by kind,
`[unverified]` count and ratio, fenced blocks skipped.

## The checker states its own limits

The lint always prints, on success and on failure alike, the list of
things it did not check — the six items under "What only review can
enforce", in one short line each. Not a footnote in the documentation:
the program's own output, every run.

The reason is that the discipline binds this program too. A green
check is a receipt ("R1 through R4 hold over this file"), not a
verdict ("this report is honest"), and a checker that prints only a
green tick asserts the verdict it is not entitled to. The tool obeys
the rule it enforces or nobody should believe either.

## The registration gate — the detector

The gate answers the backlog entry's actual trap: not a bad report,
but a generator that quietly never runs the lint.

A second flake check scans the source tree for readers of
`docs/state/` — the literal string in any file under `tools/` — and
fails unless every file that matches is listed in an allowlist
committed beside the check, each entry carrying one line of why.
Today the allowlist is empty and the scan finds nothing, and the check
asserts both. The day someone adds a generator, the build fails and
the author has to open the allowlist, read the discipline, and say in
writing that their generator runs the lint. The forcing function is a
human sentence, which is the most a check can honestly ask for here.

The gate must be a pure function over a list of file contents so that
its own tests can feed it a synthetic tree, rather than mutating the
real one to test the failure path.

Its evasions, stated rather than papered over: a generator that builds
the path dynamically, one that lives outside `tools/`, and one that
lives in another repository and reads a clone of this one. The gate
catches the careless case, which is the common one. It does not catch
an author working around it, and it is not a security boundary.

## The resolver, specified and deferred

Resolving a citation against the artifact it names — that `PR #13` is
merged, that a sha exists, that a path exists at the named revision —
requires the git repository and, for pull requests, the network.
`nix flake check` runs in a sandbox with neither: no `.git`, no
`gh`, no network. A resolver cannot be a flake check, and pretending
otherwise would produce a check that passes because it could not look.

So the split is structural and permanent, not a staging convenience:

- **The lint** is pure and offline. It takes report text and returns
  violations. It runs in `nix flake check` over the fixture corpus,
  and anyone can run it on a real report.
- **The resolver** needs the repo and the network. It is specified
  here and **not built by this task**, because there is no generator
  whose output it would resolve. When the first generator is proposed,
  building the resolver is part of that task, and the generator runs
  it before emitting — the lint checks that citations are well-formed,
  the resolver checks that they are true, and only the generator's own
  task can wire the second one in.

Whoever builds it should expect it to be new code against Dovetail's
ledgers (git, `gh`, `docs/tasks/`) rather than a port: the backlog
entry already records that Castle Turing's is bound to Castle Turing's
ledgers.

## Naming

The package is `dovetail-report-lint`, plainly descriptive. Three
reasons. The verbs in this repo (`show`, `run`, `scriptorium`) are
things the resident invokes; this is a check that runs in a build, a
small piece, and `AGENTS.md` reserves the Diamond Age well for
load-bearing components rather than spending it here. "Report" is
already the word `docs/state/README.md` uses for the artifact, so
reusing it is consistency rather than collision. And a Diamond Age
name for a linter could collide with a load-bearing name elsewhere in
the ecosystem, which this checkout cannot check.

Names are cheap to change now and expensive later; if review prefers a
metaphor, rename before merge.

## What is deliberately left out

- **A generator.** See "what this brief refuses to decide."
- **The resolver.** See above; the reason is structural.
- **A threshold on the `[unverified]` ratio.** Reported, never
  enforced. Any number would be invented precision and would teach a
  generator to sit just under it.
- **Any change to `docs/state/README.md`'s discipline itself.** The
  four rules are adopted, not amended. This task builds a check for
  the part of them that is checkable; it does not narrow the rules to
  the part that is checkable, and the review section exists to keep
  that distinction visible.
- **A `docs/state/` document for the report registry.** Adding a
  document there is a deliberate act and only the resident closes that
  question. The allowlist lives with the check that reads it.
- **CI beyond `nix flake check`.** The repo has one check workflow and
  this rides it.

## Judgment calls recorded

The dispatch granted autonomy for this brief and asked that every
judgment call be recorded rather than silently made.

1. **This brief lands without its implementation.** `AGENTS.md` says a
   brief "is committed on the branch that implements it, never
   separately." The dispatch for this task asked for the brief alone,
   and this is a spec task in a sprint whose implementation is a later
   run. The deviation is stated here rather than glossed: whoever
   implements this updates this file in the same PR if the design
   shifts, which is the part of the rule that still applies.
2. **`Milestone: none — hygiene`, under protest.** This is repo
   mechanism, not tidying, and `none — repository mechanism` — the
   phrase that fits it exactly — was retired by the resident's
   2026-09-08 ruling. The two surviving values are a clause key from
   `docs/state/MILESTONE.md` (there is none for reporting discipline)
   and `none — hygiene`. Task 0014 took the same value for the same
   kind of work, so precedent decides it here; the vocabulary gap is
   flagged for the resident rather than closed by inventing a third
   value.
3. **The report format is specified in this brief.** Rule 4 is not
   enforceable without a declared section structure, so a checker for
   the discipline necessarily fixes part of the report's shape. Only
   the minimum is fixed: three header keys and the first two headings.
   What a report *contains* is left to whoever builds one.
4. **The block, not the line, is the unit.** Forced by hard-wrapped
   markdown. A line-based rule would be unusable in this repo and
   would be worked around immediately.
5. **The exemption reuses `[stated YYYY-MM-DD]`** rather than a new
   marker, so the repo has one provenance vocabulary.
6. **Fenced blocks are exempt and the evasion is stated.** The
   alternative — linting quoted command output for the word "done" —
   is worse than the hole.
7. **`docs/state/README.md` gets a one-sentence patch in this PR**,
   under the same-PR rule, recording that the enforcement is now
   specified and not yet built. `docs/state/MILESTONE.md` is not
   patched: `[m3-now]` tracks the M3 queue, and work carrying `none —
   hygiene` serves no clause there. Task 0014 appears in that section
   because the state layer itself was landing in that PR, which is not
   the case here.
8. **Prior art is cited without being read.** Mediatron's `AGENTS.md`
   is not in this checkout. Rather than paraphrase a document this
   brief has not seen, it is named as a record and the discipline is
   restated from the in-tree source. This is the same move the
   discipline asks a report to make.
9. **The detector convention is satisfied even though it did not
   bind.** "An incident ships its detector" binds a backlog entry
   filed from a regression, outage, or silent failure; the promoted
   entry is preventive and predates the convention's adoption, so no
   incident section was owed. The registration gate is the detector
   regardless, and the "what only review can enforce" section is the
   statement of what no check will catch.

## Verification

**What an agent can verify with no human.**

- `nix flake check` passes with two new entries: the lint package,
  whose unit tests run in its own check phase (the pattern the other
  four packages already use, so the check is the package), and the
  registration gate.
- The fixture corpus, committed under the lint package's tests: for
  each of R1, R2/R3 and R4, at least one report that must pass and one
  that must fail, with the expected violation asserted by rule name
  and line, not merely by exit status.
- The false-positive fixtures specifically, because these are where a
  careless implementation breaks: a blockquote carrying `[stated
  2026-09-08]` and the word "complete", which must pass; the same
  blockquote without the provenance mark, which must fail; a fenced
  block containing every word on the list, which must pass; a claim
  spanning three hard-wrapped lines with its citation on the last,
  which must pass; a three-line block with no citation and no
  `[unverified]`, which must fail once, not three times.
- The header rules: each of the three required keys missing, in turn.
- The block unit under list items, including a bullet whose
  continuation lines carry the citation.
- The gate's own tests, over a synthetic file list: a match with no
  allowlist entry fails, a match with one passes, the empty tree
  passes.
- An example report, committed as documentation and linted by the test
  suite, proving the format is writable by hand and that the rules do
  not contradict each other in practice.
- The self-limitation output appears on both a passing and a failing
  run — asserted in a test, since it is a requirement and not a
  courtesy.

**What needs human hands.**

- Whether the completeness-word list is the right list, and whether
  four families is too few. No test can answer this; a blocklist's
  adequacy is not a property a fixture can assert.
- Whether the citation grammar covers what a real Dovetail report
  would cite, which is only knowable once a generator is proposed.
- Confirming the report format before it is baked in: three header
  keys and the ordering of the first two sections are cheap to change
  now.
- The `Milestone:` vocabulary gap in judgment call 2.
- The naming question, if review prefers a metaphor to
  `dovetail-report-lint`.
- The backlog entry's original open question, which this brief
  deliberately leaves open: whether Dovetail wants a generated status
  report at all.

**What no verification reaches, in this task or any later one.** The
fixture corpus proves the lint behaves as specified. It does not prove
that a report which passes the lint is honest, and today the check
runs over fixtures and zero real reports — which is not the same thing
as the discipline being enforced. That gap is the point of the review
section above, and stating it here rather than reporting a green check
is the discipline applied to this brief.
