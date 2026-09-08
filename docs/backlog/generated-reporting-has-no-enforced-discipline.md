# Generated reporting has no enforced discipline

**What.** `docs/state/README.md` states a reporting discipline for any
generated report that reads `docs/state/` — no completeness
vocabulary, every claim cited, ungrounded lines marked `[unverified]`,
threats and drift before accomplishments — adopted from Castle
Turing's operator-handover research and its task 0062. Nothing in this
repo checks it. There is no generator yet that reads `docs/state/`, so
there is also nothing to lint.

**Why it matters.** The discipline exists because fluent, uncited
summaries read as more trustworthy than they are, and self-reported
completion is measured false in a large fraction of cases with no
reliable detector. A stated rule with no mechanical check is exactly
the shape of defect the rule itself warns about: it looks satisfied
until something is built that could violate it silently.

**What we already know.** Castle Turing task 0062 built a claim-checker
for its own operator handover — it resolves each citation in a
generated report against the artifact it claims (a merged PR, green
checks, a resolved review finding) and fails loudly on a mismatch, plus
a lint that rejects completion vocabulary outside quoted resident
verdicts. That checker is specific to Castle Turing's ledgers (`gh`,
the journal, review dispositions) and is not directly portable, but its
shape is a template.

**Open questions.** Whether Dovetail needs a generated status report at
all before this matters, or whether the discipline stays dormant until
one is proposed. If one is proposed, whether its claim-checker should
be built new against Dovetail's own ledgers (git, `gh`, `docs/tasks/`)
or adapted from Castle Turing's.
