---
name: synthesis
description: Review a compiled Quartus project of the PDS course - warnings that point to design errors (inferred latches, incomplete sensitivity lists, unused signals, derived clocks), resources (ALMs, registers, memory, DSP) and timing (Fmax, slack, unconstrained paths). Use after the student compiled a design in Quartus or asks about synthesis or timing results.
---

# Synthesis and timing review

{{include teach-rule}}

{{include course-context}}

## Steps

1. The student compiles the project (Quartus **Processing > Start Compilation**, or `quartus_sh --flow compile <project>`, which they run). Do not start long compilations yourself.
2. `synth_summary <project folder>` reads the reports (project folder or `output_files/`): flow summary, `design_warnings` with explanations and the topic that covers them, and timing.
3. Explain, most important first:
   - **latch inferred (10631)** and **incomplete sensitivity list (10492)**: in a combinational process every output must be assigned in every branch and every read signal must be in the list (or `process(all)` in VHDL-2008); see topic 5 (`topic_get 5`) and show where in the student's file;
   - **registers**: a purely combinational task must have `Total registers` 0; a sequential one should have the expected number (state bits, counters);
   - **resources**: compare ALMs between architectures when the task asks for optimization (topic 8);
   - **timing**: without an SDC file the analysis assumes 1 GHz (topic 13); with one, negative slack means the design is too slow for the clock: find the critical path (Timing Analyzer **Report Timing**) and discuss pipelining (topic 14) or a simpler next-state logic. Unconstrained input/output ports need `set_input_delay`/`set_output_delay` or a false path for asynchronous inputs.
4. Link the topic pages and video moments with `topics_search` for the concepts the student needs.

Explain causes and point to the lines; the student changes the code.
