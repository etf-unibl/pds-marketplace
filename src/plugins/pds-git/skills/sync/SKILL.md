---
name: sync
description: Explain pushing, pulling and bringing in the newest assignments branch in the PDS course, and guide the student through merge conflicts. Use when the student wants to push, update their branch, or has a merge conflict.
---

# Push, update, conflicts

{{include teach-rule}}

{{include course-context}}

## Push

- First push of a branch: `git push -u origin <branch>`; later just `git push`. Explain that `-u` links the local branch with `origin/<branch>`.
- `repo_state` shows `ahead`/`behind`. If the push is rejected because the remote has new commits (e.g. edited on the web or by a team member), show `git pull` and explain that it is fetch + merge.

## Bringing in the newest `assignments`

When the instructor adds something to `assignments` (e.g. new tests or workflow fixes), the student merges it into the task branch:

```
git fetch origin
git merge origin/assignments
```

Explain merge vs rebase: the course uses merge (no rewritten history, no force push). Merge commits are not checked for the message format.

## Merge conflicts

1. `repo_state` shows `merge_in_progress` and the conflicting files (unmerged paths in `git status`).
2. Explain the conflict markers (`<<<<<<<`, `=======`, `>>>>>>>`): ours (the task branch) and theirs (the merged branch). Read the file with the student and explain what each side contains; the student decides and edits the file (you do not edit files in `assignments/`).
3. Then `git add <file>` for each resolved file and `git commit` (the merge commit message is prepared by git). To give up: `git merge --abort`.
4. Check with `repo_state` and, for VHDL, `vhdl_analyze` on the resolved files.
