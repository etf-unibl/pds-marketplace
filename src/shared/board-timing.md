## The FPGA and the DE1-SoC board (verified facts, with their source)

Sources: *DE1-SoC User Manual* (Terasic, rev. F of 2019-01-28; rev. E of 2015 where noted) and the *DE1-SoC schematics* (rev. F of 2014-11-20; rev. C of 2014-03-24 where noted), sheet numbers as printed. Use only these facts and what a tool reads from a datasheet. Anything else about the board is unknown (see the strict rule).

- **The FPGA:** Cyclone V SE `5CSEMA5F31C6` (speed grade 6). Its own delays (I/O buffers, routing, the setup, hold and clock-to-output times of its registers) are in the Quartus timing model, applied at the slow and the fast corner. **The SDC describes only what is outside the FPGA:** `set_input_delay` and `set_output_delay` hold the external device and the board, never numbers of the FPGA. The FPGA side appears in `quartus_timing` (data delay, slack).
- **Clocks:**
  - `CLOCK_50` (PIN_AF14), `CLOCK2_50`, `CLOCK3_50` and `CLOCK4_50` are 50 MHz outputs of a Si5350C clock generator (manual 3.5; schematic sheet 6).
  - `CLOCK_50` is 20 ns; PLL clocks: `derive_pll_clocks`.
- **I/O voltage:** the FPGA pins of the user interfaces are 3.3 V (pin tables of the manual). The column of a component datasheet is therefore the one for a 3.3 V supply or I/O supply (`VCC`, `OVDD`, `VDDQ`, as the datasheet names it).
- **GPIO headers (JP1, JP2):**
  - Each of the 2x36 data pins goes from the FPGA through a 47 Ω series resistor (resistor networks RN2...RN19) to the header. On the header side, a BAT54S diode pair clamps it to 3.3 V and GND (manual 3.6.3; schematic sheets 12 and 13; on rev. C the clamp rail is `VCC3P3_GPIO`).
  - On GPIO 0, `GPIO_0_D0` and `GPIO_0_D2` (header pins 1 and 3) are marked as clock inputs (`Clock_in`, sheet 12).
  - A component on a GPIO header is the student's: they provide its datasheet.
- **On-board devices connected to the FPGA:** the notes of each are returned by **`board_device_timing`** (`sdram`, `adc-ltc2308`, `adc-ad7928`, `vga-adv7123`, `audio-wm8731`, `video-adv7180`, `level-shifter-txb0104`, `clock-si5350c`, `fpga-cyclone-v`). They cover the connection and the clock, where the timing is in the checked datasheet revision, the role of each parameter, and the pitfalls. Call it before explaining an on-board device. In short:
  - **SDRAM (U27):** the part is not named in the board documents; read the chip marking (revision letter and speed grade change the values). One lab board carries IS42S16320D-7TL (`board_device_timing sdram`), but the student confirms the marking on their own board. `DRAM_CLK` is a PLL clock output of the FPGA.
  - **ADC (U24):** check the board revision or the chip.
    - **Rev. F boards:** LTC2308, connected directly. Its timing is specified at OVDD = 5 V, but the board runs it at 3.3 V.
    - **Rev. C boards:** AD7928 at 5 V, behind a TXB0104 level shifter (U26), whose delay adds to every ADC signal.
    - The FPGA pins are the same; the protocols differ.
  - **VGA DAC ADV7123:** `VGA_CLK` is a PLL clock output. `VGA_HS` and `VGA_VS` bypass the DAC. The speed grade is on the chip.
  - **Audio codec WM8731:** master or slave mode is chosen by the design; the timing is given at 25 °C only.
  - **TV decoder ADV7180:** sends its clock `TD_CLK27` with the data (source-synchronous input).
  - **Asynchronous inputs** (synchronize them, then use a false path): PS/2 (through 120 Ω, sheet 21), the IR receiver, and `KEY[3:0]` (through a 74HC245 buffer, sheet 20).
- **Board delays, estimated:**
  - A trace on FR-4 carries a signal about 15 cm per ns (6 to 7 ps/mm). The length is the path between the pins: from the board layout if available, otherwise the straight distance on the board times about 1.5 for routing.
  - A ribbon cable or jumper wires on a GPIO header add about 5 ns per metre.
  - A series resistor `R` with the load capacitance `C` it drives (input pins, trace, clamp diodes) slows the edge by about `0.7·R·C`. For example, 47 Ω and 10 pF give 0.3 ns. The capacitances are in the datasheets of the parts.
  - A buffer or level shifter in the path adds its own `tpd` (its datasheet).
  - For the clock-forwarding formulas, the difference between the clock and data traces matters, not their lengths alone.
  - A board delay is an estimate, never a datasheet value. Agree the estimate with the student, use 0 for a minimum (the safe side for hold), round a maximum up, and write the assumption in a comment in the SDC.
