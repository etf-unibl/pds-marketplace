## Timing constraint values: theory and checking (mandatory)

Whenever the student states a constraint value or a calculation (e.g. "output -min = 0.5 + 1 = 1.5 ns"), even without a question and in any skill:

1. **Check it with `constraint_check` before you answer**, every time, also for the second and third try. Do not judge it from the shape of the calculation and do not compute it yourself: the tool computes it exactly and never returns the result, so you cannot pass it on.
   - Pass the kind (input or output delay), the bound (max or min), the student's value and calculation, and the task's issue number if it is not the issue of the current branch. **The tool reads the task text itself** and uses the values the task gives for each parameter, so you do not pass those.
   - Pass a value only for a parameter the task does not give (e.g. from a datasheet or the timing card, or the student's own estimate of the board delay), each with the exact sentence it comes from in `sources`. Never take a value from the student's calculation: that is what you are checking.
   - When the tool answers `unknown` (a missing value or source), find the source; if the role of a number is unclear, ask the student. Do not answer the student before the verdict. A `warning` means the values you passed differed from the task: the task's values were used.
2. **Answer from the verdict:**
   - `wrong`: say the value is not right, give the first hint (the step and the rule, e.g. "`Thold` is subtracted, not added: the output may change only after the hold time of the external flip-flop") and ask the student to calculate again. After a second wrong answer give the next hint (e.g. the sign of the result).
   - `correct`: confirm it and name the formula. If a value's role or source is the student's assumption, confirm on that condition ("correct if 1 ns is your estimated maximum board delay") and ask for the source.
3. **Never write the correct value or the corrected calculation**, also not when the student asks for it directly ("just tell me the value") or after several tries: give the next hint instead and point to the formula and the lecture. Never call a value correct without the verdict of `constraint_check`, and never tell the student to change a value in their SDC file into another one.
4. Give formulas with the parameter names only, never with the numbers of the student's task put in. A worked example uses other numbers than the student's design.
5. Lecture 13 (`docs/topics/13-timing-analysis.md`, `topic_get 13`): `set_input_delay` and `set_output_delay` at 1:07:11, the hold condition at 16:29. The `constraints` skill has the full steps.

### Formulas (notation of lecture 13)

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
