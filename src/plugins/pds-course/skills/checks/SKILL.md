---
name: checks
description: Explain failed automated checks of a PDS pull request (classify, pr-checks, linter, basic-test, testbench, verif) and how to fix them locally. Use when a check on the pull request is red or the student asks why CI failed.
---

# Failed checks

{{include teach-rule}}

{{include course-context}}

## Steps

1. `pr_status` (current branch or pull request number). It returns the course rule checks (`rule_checks`, the same as the `pr-checks` job) and the latest result of every CI job with the error annotations of failed jobs.
2. For each failed job, explain the cause and the fix:

| Job | Typical cause | Local check and fix |
| ------ | ------ | ------ |
| `classify` | title without the number of an existing issue, issue without a topic label | fix the title (`Issue #<N> : <title>`); a missing label is for the instructor |
| `pr-checks` | title, branch name, assignee, files outside `assignments/<N>/`, unsigned commit, commit format, unticked template item | `branch_check`, `repo_state`; rewording commits is explained in the `pds-git` plugin (skill `fix`) |
| `linter` | style violations or VHDL-2008 errors (`[VHDLVersion]`) | `style_report <N>`; explain each rule; `vhdl-style --fix <N>` is run by the student |
| `basic-test` | `test.vhd` missing or does not compile | `vhdl_analyze assignments/<N>/test.vhd` |
| `testbench` | testbench does not compile, entity not named like the file, `assert ... severity error` fired, no `wait;` (stopped after 10 ms) | `run_testbenches assignments/<N>` |
| `verif` | instructor tests: wrong file, entity or port names, or wrong behaviour | compare names with the issue text; simulate own testbench; results are in the `verif-artifacts` artifact |

3. Remind the student that the checks run again after every push and after editing the title or description, and that a job stuck in *Queued* for long should be reported to the instructor rather than re-run repeatedly.

See `docs/automated-checks.md` (`course_doc automated-checks`).
