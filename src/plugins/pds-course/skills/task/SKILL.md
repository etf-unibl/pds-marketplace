---
name: task
description: Explain a PDS course task (GitHub issue) to the student - what to submit, in which folder, on which branch, with which commit and pull request title, the deadline and the matching guides and topic pages. Use when the student asks what an issue requires or how to start it.
---

# Task context

{{include teach-rule}}

{{include course-context}}

## Steps

1. Get the issue: `task_context` with the issue number (or without it, for the issue of the current branch). It returns the title, kind (`test` = test assignment, `graded` = graded assignment of group `assignment-N`), assignees, deadline (`due_on`), the folder, the branch prefix and the exact commit and pull request title.
2. Summarize for the student:
   - what the issue asks (read `body`; quote the requirements, do not invent new ones);
   - the folder `assignments/<N>/` and the required file and entity names; the instructor's tests expect exactly these names, so wrong names fail `verif` even for a correct design;
   - for the test assignment: `test.vhd` with entity `test` (see `course_doc test-assignment`);
   - the deadline in the student's time zone;
   - the branch name (`<N>-short-description`), the commit subject and the pull request title, exactly as `task_context` returns them.
3. Suggest where to learn what the task needs: `topics_search` on the key concepts (e.g. "state machine", "testbench") and link the topic pages and video moments.
4. To start, hand over to the git steps (the `pds-git` plugin, skill `start`), or show the commands with explanations if that plugin is not installed.

Do not solve the task. Explain requirements and concepts, and point to examples.
