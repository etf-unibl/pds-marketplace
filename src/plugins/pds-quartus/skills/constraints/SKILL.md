---
name: constraints
description: Timing constraints (the SDC file) of a PDS design in Quartus - the clock (create_clock), PLL clocks, a virtual clock, input and output delays (set_input_delay / set_output_delay), false paths for switches, keys and LEDs, the maximum delay of a combinational path (set_max_delay) - with the theory to calculate the values (setup and hold conditions, lecture 13). The student writes the constraints; the assistant teaches how to find the values and checks them with the timing analysis. Use when the student asks about the SDC file, timing constraints, unconstrained paths, input or output delay, or how to choose a constraint value.
---

# Timing constraints (SDC)

The student writes the constraints and calculates their values; you teach the theory, check the reasoning and verify the result with the timing analysis. Constraints are part of the timing lecture, so a ready-made SDC would take away what the student should learn.

## Steps

1. **Where the design stands.** The SDC file the project uses is `sdc_file` of `quartus_project_create`; read it. Normally it is `<top>.sdc` in the project folder (outside the repository). **When the task asks to submit the constraints** (an `.sdc` file in `assignments/<N>/`), the student edits the submitted file and the project must use it:
   - if `assignments/<N>/<top>.sdc` exists when the project is created, `quartus_project_create` uses it (`sdc_source`) and writes no second copy;
   - if the project was created before the student added that file: the student copies the project's `<top>.sdc` (the template, or their edited version) into `assignments/<N>/<top>.sdc` (show the `copy` command), then the project is created again with `overwrite: true` so it uses that file. Never tell the student to edit one file while Quartus reads another.
   After a full compilation (`compile` skill, `flow: "full"`), **call `quartus_timing`** and show what is unconstrained (`unconstrained`, `check_timing`) and which clocks exist.
2. **Point to the lecture** `docs/topics/13-timing-analysis.md` (with pds-learning: `topic_get 13`) and the video moments that fit the question: setup and hold (01:13), the setup condition and fmax (11:56), the hold condition (16:29), clock skew and hold violations (20:31), the SDC file (44:11), `create_clock` (53:16), `set_input_delay` and `set_output_delay` (1:07:11). Closing timing by pipelining: topic 14 (`topic_get 14`).
3. **Explain the theory** of the constraint at hand (formulas in the shared text below), in the lecture's notation, and ask the student where each number comes from: the clock of the task or the board, the datasheet of the external device (`Tco`, `Tsetup`, `Thold`), the board delay, the requirement of the task.
   - **An on-board device** (SDRAM, ADC, VGA DAC, audio codec, TV decoder): `board_device_timing` gives its connection, clock, datasheet pages and pitfalls.
   - **The component's values:** a timing card from the pds-datasheet `datasheet` skill holds them (role, datasheet parameter, value, page). Use the card's roles in the formulas below. Without a card: if the student has the datasheet as a PDF, use that skill (with pds-datasheet installed; otherwise tell the student to install it), or let the student read the values with the parameter names of that skill. Never fill in a component value yourself: a value without a source stays open (strict rule below).
   - **The board delay:** an estimate (below, "The FPGA and the board"); the student writes the assumption in a comment next to the constraint. **Let the student calculate the value.**
   - Check every value and calculation of the student against the formulas (shared text below): never confirm a wrong value, never give the result.
4. **The student edits the SDC file the project uses** (`sdc_file`, step 1). The generated file already has the board facts (the `CLOCK_50` clock, `derive_pll_clocks`, `derive_clock_uncertainty`) and commented templates with the design's port names: uncomment a line and write the value. **Do not write the SDC yourself**, also not when asked: show the line, explain each option, and let the student add it, as with commands that change something.
5. **Check:** compile again with `flow: "full"` (the Fitter uses the SDC too), then `quartus_timing`. The constrained path must no longer be listed as unconstrained; read the setup slack (`-max` values) and the hold slack (`-min` values). Negative slack: `timing` skill (what to change in the design, or whether the requirement allows a different constraint). An SDC error (unknown port, wrong syntax) appears in the compile result: explain the message and let the student correct the line.
6. **Keep the student's work.** Never re-create the project to "reset" constraints. If the project is re-created (`overwrite`, only when the student asks), `quartus_project_create` keeps an edited SDC (`sdc_kept`) and writes the fresh template next to it as `<top>.sdc.new`.

## Notes

- The constraints are read by the Fitter as well: after any change of the SDC compile again before `quartus_timing`.
- Show how the same is done in the GUI: **Tools > Timing Analyzer**, menu **Constraints** (*Create Clock*, *Set Input Delay*, *Set Output Delay*, *Set False Path*), which shows the matching SDC command (lecture 13).

{{include sdc-theory}}

{{include datasheet-rule}}

{{include board-timing}}

{{include quartus-tools-rule}}

{{include teach-rule}}

{{include course-context}}
