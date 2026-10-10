# DE1-SoC devices: timing notes for the constraints

Checked against the board documents (DE1-SoC User Manual rev. F 2019-01-28 and rev. E 2015, schematics rev. F 2014-11-20 and rev. C 2014-03-24) and the datasheet revisions named in each section. These notes say where the values are and what to watch for, so the assistant can guide the student and check their reading. **The student reads every value from their own datasheet.** A value here is valid only for the named part, revision and column. If the student's chip or datasheet differs, the value here does not apply. Nothing here may be used to fill in a value that the student's datasheet does not contain.

## sdram
- **Board:** U27, 64 MB (32Mx16), 3.3 V, all lines directly to the FPGA (schematic sheet 14). `DRAM_CLK` is PIN_AH12 = `FPLL_BL_CLKOUT0`, a PLL clock output (sheet 6): a clock sent from the FPGA, so the clock-forwarding formulas apply (`create_generated_clock` on `DRAM_CLK`).
- **Part:** not named in the manual or the schematic. Read the marking of U27: the family and voltage (IS42**S** = 3.3 V, IS42**R** = 2.5 V in the ISSI ordering tables), the revision letter (`...16320D`, `...16320F`) and the speed grade (`-5`, `-6`, `-7`).
- **Checked datasheets:** ISSI IS42/45S16320D Rev. 00B (2011-06-09), AC electrical characteristics page 19; ISSI IS42/45S16320F Rev. C4, same table on page 17. Ordering information (speed grade → frequency): D, page 62.
- **Roles:**
  - `Tco(ext,max)` = `tAC` (access time from CLK), in the row of the CAS latency the design programs (`tac3` / `tac2`).
  - `Tco(ext,min)` = `tOH` (output data hold, `toh3` / `toh2`).
  - `Tsetup(ext)` = `tDS` / `tAS` / `tCMS` / `tCKS` (data, address, command, CKE).
  - `Thold(ext)` = `tDH` / `tAH` / `tCMH` / `tCKH`.
  - Clock limit = `tCK` for the CAS latency.
  - Design, not SDC: `tRCD`, `tRP`, `tRC`, `tRAS`, `tMRD`, `tREF` (cycles of the controller).
- **Watch for:**
  - The revisions differ: `tOH` is 2.7 ns (-6, -7) in D but 2.5 ns in F; `tDS` (-5) is 1.8 ns in D but 1.5 ns in F. Check the revision of the datasheet against the chip.
  - Footnote 2: setup and hold are measured with `tt` = 1 ns; with a slower clock edge, `(tt/2 - 0.5)` ns is added. Footnote 3: reference level 1.4 V.
  - Columns: three speed grades, each with Min and Max; `—` means no value on that side.

## adc-ltc2308
- **Board:** rev. F boards (manual rev. F 3.6.12; schematic rev. F sheet 21, U24 LTC2308CUF). `ADC_SCLK` (PIN_AK2), `ADC_DIN`, `ADC_DOUT` and `ADC_CONVST` (PIN_AJ4) go directly to the FPGA, with no series resistors. OVDD (pin 19) is on VCC3P3 through R447 (0 Ω): the digital I/O runs at **3.3 V**. SCLK comes from the FPGA (a clock sent from the FPGA, or SCLK generated as data by the design).
- **Checked datasheet:** LTC2308 Rev. C, 10/16 (document `2308fc`): Timing Characteristics on page 5, timing diagrams on page 10, SDI/SDO behaviour on pages 8 and 15.
- **Roles:**
  - `Tco(ext,max)` = `tdDO` (SDO data valid **after SCK falling edge**, CL = 25 pF).
  - `Tco(ext,min)` = `thDO` (SDO hold time after SCK falling edge).
  - `Tsetup(ext)` = `tSUDI` (SDI valid before SCK rising edge).
  - `Thold(ext)` = `tHD` (SDI hold after SCK rising edge).
  - Clock limit = `fSCK` max, `tWHCLK` / `tWLCLK`.
  - Design: `tCONV`, `tACQ`, `tWHCONV`, `tHCONVST`, `fSMPL(MAX)`.
- **Watch for:**
  - **Note 4: the timing is specified at OVDD = 5 V** (AVDD = DVDD = OVDD = 5 V). The board runs OVDD at 3.3 V, and this datasheet gives no timing at 3.3 V. Say so: the 5 V values are not 3.3 V values. The student decides with the course staff how to proceed (e.g. a margin, or a lower SCK frequency), stated as an assumption.
  - SDO changes on the falling SCK edge and SDI is sampled on the rising edge: the two directions use different edges (`-clock_fall` where the edge is the falling one).
  - Input capacitance `CIN` = 5 pF (page 4).

## adc-ad7928
- **Board:** older boards, shown in the schematic rev. C (2014-03-24, sheet 21) and the manuals rev. E and v0.6. U24 is an AD7928BRUZ at the same FPGA pins as the later LTC2308; PIN_AJ4 is `ADC_CS_N`.
  - **Supply:** AVDD and VDRIVE are on VCC5_ADC: the ADC runs at **5 V**, so its table column is **AVDD = 5 V**. Reference: ADR5041 on REFIN (net `VREF2P5`).
  - **Level shifter:** `ADC_SCLK`, `ADC_DIN`, `ADC_DOUT` and `ADC_CS_N` pass through **U26, a TXB0104RGYR** (VCCA = 3.3 V on the FPGA side, VCCB = 5 V on the ADC side, OE pulled up to 3.3 V through 10 kΩ). It adds its own propagation delay to every signal (section `level-shifter-txb0104`). There are no other series parts.
- **Checked datasheet:** AD7908/AD7918/AD7928 Rev. E: Timing Specifications, Table 4, page 9; load circuit Figure 2; serial interface timing diagrams on pages 25-26.
- **Roles:**
  - `Tco(ext,max)` = `t4` (data access time after SCLK **falling** edge).
  - `Tco(ext,min)` = `t7` (SCLK to DOUT valid hold time).
  - `Tsetup(ext)` = `t9` (DIN setup before SCLK **falling** edge).
  - `Thold(ext)` = `t10` (DIN hold after SCLK falling edge).
  - `t2` (CS to SCLK setup), `t3` (CS to DOUT enabled), `t11` (16th SCLK falling edge to CS high).
  - Clock limit = `fSCLK`.
  - Design: `tCONVERT` (16 SCLK), `tQUIET`.
- **Watch for:**
  - Footnote 1: sample tested at 25 °C, inputs timed from 1.6 V with 5 ns edges. Footnote 2: SCLK mark/space ratio 40/60 to 60/40.
  - Unlike the LTC2308, both directions use the falling edge.
  - The translator delays enter the formulas like board delays:
    - SCLK goes out through it (A to B), and DOUT comes back through it (B to A): both add to the input delay (a round trip).
    - SCLK and DIN both go out through it: only their difference (the channel-to-channel skew) changes the output timing.

## level-shifter-txb0104
- **Board:** U26 on rev. C boards, between the FPGA (A port, VCCA = 3.3 V) and the AD7928 (B port, VCCB = 5 V), schematic rev. C sheet 21. The package is RGY (VQFN 14).
- **Checked datasheet:** TI TXB0104 Rev. K: Switching Characteristics, VCCA = 3.3 V ± 0.3 V, table 5.21 for the RGY package ("Other Packages", not BQA/DYY), page 14; the column for VCCB = 5 V ± 0.5 V. Parameter measurement information on page 17; output load considerations in 7.3.3, page 21.
- **Roles:**
  - `tpd` A-to-B (FPGA → ADC: SCLK, DIN, CS_N), Min and Max;
  - `tpd` B-to-A (ADC → FPGA: DOUT), Min and Max;
  - `tSK(O)`, the channel-to-channel skew, Max.
  The student adds them to the board path with min to min and max to max.
- **Watch for:** the BQA/DYY tables on the same pages are another package. The TXB0104 senses the direction automatically and has weak output drivers, so its delay depends on the load (7.3.3).

## vga-adv7123
- **Board:** U5 ADV7123 (sheet 16), VAA = 3.3 V (VGA_VCC3P3 through R57, 0 Ω), RSET = 560 Ω. `VGA_R/G/B[7:0]` go to the upper 8 bits (R9...R2 etc.), together with `VGA_BLANK_N` and `VGA_SYNC_N` (clocked by the DAC). `VGA_CLK` (PIN_A11) is a PLL clock output (`FPLL_TL_CLKOUT0`, sheet 6): a clock sent from the FPGA. `VGA_HS` and `VGA_VS` do **not** pass the DAC: they go to the connector through 47 Ω (R18, R17), so they have no setup or hold relation to `VGA_CLK`.
- **Part:** the speed grade (50, 140, 240 or 330 MHz) is in the part number on the chip; the schematic only says "ADV7123".
- **Checked datasheet:** ADV7123 Rev. D: 3.3 V Timing Specifications, Table 6, page 8, with the timing diagram (Figure 2) on the same page. The conditions match the board: VAA = 3.0 V to 3.6 V, RSET = 560 Ω, CL = 10 pF.
- **Roles:**
  - `Tsetup(ext)` = `t1` (data and control setup, Min column).
  - `Thold(ext)` = `t2` (data and control hold, Min column).
  - Clock limit = `fCLK` of the speed grade, `t4` / `t5` (pulse widths per grade).
  - Design: pipeline delay `tPD` = 1 clock cycle: HS and VS (which bypass the DAC) are delayed one clock in the design to stay aligned with the picture.
- **Watch for:** the 5 V Timing Specifications are on page 7, the 3.3 V ones on page 8; the board uses the 3.3 V table. The temperature range depends on the grade (footnote 2).

## audio-wm8731
- **Board:** U3 WM8731 (sheet 18). `AUD_XCK` → XTI/MCLK; `AUD_BCLK`, `AUD_DACDAT`, `AUD_DACLRCK`, `AUD_ADCDAT`, `AUD_ADCLRCK` directly to the FPGA, with no series resistors. MODE is tied to GND: 2-wire (I2C) control, address 0x34, through the I2C multiplexer (manual 3.6.5). Master or slave mode is chosen by the design (register setting).
- **Checked datasheet:** Wolfson WM8731 Production Data Rev 4.0 (February 2005): master clock timing on page 13; digital audio interface in master mode on page 14 and in slave mode on pages 15-16; 3-wire control on page 16; 2-wire control on page 17.
- **Roles:**
  - **Slave mode (the FPGA drives BCLK and LRC):**
    - `Tsetup(ext)` = `tDS` (DACDAT to BCLK rising) and `tLRSU`.
    - `Thold(ext)` = `tDH` and `tLRH`.
    - `Tco(ext)` = `tDD` (ADCDAT from BCLK **falling** edge; Min and Max).
    - Clock limits: `tBCY`, `tBCH`, `tBCL`.
  - **Master mode (the codec drives BCLK):** `tDL` (LRC from BCLK falling edge), `tDDA` (ADCDAT from BCLK falling edge), `tDST` / `tDHT` (DACDAT setup and hold to BCLK rising edge).
  - MCLK limits: `tXTIY` (cycle time), `tXTIH` / `tXTIL`, duty cycle.
- **Watch for:**
  - All values are at **TA = +25 °C** and 3.3 V, not over the temperature range. Say so.
  - The master-mode table repeats "Slave Mode" in its test conditions (an error in the datasheet): take the table under the master-mode figure.
  - A newer revision exists (Cirrus Logic). The student cites the revision they use.

## video-adv7180
- **Board:** ADV7180 (sheet 17; manual 3.6.7), crystal 28.63636 MHz (sheet 17; datasheet nominal 28.6363 MHz). `TD_CLK27` is the decoder's output clock (LLC) into the FPGA, with the data `TD_DATA[7:0]`, `TD_HS` and `TD_VS`. This is a **source-synchronous input**: the clock comes with the data, so the clock is created on `TD_CLK27` (`create_clock`) and the input delays are relative to it.
- **Checked datasheet:** ADV7180 Rev. K: Timing Specifications, Table 5, pages 8-9; Figure 7 (Pixel Port and Control Output Timing) on page 9.
- **Roles:** the data is launched around the **negative** LLC edge:
  - `t11` = negative clock edge to the start of valid data (Max column);
  - `t12` = end of valid data to the negative clock edge (Max column);
  - the datasheet gives `tSETUP = t10 - t11` and `tHOLD = t9 - t12`, with `t9 : t10` the LLC high/low ratio (45:55 to 55:45).
  The student derives the input delays (data valid window) from these, relative to the falling edge (`-clock_fall`).
- **Watch for:**
  - `t11` and `t12` are alone in their rows. The page text loses the column; `datasheet_page` with `layout: true` shows them under Max.
  - The LLC frequency is not in Table 5. The pin descriptions (pages 12-15) give it: nominally 27 MHz, but varying up or down with the video line length. The clock constraint uses the nominal period; the student notes that it varies.

## clock-si5350c
- **Board:** Si5350C-B02330-GM generates `CLOCK_50`, `CLOCK2_50`, `CLOCK3_50`, `CLOCK4_50` (manual 3.5; sheet 6).
- **Checked datasheet:** Si5350C-B Rev. 1.2: Output Characteristics, Table 7, page 7.
- **Use:** period and cycle-to-cycle jitter of the board clock (`JPER`, `JCC`), depending on the configuration (footnote 3). Optional for the course: the clock constraint (`create_clock -period 20`) and `derive_clock_uncertainty` are enough. Jitter is used only when the student wants to model it, with the value and row cited.

## fpga-cyclone-v
- **Checked datasheet:** Cyclone V Device Datasheet CV-51002, version 2023.05.23 (two identical copies were checked).
- **Use:** not for `set_input_delay` / `set_output_delay` (Quartus models the FPGA). Useful for estimates:
  - pin capacitance, Table 12 on page 17: `CIOTB` and `CIOLR` (6 pF), for the `0.7·R·C` delay of a series resistor;
  - the VCCIO 3.3 V range on page 8.
- **Watch for:** the pages with the most timing words in this datasheet (SPI, SD/MMC, USB, EMAC, Quad SPI timing) belong to the **HPS** (the ARM side), not to the FPGA fabric. They are not used for FPGA constraints.
