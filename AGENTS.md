# Dovetail — operator contract

You are working in the public Dovetail repo, part of the Castle Turing
ecosystem. Read `docs/vision.md` once per session if you haven't; it is
the founding context, and nothing in it is yet a binding commitment —
positions there hold until implementation confirms or overturns them,
and the same PR that overturns one amends the document.

This file is the operator contract, written harness-neutral: it applies
to any agent (or person at a shell) working in this checkout. A rule
that only works in one harness must say so. Operator-personal
preferences — authority levels, budgets, machine paths — live in the
operator's own profile, never here.

## Hard rules

- **Never write personal data into this repo.** No credentials, real
  names of third parties, machine-specific paths, or any artifact of a
  resident's private layer — not in code, docs, test fixtures, or
  commit messages. Placeholder paths (`/home/resident/...`) exist so
  nobody has to invent one.
- **Public mechanism, private configuration** (Castle Turing Design
  Principle 01) on every change: taste — colorschemes, keymaps,
  typefaces, scratch locations — belongs in a documented private-layer
  slot, never hardcoded. If a feature can't split that way, the design
  is not done; say so rather than merging it.
- **Tooling calls Dovetail's verbs, never the editor by name.** Once
  the provider slot exists, a tool that shells out to `nvim` directly
  is a design smell (vision, starting position 4).
- **Docs are written for strangers**: a reader who is not us, on
  hardware that is not ours, who may be implementing a provider for an
  editor we do not use.

## Session discipline

- **Start every session on a freshly pulled `main`:**
  `git fetch --all --prune && git checkout main && git pull --ff-only`,
  before reading anything else — conventions and task numbering are
  exactly as stale as the checked-out branch.
- Parallel sessions use git worktrees, one branch per session, under
  `.claude/worktrees/<branch>` inside this repo — never as siblings in
  the projects directory. Sweep a worktree when its branch merges,
  after verifying both that it merged and that the tree is clean.
- No direct commits to `main`; merges go through PRs so review can
  happen there. Opening a PR is the normal end of a unit of work.
- Scope every review and diff against `origin/main`, never a local
  branch ref: `git fetch` first, then confirm scope with
  `git diff origin/main...HEAD --stat`.
- Never force-push, delete remote branches, or rewrite published
  history — work around instead (fresh branch plus cherry-pick, a
  reland branch, a revert commit).

## The work record

Deferred work, implementation briefs, and research live in the tree,
readable by anything that can read files — no issue tracker, no
external pages:

- `docs/state/` — current truth, maintained and patched in the same PR
  that changes it; everything else under `docs/` is record. Deriving
  work cites `docs/state/MILESTONE.md`'s clause keys — see
  `docs/state/README.md`, adopted from Castle Turing task 0061.
- `docs/backlog/` — one plain-text file per deferred item, named as a
  statement of the problem, slugs not numbers. See its README for the
  entry shape and lifecycle.
- **An incident ships its detector.** A backlog entry filed from a
  regression, outage, or silent failure answers, in its own section,
  how it would have been caught sooner; the brief that fixes it
  either lands that detector as an automated check or states why
  none is mechanically possible. Blank is not an answer — the same
  non-emptiness rule that binds `Model-because:`. A silent failure
  looks like a quiet day; only a check outlives the memory of the
  incident. (Resident-adopted 2026-09-08, ecosystem-wide, from the
  review-pipeline regression a human question caught and no
  automated check did.)
- `docs/tasks/` — numbered briefs (`0001-`, `0002-`, …), each the spec
  and reasoning for one piece of implementation work. **Every piece of
  implementation work gets a brief, however small** — proportionality
  decides its length, never whether it exists. A brief is committed on
  the branch that implements it; if the design shifts during
  implementation, the same PR updates the brief. Numbers are allocated
  by checking the directory at write time, never from a stale listing.
  Speccing a backlog entry promotes it to a brief and deletes the
  backlog file in the same commit. Move a merged task's file to
  `docs/tasks/done/` when tidying.
- **Task file format** (so any harness can consume the queue): a
  header of `Key: value` lines (`Title:` at minimum), a blank line,
  then a markdown body that becomes the working agent's brief. Boring
  on purpose. `Milestone:` is one such key — see `docs/tasks/README.md`
  for its two, not-yet-reconciled meanings.
- `docs/research/` — full point-in-time research reports, one file per
  report; see its README for how they relate to the backlog.

Every brief states its verification plan: what the implementing agent
can test with no human involved, and which steps genuinely need human
hands.

## Ask before acting

- Clarifying questions belong to the human; no agent invents an answer
  the spec workflow says to ask for.
- Ask for explicit approval before writing a brief to disk, unless the
  human granted autonomy for that task — then proceed and record every
  judgment call that would otherwise have been a question.
- A change to this file or to `CLAUDE.md` always needs explicit
  approval, autonomy grant or not.

## Naming

Prefer names from *The Diamond Age* for projects and load-bearing
components; plain castle metaphors are fine for smaller pieces — the
Diamond Age well is not spent on minor things. Name collisions are
defects, not style preferences: a word already load-bearing in the
ecosystem (journal, record, seat, resident, worker) is not reused to
mean something else here.

## Why this file is `AGENTS.md`

Codex and OpenCode read `AGENTS.md` natively; Claude Code reads
`CLAUDE.md`, so the committed `CLAUDE.md` here is a thin pointer that
imports this file (the pattern verified against each harness's
documentation in the emcee repo, 2026-09-02). Edit this file, not that
one.
