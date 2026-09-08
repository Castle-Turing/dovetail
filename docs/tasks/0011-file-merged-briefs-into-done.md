Title: File merged briefs into done
Milestone: none — hygiene

# 0011 — File merged briefs into done

Tidying, per `docs/tasks/README.md`: a merged brief is moved to
`docs/tasks/done/` promptly, so a harness reading the top level as a
queue sees it as unambiguously finished.

Both of these merged into `main` (pull requests #9 and #8
respectively; the merge commits are on `main`, no judgment needed):

```
git mv docs/tasks/0006-scriptorium.md docs/tasks/done/
git mv docs/tasks/0007-launch-failures-are-loud-on-every-path.md docs/tasks/done/
```

Nothing else in the diff: no content changes to either file, no other
files touched, no renumbering.

## Verification plan

Agent-testable, no human involved: `git diff --stat` against the base
shows exactly two renames and this brief; `git status` clean after
committing.

Genuinely needs human hands: nothing.
