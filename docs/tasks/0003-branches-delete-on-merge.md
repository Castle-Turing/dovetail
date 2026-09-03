Title: Branches delete on merge

# 0003 — Branches delete on merge

Merged pull-request head branches lingered on the remote: task 0001's
`emcee/0001-flake-and-nixvim-module` branch survived its own merge and
had to be noticed and deleted by hand. The operator wants merged
branches gone automatically (decided 2026-09-03).

**Numbering.** This brief takes 0003 and deliberately skips 0002.
Merged prose — `docs/vision.md` and brief 0001 — refers to "task 0002,
the `show` verb" in four places, and reallocating an entrenched forward
reference to a housekeeping change would be exactly the name-collision
defect the operator contract calls out. 0002 stays reserved for the
`show` verb; this note is what keeps the gap readable as intent rather
than error.

**The change.** The repository's `delete_branch_on_merge` setting on
GitHub is enabled, so the forge deletes a PR's head branch the moment
the PR merges — for branches hosted in this repository. A PR from a
fork is outside the setting's reach: the head branch lives in the fork,
and its owner remains responsible for it. Closing a PR *without*
merging leaves its branch alone either way, which is the direction the
harness relies on: an unmerged branch may be the only copy of real
work. The setting is forge configuration and
lives outside the tree; this brief is its in-tree record, per the
convention that the work record is readable by anything that can read
files. Anyone forking this repo onto other infrastructure re-applies
the intent, not the mechanism. The one branch that predated the
setting, `origin/emcee/0001-flake-and-nixvim-module`, was deleted by
hand with explicit operator approval the same day.

**Considered and rejected.** A CI workflow that deletes branches after
merge: reimplements a forge feature, adds a token with delete
authority, and runs code where a checkbox suffices. Leaving manual
deletion as the norm: remote-branch deletion is deliberately outside
agents' standing authority here, so the manual path funnels routine
cleanup through operator approval forever.

## Verification plan

Agent-testable, no human involved:

- `gh api repos/Castle-Turing/dovetail --jq .delete_branch_on_merge`
  returns `true`.

Needs human hands:

- Merging this PR — its own head branch disappearing afterwards is the
  live end-to-end test of the setting.
