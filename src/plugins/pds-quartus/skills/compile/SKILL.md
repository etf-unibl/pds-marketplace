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
   A run longer than about 90 s continues in the background: the result has `status: "running"`, a `job` id, the elapsed time and the finished stages. Tell the student briefly what Quartus is doing (e.g. "synthesis done, fitter running"), then **call `quartus_job` with the job id** and repeat until `status: "done"`; the done result is the same as a direct one. Until then the reports in the project folder belong to an unfinished run: do not read them, and do not call `synth_summary` or `quartus_timing` or start another compilation of the same project.
3. Explain the result in the course terms:
   - **errors**: file and line, what Quartus means, the VHDL-2008 rule behind it; the fix is the student's to make in `assignments/<N>` (show it, do not edit graded files);
   - **critical warnings** first (e.g. missing pin assignments, timing not met), then the synthesis review: inferred latches (incomplete assignment in a combinational process), registers removed or stuck at a constant, sensitivity-list problems, truncated values; the known harmless warnings are filtered;
   - the topic pages explain the background (`docs/topics/05-sequential-statements.md` latches, `08-combinational-optimization.md`, `09`..`11` sequential design) - point to them.
4. Show the commands the tool ran (`quartus_map <project>` or `quartus_sh --flow compile <project>`), so the student can run them in the project folder, and where the reports are (`output_files/*.rpt`; in the GUI **Processing > Compilation Report**; RTL schematic: **Tools > Netlist Viewers > RTL Viewer**).
5. After a successful full compilation: if the student asked about timing, **call `quartus_timing`** and answer from its result (`timing` skill); the timing summary of the compilation itself has no input-to-output delays of a combinational design. `program` skill for the board.

{{include quartus-tools-rule}}

{{include teach-rule}}

{{include course-context}}
