---
name: compile
description: Runs Intel Quartus Prime on a PDS project from the command line - Analysis & Synthesis only, or the full compilation (synthesis, fitter, assembler, timing) that produces the .sof for the board - and explains errors, critical warnings and synthesis problems (inferred latches, removed registers, incomplete sensitivity lists, truncated values). Use when the student asks to synthesize, compile, or why Quartus fails or warns.
---

# Compile with Quartus

## Steps

1. Project: the folder made by the `project` skill (`quartus_project_create`), or an existing project folder with a `.qpf`. No project yet: create one first.
2. **Call `quartus_compile`** with
   - `flow: "synthesis"` to check that the design synthesizes and to review it (seconds to a minute; enough for most assignments),
   - `flow: "full"` before timing analysis or programming the board (a few minutes; produces `output_files/<top>.sof`).
3. Explain the result in the course terms:
   - **errors**: file and line, what Quartus means, the VHDL-2008 rule behind it; the fix is the student's to make in `assignments/<N>` (show it, do not edit graded files);
   - **critical warnings** first (e.g. missing pin assignments, timing not met), then the synthesis review: inferred latches (incomplete assignment in a combinational process), registers removed or stuck at a constant, sensitivity-list problems, truncated values; the known harmless warnings are filtered;
   - the topic pages explain the background (`docs/topics/05-sequential-statements.md` latches, `08-combinational-optimization.md`, `09`..`11` sequential design) - point to them.
4. Show the commands the tool ran (`quartus_map <project>` or `quartus_sh --flow compile <project>`), so the student can run them in the project folder, and where the reports are (`output_files/*.rpt`; in the GUI **Processing > Compilation Report**; RTL schematic: **Tools > Netlist Viewers > RTL Viewer**).
5. After a successful full compilation: `timing` skill for timing closure, `program` skill for the board.

{{include teach-rule}}

{{include course-context}}
