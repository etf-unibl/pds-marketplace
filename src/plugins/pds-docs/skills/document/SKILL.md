---
name: document
description: Draft the Doxygen documentation (--! comments) of a VHDL design file in a PDS assignment as a skeleton - brief descriptions of the file, entity, ports, generics, architecture, signals, constants, types, processes and instances read from the code, with TODO placeholders for the detailed descriptions the student writes. Use when the student asks to document a design, add Doxygen comments, or start the documentation of an assignment.
---

# Documentation skeleton

The student documents the design (graded). You may add a skeleton through `docs_skeleton`, the only allowed change of a file in `assignments/`: brief descriptions you read from the code, and TODO placeholders for what the student writes.

## Steps

1. **Which file.** The design files of the task folder `assignments/<N>/` (`*_tb.vhd` are not part of the generated documentation). One file at a time; ask which one when there are several and the student did not say.
2. **Read the file and call `docs_outline`.** Understand the design from the code: what each port, signal and process does. The outline gives the key of every element and the comments it already has.
3. **Say what you will add and what stays theirs:** brief descriptions for the undocumented elements, `@details` placeholders for the entity and architecture, TODO placeholders for every brief you cannot state from the code. Existing comments are not changed.
4. **Write the briefs** (`briefs`: key -> one sentence, at most 120 characters, no Doxygen commands), only for elements without a comment and only what the code shows:
   - port / generic: what it carries, its unit or encoding, its active level when the code shows it (e.g. `Synchronous reset, active high` when the process tests `rst_i = '1'` inside `rising_edge`);
   - signal / constant / type: its role (`Current value of the counter`, `States of the control FSM`);
   - process: what it does (`Counter register with synchronous reset`), instance: what the instantiated unit does here;
   - file, entity, architecture: one sentence on what it is (`Modulo-10 counter with terminal count`, `RTL architecture with a register and next-state logic`).
   Leave a brief out (TODO) when the purpose is not clear from the code.
5. **Show the draft first:** `docs_skeleton` with `write: false`. Show the diff, the TODO placeholders and the skipped elements with the reason (e.g. a plain `--` comment the student can change to `--!`, a shared declaration `signal a, b`, an unlabeled process). Ask the student to confirm.
6. **Write it** after the student agrees: `docs_skeleton` with `write: true`. If the result has `realign`, say that `vhdl-style` will report the alignment of those comments and `vhdl-style --fix <N>` aligns them (the student runs it).
7. **What the student does next:**
   - fill every TODO in their own words, starting with the `@details` of the entity and architecture; help with questions about the design, never with the text (`docs_check` lists what is left);
   - check the briefs you generated and change any they would say differently: it is their documentation;
   - `style_report <N>` (the course style), then the `preview` skill to see the pages;
   - commit as usual: the skeleton's comments need no `AI-assisted-by:` line (below).

## Notes

- The tool places comments in the layout the course style accepts: a blank line between the comment and `entity` / `architecture` / `type` / `function` (VSG requires it, Doxygen still attaches the comment), port and signal comments at the end of the line in one column.
- It never puts a comment above a line whose previous line ends with a `--!` comment: Doxygen would join the two and attach both to the lower element (checked with Doxygen 1.9.5, the version of GitHub Pages).
- A second run adds nothing to elements that already have a comment, so it is safe after the student's edits.

{{include docs-rule}}

{{include teach-rule}}

{{include course-context}}
