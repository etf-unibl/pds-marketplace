---
name: setup
description: Check and explain the student's PDS course setup (git identity with the GitHub noreply e-mail, course git hooks, Python virtual environment with the style tools, GHDL, Quartus, ModelSim/Questa, gh). Use when a student starts the course, clones the repository, or a tool is missing or misconfigured.
---

# Course setup check

{{include teach-rule}}

{{include course-context}}

## Steps

1. Run `env_check` (read-only). It reports the tools on PATH with versions, the git identity, whether the course hooks are enabled and a list of problems.
2. Go through the problems one at a time, most important first:
   - **git identity**: `user.name` must be the student's name, `user.email` the GitHub noreply address `<number>+<username>@users.noreply.github.com` (GitHub **Settings > Emails > Keep my email addresses private**). Show `git config --global user.name "..."` and `git config --global user.email "..."` and explain why the noreply address is used (private e-mail, sign-off line `Signed-off-by` must match the author).
   - **hooks**: show `git config core.hooksPath .githooks` (run once in the repository) and explain what the three hooks do (pre-commit: only `assignments/<N>/`; commit-msg: message format and sign-off; prepare-commit-msg: pre-filled message).
   - **style tools**: a virtual environment in the repository and `python -m pip install -r requirements.txt` (on the `assignments` branch); the environment must be activated in every new terminal. Check the version with `vhdl-style --version`.
   - **GHDL, Quartus, ModelSim/Questa**: point to the matching section of `docs/tools-setup.md` (use `course_doc tools-setup`) and say which folder must be on PATH.
3. After the student has made a change, run `env_check` again and confirm what is now correct.

Point to `docs/getting-started.md` (checklist) and `docs/git-setup.md` for the full instructions. Never run installers or `git config` writes yourself.
