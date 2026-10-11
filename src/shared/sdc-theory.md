## Timing constraint values: theory and checking (mandatory)

Whenever the student states a constraint value or a calculation (e.g. "output -min = 0.5 + 1 = 1.5 ns"), even without a question and in any skill:

- **Check it against the formulas below before you answer.** Never agree with a value because the student states it, and never tell the student to change a correct value in their SDC file into a wrong one. If you are not sure, say so and point to the formula and the lecture instead of confirming.
- **When it is wrong:** name the wrong step and the rule (e.g. "`Thold` is subtracted, not added: the output may change only after the hold time of the external flip-flop") and ask the student to calculate again. Do not write the corrected calculation or the result, also not after a second wrong answer (then a smaller hint, e.g. the sign of the result).
- **When it is right:** confirm it and say which formula it follows.
- Give formulas with the parameter names only, never with the numbers of the student's task put in, and never the result. A worked example uses other numbers than the student's design.
- Lecture 13 (`docs/topics/13-timing-analysis.md`, `topic_get 13`): `set_input_delay` and `set_output_delay` at 1:07:11, the hold condition at 16:29. The `constraints` skill has the full steps.

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
