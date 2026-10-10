---
name: submit
description: Prepare the submission of a PDS task - pre-submission checklist (local checks like CI), pull request title and description following the course template, and the commands to push and open the pull request. Use when the student wants to submit or open a pull request.
---

# Submitting a task

{{include teach-rule}}

{{include course-context}}

## Steps

1. **State**: `repo_state` - the branch must start with the issue number, nothing outside `assignments/<N>/` may be staged or committed, no merge or rebase may be in progress. `branch_check` (with the issue title from `task_context`) checks every commit like the `pr-checks` job.
2. **Local checks**, the same as CI (use the tools, and show the commands):
   - style: `style_report <N>` (`vhdl-style <N>`);
   - testbenches: `run_testbenches assignments/<N>` (GHDL, VHDL-2008, like the `testbench` job);
   - test assignment: `vhdl_analyze assignments/<N>/test.vhd`;
   - documentation (graded, not checked by CI; `docs/design-documentation.md`): every design file has the Doxygen comments the guide requires and no TODO placeholder is left. With the pds-docs plugin, its `review` skill checks it (`docs_check`); otherwise point the student to the guide.
   Fix what fails before submitting (explain, do not edit the student's files).
   - AI attribution (course rule): if an AI tool generated code in the solution, every commit containing such code must have an `AI-assisted-by: <tool> - <how it was used>` line (`docs/assignment-submission.md`, "Korišćenje AI alata" / "Using AI tools"). Ask the student; a missing line is fixed by rewording the commit (the `fix` skill of pds-git explains `git commit --amend` / `git rebase -i` and the force push it needs).
3. **Push**: show `git push -u origin <branch>` and explain `-u` (first push of the branch).
4. **Pull request**: give the student the exact title (`Issue #<N> : <issue title>`) and explain how to open the pull request to `assignments` (web: **Compare & pull request**, base `assignments`; or `gh pr create --base assignments`, which they run themselves). The description follows the template that GitHub fills in: write a draft of the summary section (`<!-- section:summary -->`) from the student's own explanation of their solution, and remind them to tick every check item only when it is true. The changes section is filled in by CI from the commit messages.
5. **After opening**: `pr_status` shows the rule checks and the CI results; if something fails, use the `checks` skill.

See `docs/assignment-submission.md` and `docs/automated-checks.md` (`course_doc`).
