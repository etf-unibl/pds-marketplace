---
name: fix
description: Help the student fix git mistakes in the PDS workflow - wrong branch, files outside assignments/<N>/ in a commit, wrong or unsigned commit messages, undoing a commit, recovering lost work. Use when a hook or the pr-checks job rejects commits, or the student says something went wrong in git.
---

# Fixing mistakes

{{include teach-rule}}

{{include course-context}}

Always start with `repo_state` and `branch_check` (and `git log --oneline -5`, read-only) to see the real situation, and say what you see before proposing anything. Prefer the safest fix; warn before any command that discards work, and mention `git reflog` as the safety net.

| Situation | Commands to show and explain |
| ------ | ------ |
| Changes made on the wrong branch, not committed | `git stash`, `git switch <right-branch>`, `git stash pop` |
| A file outside `assignments/<N>/` is staged | `git restore --staged <file>` |
| Last commit (not pushed) has a wrong message or no sign-off | `git commit --amend -s` (fix the message in the editor) |
| Several commits (not pushed) need fixing | `git reset --soft origin/assignments`, then one new commit with `git commit -s`; or `git rebase -i` only for experienced students |
| Commits already pushed need a new message or sign-off | rewrite as above, then `git push --force-with-lease`; explain why plain `--force` is dangerous and that the pull request updates itself |
| A commit changed files outside the folder | `git revert <sha>` (pushed) or `git reset --soft HEAD~1` and re-stage only `assignments/<N>/` (not pushed) |
| Work seems lost after reset or rebase | `git reflog`, then `git switch -c rescue <sha>` |
| Branch name does not start with `<N>-` | `git branch -m <N>-<name>`; if pushed, push the new name and open the pull request from it |

After each step the student runs, check again with `repo_state` and `branch_check`. Explain the cause, so the mistake is not repeated (e.g. hooks not enabled).
