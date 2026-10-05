---
name: style
description: Explain VHDL style check results of the PDS course (vhdl-style, VSG rules and course pds_ rules, VHDL-2008 errors) and how to fix them. Use when the linter job fails or the student asks about a style rule or a vhdl-style message.
---

# VHDL style

{{include teach-rule}}

{{include course-context}}

## Steps

1. `style_report <N>` (or a folder or file). It runs `vhdl-style` without `--fix` and returns the violations with file, line, rule and message. If the tool is missing, explain the setup (virtual environment, `python -m pip install -r requirements.txt`).
2. Group the violations: many are fixed automatically by `vhdl-style --fix <N>` (indentation, case of keywords, spacing). Show that command, explain that it rewrites the files and that the student should review the changes with `git diff` before committing; the student runs it.
3. Explain the remaining violations one rule at a time:
   - `pds_*` rules are course rules; their message starts with the OHWR rule name in brackets (e.g. `[FileHeader]`, `[PortsName]`);
   - other identifiers are VSG rules;
   - `[VHDLVersion]` lines are GHDL errors (the code is not valid VHDL-2008); explain them like compiler errors.
   Look the rule up in the rule reference linked from `docs/vhdl-code-style.md` (`course_doc vhdl-code-style`) and show the corrected line; the student edits the file.
4. Run `style_report` again after the student's changes.

Typical course rules: file header with the current year, file named like the entity, port suffixes by mode (`_i`, `_o`), signal and constant naming, one statement per line, no `buffer` ports, only `numeric_std` arithmetic.
