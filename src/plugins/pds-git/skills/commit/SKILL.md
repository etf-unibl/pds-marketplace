---
name: commit
description: Help the student make a commit in the PDS course format - stage only assignments/<N>/, draft the message (Issue #<N> : <title>, empty line, "- " items) from the staged changes, check it, and explain git commit -s. Use when the student wants to commit or asks about the commit message format.
---

# Committing

{{include teach-rule}}

{{include course-context}}

## Steps

1. `repo_state`: branch, issue, staged and unstaged files, files outside `assignments/<N>/`.
2. **Staging**: if needed, show `git add assignments/<N>/<file>` (by path; explain why not `git add .` in the repository root) and how to unstage (`git restore --staged <file>`). Look at the changes with `git diff --staged` (read-only; you may run it to describe them).
3. **Message**: get the exact issue title (`task_context`) and draft:

```
Issue #<N> : <issue title>

- <what changed, from the staged diff>
- <...>
```

   Base the items on the actual diff and on what the student says they did; keep them short and factual. Check the draft with `commit_check` (it also checks the sign-off against the git identity).
4. **Command**: show `git commit -s` and explain:
   - `-s` adds `Signed-off-by: <name> <e-mail>` from the git configuration (required by CI);
   - with the hooks enabled, `git commit -s` opens the editor with the pre-filled first line; the student pastes or writes the items;
   - for a one-line terminal command they can use `git commit -s -m "Issue #<N> : <title>" -m "- item one" -m "- item two"` (each `-m` is a paragraph, so the first gives the subject and the empty line).
5. If the hook rejects the commit, read its message with the student; the message file is kept, so they fix it and commit again.
6. After the commit: `repo_state` and `branch_check` (the format and sign-off of all commits of the branch).
