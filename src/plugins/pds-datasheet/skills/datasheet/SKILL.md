---
name: datasheet
description: Reads the timing of a component datasheet (PDF) the student provides - finds the timing requirements, switching / AC characteristics and timing diagrams, explains each parameter (clock-to-output, setup, hold, access time, output hold, clock limits), the min/typ/max columns and the test conditions, and helps the student choose the values that match the DE1-SoC board. Strict: every value comes from a datasheet page or the student, a value not found is reported, never invented. The result is a timing card for the timing constraints (pds-quartus constraints skill). Use when the student gives a datasheet, asks where a timing value is in a datasheet, or what a datasheet parameter means.
---

# Timing from a component datasheet

The student learns to find and read the timing of a real component. Show where the information is and what it means, and **let the student choose the values**: which row, which column, min or max. Confirm a correct choice; for a wrong one, point to the column header, the condition or the footnote that decides it. The values end in a **timing card**, from which the student calculates the constraints (pds-quartus `constraints` skill). **Every value comes from the datasheet or the student, with its page; a value you cannot find is reported as not found** (the strict rule below).

Who provides what:
- **On-board devices of the DE1-SoC** (SDRAM, ADC, audio codec, VGA DAC, TV decoder): the parts and connections are in the board facts below. The student provides the datasheet of the exact part on their board.
- **A component the student connects to a GPIO header:** the student finds and provides its datasheet.

## Steps

1. **On-board device?** For a DE1-SoC device, call `board_device_timing` first: how it is connected and clocked, the checked datasheet revision, the pages, the pitfalls.
2. **The exact part.** Ask for the part number and suffix printed on the chip (speed grade, temperature range), or the board revision for an on-board device. On the DE1-SoC the SDRAM part is not named in the board documents, and the ADC differs between board revisions (board facts below). Without the exact part, say which values depend on it and leave them open.
3. **The datasheet.** The student gives the path of the PDF. Datasheets are the vendor's documents: keep them next to the repository, not in it, and cite the title, revision and web address in the design documentation. **Call `datasheet_open`**: title and revision, the bookmarks of the timing sections, the pages with timing tables and diagrams. Check that the datasheet covers the exact part (title, ordering information: `datasheet_search` for the part number); if it does not, say so and ask for the right one. A PDF without text (a scan) cannot be read: ask the student to read the values from it, with the page number.
4. **Which interface.** Ask which pins of the component connect to the FPGA, in which direction, and who drives its clock (its own oscillator, or an FPGA pin). Only the parameters of those pins matter. Show the student the sections and pages (e.g. "6.6 Timing Requirements, page 6; Figure 6-1 timing diagram, page 7") and the diagram that defines the parameters: the edge each one is measured from, and the edge it is measured to.
5. **The tables. Call `datasheet_timing`** for those pages. Explain how the table is built:
   - A page without a ruled table comes back as its text: read the rows from it (symbol, parameter, values in the column order of the header).
   - Rows are the parameters with their symbol, from and to pins, and conditions.
   - Column groups are the supply voltage, temperature range, part or speed grade, and MIN/TYP/MAX.
   - Ask the student which column group fits their setup: VCC = 3.3 V on the DE1-SoC GPIO, the temperature range of the part they have (the suffix of the part number), the load, and the speed grade printed on the chip.
6. **The parameters** (table below): explain each one the student needs in their own words and with the diagram, and ask which role it has in the formulas (the constraints skill's theory).
7. **Check every chosen value on the page** (`datasheet_page`; with `layout: true` a value alone in its row stays under its MIN/TYP/MAX header; `datasheet_search` for a symbol or a footnote):
   - The tables are extracted automatically. A cell with several numbers (`merged_values`) spans merged columns, and only the page shows which ones.
   - Overbars are lost in the extracted text: `Q` and Q̄ (or `CS` and its active-low form) can look the same in two rows. The page shows which row is which.
   - Footnotes change a value: some apply only at another load, or only when the clocks are tied together.
   - The test conditions are in "Parameter Measurement Information" or "Load circuit": the load capacitance (`CL`) and the reference level (`VM`, e.g. VCC/2). A larger real load means a longer delay.
8. **A parameter that is not there.** Search for it (`datasheet_search`: the symbol, its names in the table below, the words of its description) and look at the timing pages. If it is not found, report exactly that: what you searched and where. Then the student finds it another way (strict rule). Do not continue with a guessed value.
9. **The timing card.** When the student has chosen and checked the values, write the card (format below) and continue with the pds-quartus `constraints` skill: the student calculates the input and output delays from the card and the board delays, and writes the SDC. If pds-quartus is not installed, tell the student to install it (`docs/students.en.md`).

## Datasheet names and their role

| Role in the formulas | Names in datasheets | Notes |
| --- | --- | --- |
| `Tco(ext,max)`: clock edge to valid output of the component (for `set_input_delay -max`) | `tCO`, `tCLK-Q`, `tpd` from CLK to Q (logic families), `tAC` (SDRAM access time from the clock), `tV` / `tDOV` / `tSDO` ("SCK to SDO valid", SPI devices), `tD` | Always the MAX column. A memory or ADC lists one per mode or clock frequency (e.g. per CAS latency): use the row of the mode in the design. |
| `Tco(ext,min)`: earliest output change after the edge (for `set_input_delay -min`) | `tpd` MIN, `tOH` (output hold, SDRAM), `tHO` / `tDOH` ("SDO hold after SCK") | Often not given. Only when the MIN column is empty may 0 be proposed (the data may change right at the edge): marked "assumed", and the student decides. |
| `Tsetup(ext)`: data before the component's clock edge (for `set_output_delay -max`) | `tSU`, `tS`, `tDS` (data), `tAS` (address), `tCMS` (command), `tSUDI` | MIN column: the component needs at least this. |
| `Thold(ext)`: data after the component's clock edge (for `set_output_delay -min`) | `tH`, `tHD`, `tDH`, `tAH`, `tCMH` | MIN column. A hold time of 0 still enters the formula. |
| Clock limits: the clock the design gives the component | `fCLK` / `fmax` / `fSCK` max, `tCK` / `tCYC` min (period), `tCH` / `tCL` / `tw` (high and low pulse width) | A check of the design (clock divider, PLL), not an SDC value. |
| Not for the SDC, but for the design | `tCONV` (ADC conversion), `tRCD` / `tRP` / `tREF` (SDRAM commands, refresh), `tw` of reset, `tPZH` / `tPZL` / `tdis` (output enable and disable of a bus) | Clock cycles the state machine must wait: count them with the clock period. |
| Never used | TYP values, `tr` / `tf` / `tt` (edge transition times) | TYP is a typical part, not a guarantee. Transition times are part of how the delays are measured. |

- A missing MIN or MAX means the vendor guarantees nothing on that side. Say so in the card. A safe value is allowed only where the strict rule names one; every other missing value stays open.
- Some datasheets give a value only for one supply voltage or one temperature. The card notes the condition.

## Timing card (format)

```
Timing card: <part number> - <datasheet title, revision>, interface <pins to the FPGA>
Clock of the component: <own oscillator f = ... | FPGA pin <name>>; conditions: VCC = 3.3 V, <temperature range>, CL = <pF>
| Role         | Datasheet parameter     | Value   | Where              | Note                     |
| Tco(ext,max) | tpd CLK->Q, MAX         | 5.9 ns  | p. 7, 6.7 Switching|                          |
| Tco(ext,min) | tpd CLK->Q, MIN         | 2.2 ns  | p. 7, 6.7 Switching|                          |
| Tsetup(ext)  | tsu Data                | 1.3 ns  | p. 7, 6.6 Timing   |                          |
| Thold(ext)   | th                      | 1.2 ns  | p. 7, 6.6 Timing   |                          |
| Clock limit  | fmax                    | 175 MHz | p. 7, 6.7 Switching| the design's clock must be lower |
| Condition    | CL, test load           | 50 pF   | p. 9, Figure 7-1   | load of the values above |
| Not found    | <symbol>                | open    | searched: <pages, terms> | the student looks for it: <where> |
```

The values above only show the format (SN74LVC1G74 at 3.3 V, -40 to 85 °C). Never put them, or any value not read from the student's datasheet, into a card.

{{include datasheet-rule}}

{{include board-timing}}

{{include teach-rule}}

{{include course-context}}
