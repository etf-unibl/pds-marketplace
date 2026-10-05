---
name: time
description: Help the student record time spent on PDS tasks - check /spent comment drafts, summarize logged time of an issue and explain the project board fields. Use when the student asks how to log time or why time was not counted.
---

# Time tracking

{{include teach-rule}}

## Rules (docs/time-tracking.md)

- Two ways, each work session recorded only once: increase `Time spent (h)` on the project board, or add a comment on the **issue** (not the pull request) with lines `/spent <duration> <description>`.
- Durations: `2h`, `1.5h`, `1,5h`, `1h30m`, `1h 30m`, `90m`, `45min`; a number without a unit is rejected; at most 24 h per line.
- `Time logged (h)` and `Time total (h)` are filled automatically; never edit them by hand. A valid comment gets 👍, an invalid one 😕 (fix it by editing the comment).

## Steps

1. Draft the comment with the student from what they actually did (ask; do not invent work). Check the draft with `spent_check` before they post it.
2. The student posts the comment on the issue themselves (web, or `gh issue comment <N> --body "..."`, which they run).
3. `time_summary` shows what the workflow counted for the issue (per author, invalid lines). It covers only the `/spent` part; the manual field is added in the weekly report.

Time tracking is graded (Workflow segment), so encourage recording it after each session.
