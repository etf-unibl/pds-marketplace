---
name: start
description: Guide the student through starting work on a PDS issue with git - fetch, create the task branch from origin/assignments with the issue number, create the assignments/<N> folder. Use when the student starts a new task or asks how to create a branch.
---

# Starting a task

{{include teach-rule}}

{{include course-context}}

## Steps

1. `repo_state`: check that the student is in the course repository, that there are no uncommitted changes they could lose, and whether the hooks are enabled (if not, show `git config core.hooksPath .githooks` first).
2. Show and explain, one command at a time, waiting for the student to run each:

```
git fetch origin
git switch -c <N>-<short-name> origin/assignments
```

   - `fetch` downloads the newest `assignments` without changing their files;
   - `switch -c` creates the branch from `origin/assignments` and moves to it; the name must start with `<N>-` (the CI checks it); `git checkout -b <name> origin/assignments` is the older equivalent.
3. Check with `repo_state` that the branch and the issue number are right.
4. The work goes into `assignments/<N>/` only; the pre-commit hook rejects anything else. The first commit is explained in the `commit` skill.

If the student already made changes on the wrong branch, use the `fix` skill instead.
