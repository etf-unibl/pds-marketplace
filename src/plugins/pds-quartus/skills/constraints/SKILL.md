---
name: constraints
description: Timing constraints (the SDC file) of a PDS design in Quartus - the clock (create_clock), PLL clocks, a virtual clock, input and output delays (set_input_delay / set_output_delay), false paths for switches, keys and LEDs, the maximum delay of a combinational path (set_max_delay) - with the theory to calculate the values (setup and hold conditions, lecture 13). The student writes the constraints; the assistant teaches how to find the values and checks them with the timing analysis. Use when the student asks about the SDC file, timing constraints, unconstrained paths, input or output delay, or how to choose a constraint value.
---

# Timing constraints (SDC)

The student writes the constraints and calculates their values; you teach the theory, check the reasoning and verify the result with the timing analysis. Constraints are part of the timing lecture, so a ready-made SDC would take away what the student should learn.

## Steps

1. **Where the design stands.** The project folder from `quartus_project_create` has `<top>.sdc`; read it (it is outside the repository). After a full compilation (`compile` skill, `flow: "full"`), **call `quartus_timing`** and show what is unconstrained (`unconstrained`, `check_timing`) and which clocks exist.
2. **Point to the lecture** `docs/topics/13-timing-analysis.md` (with pds-learning: `topic_get 13`) and the video moments that fit the question: setup and hold (01:13), the setup condition and fmax (11:56), the hold condition (16:29), clock skew and hold violations (20:31), the SDC file (44:11), `create_clock` (53:16), `set_input_delay` and `set_output_delay` (1:07:11). Closing timing by pipelining: topic 14 (`topic_get 14`).
3. **Explain the theory** of the constraint at hand (below), in the lecture's notation, and ask the student where each number comes from: the clock of the task or the board, the datasheet of the external device (`Tco`, `Tsetup`, `Thold`), the board delay, the requirement of the task.
   - **An on-board device** (SDRAM, ADC, VGA DAC, audio codec, TV decoder): `board_device_timing` gives its connection, clock, datasheet pages and pitfalls.
   - **The component's values:** a timing card from the pds-datasheet `datasheet` skill holds them (role, datasheet parameter, value, page). Use the card's roles in the formulas below. Without a card: if the student has the datasheet as a PDF, use that skill (with pds-datasheet installed; otherwise tell the student to install it), or let the student read the values with the parameter names of that skill. Never fill in a component value yourself: a value without a source stays open (strict rule below).
   - **The board delay:** an estimate (below, "The FPGA and the board"); the student writes the assumption in a comment next to the constraint. **Let the student calculate the value.** Check the calculation step by step and point to the wrong step instead of giving the result. A worked example uses other numbers than the student's design.
4. **The student edits `<top>.sdc`.** The generated file already has the board facts (the `CLOCK_50` clock, `derive_pll_clocks`, `derive_clock_uncertainty`) and commented templates with the design's port names: uncomment a line and write the value. **Do not write the SDC yourself**, also not when asked: show the line, explain each option, and let the student add it, as with commands that change something.
5. **Check:** compile again with `flow: "full"` (the Fitter uses the SDC too), then `quartus_timing`. The constrained path must no longer be listed as unconstrained; read the setup slack (`-max` values) and the hold slack (`-min` values). Negative slack: `timing` skill (what to change in the design, or whether the requirement allows a different constraint). An SDC error (unknown port, wrong syntax) appears in the compile result: explain the message and let the student correct the line.
6. **Keep the student's work.** Never re-create the project to "reset" constraints. If the project is re-created (`overwrite`, only when the student asks), `quartus_project_create` keeps an edited SDC (`sdc_kept`) and writes the fresh template next to it as `<top>.sdc.new`.

## Theory (notation of lecture 13)

- **Between two registers on one clock** with period `Tc`:
  - setup: `Tcq + Tnext(max) + Tsetup < Tc`, so setup slack = `Tc - (Tcq + Tnext(max) + Tsetup)` and `fmax = 1 / (Tcq + Tnext(max) + Tsetup)`;
  - hold: `Thold < Tcq + Tnext(min)`, so hold slack = `Tcq + Tnext(min) - Thold`;
  - clock skew `Tskew` (the capturing register gets the edge later than the launching one) adds to the setup side (`Tc + Tskew`) and to the hold requirement (`Thold + Tskew`): it helps setup and endangers hold.
  - The designer chooses `Tc` (`create_clock -period`) and changes `Tnext` (the logic); `Tcq`, `Tsetup` and `Thold` belong to the device and are in the timing report.
- **Input delay** (`set_input_delay -clock clk_virt`): an external flip-flop, clocked by the virtual clock `clk_virt` with the external device's period, launches the data; it reaches the FPGA pin `Tco(ext) + Tboard` after the edge.
  - `-max` = `Tco(ext,max) + Tboard(max)`: used for setup; the path from the pin to the first register inside the FPGA must then fit into `Tc - input delay(max) - Tsetup`.
  - `-min` = `Tco(ext,min) + Tboard(min)`: used for hold.
- **Output delay** (`set_output_delay -clock clk_virt`): an external flip-flop captures the FPGA output; the data must arrive `Tsetup(ext)` before its edge and the board adds `Tboard`.
  - `-max` = `Tboard(max) + Tsetup(ext)`: the path from the last register in the FPGA to the pin must fit into `Tc - output delay(max)`.
  - `-min` = `Tboard(min) - Thold(ext)`: used for hold.
- **The FPGA sends the clock to the device** (SPI `SCLK`, SDRAM `CLK`, a shift register's clock): the clock crosses the board too. The delays are relative to the clock on the FPGA's clock output port (`create_generated_clock` on that port, from the clock that drives it), and `Tclk_board` is the trace of that clock:
  - input: `-max` = `Tclk_board(max) + Tco(ext,max) + Tdata_board(max)`, `-min` = `Tclk_board(min) + Tco(ext,min) + Tdata_board(min)`;
  - output: `-max` = `Tdata_board(max) + Tsetup(ext) - Tclk_board(min)`, `-min` = `Tdata_board(min) - Thold(ext) - Tclk_board(max)`;
  - for an output, a clock trace as long as the data trace cancels it (why boards route them with equal lengths); for an input the two add up (the clock goes out, the data comes back), which limits how fast the FPGA can read the device.
- **Combinational path from an input to an output** (no clock): `set_max_delay -from [all_inputs] -to [all_outputs] <ns>`, where the value is the time the surrounding system allows between an input change and a valid output (e.g. what is left of the external clock period after the external `Tco`, the board delays and the external `Tsetup`). `quartus_timing` reports the actual delays (`pin_to_pin`) to compare with.
- **No timing relation to the clock:** switches and push buttons change at any moment (synchronize them in VHDL with two flip-flops, then `set_false_path -from` those ports); LEDs and 7-segment displays are read by a person (`set_false_path -to`). These are board facts, not calculated values.
- **Orders of magnitude**, only to check a result, never as a value: a board trace adds about 1 ns per 15 cm. The `Tco` and `Tsetup` of fast logic and memories are a few ns, while slow serial devices are often tens of ns. A computed input or output delay larger than the clock period means a wrong number, or a requirement the design cannot meet. A value that looks implausible is checked again on its datasheet page, not replaced.

## Notes

- The constraints are read by the Fitter as well: after any change of the SDC compile again before `quartus_timing`.
- Show how the same is done in the GUI: **Tools > Timing Analyzer**, menu **Constraints** (*Create Clock*, *Set Input Delay*, *Set Output Delay*, *Set False Path*), which shows the matching SDC command (lecture 13).

{{include datasheet-rule}}

{{include board-timing}}

{{include quartus-tools-rule}}

{{include teach-rule}}

{{include course-context}}
