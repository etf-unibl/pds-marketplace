---
name: pins
description: Help the student connect a PDS design to the DE1-SoC board - pin names and locations (SW, KEY, LEDR, HEX0-5, CLOCK_50, GPIO), checking the top-level ports against the course pin file, active-low buttons and displays, importing assignments and programming the board. Use when the student asks about pins, the board, Pin Planner or why the design does not react on the board.
---

# DE1-SoC pins and board testing

{{include teach-rule}}

## Facts (course pin file DE1_SoC_pin_assigments.csv, video tutorials 4 and 7)

- Device 5CSEMA5F31C6. `board_pins` lists signals, pins, directions and notes; filter by `SW`, `KEY`, `LEDR`, `HEX0`, `CLOCK_50`, `GPIO_0`, ...
- `KEY` buttons are active low (pressed = `'0'`); `HEX` segments are active low (lit for `'0'`), index 0..6 = segments a..g; `CLOCK_50` is 50 MHz.
- Ports connect to the board only when their names match the file (`SW`, `KEY`, `LEDR`, `HEX0`), and a board signal named `LEDR[0]` needs a vector port (`std_logic_vector(0 downto 0)`), not `std_logic`.

## Steps

1. `pin_check <top-level VHDL file>`: which port bits have a pin, which do not, and direction or vector problems. Explain each problem and show the corrected port declaration; the student edits the file. Keep the logic in internal signals and connect them to the board ports (topic 7 shows `a <= SW; LEDR(0) <= even;`).
2. Assigning pins - two ways, both done by the student:
   - recommended: Quartus **Assignments > Import Assignments** with the course CSV file (`video-tutorials/part-2/video-tutorial-07/` on `main`);
   - or `pin_plan <file>` gives `set_location_assignment` lines for the `.qsf` file, or the student enters them in **Assignments > Pin Planner**.
   Then recompile (pin assignments apply only after compilation) and check *Fitter Location* in the Pin Planner.
3. Programming: **Tools > Programmer**, hardware *DE-SoC*, JTAG, **Auto Detect**, choose 5CSEMA5, add the `.sof` file, tick **Program/Configure**, **Start** (topic 4, `topic_get 4`).
4. Nothing happens on the board: check the active-low logic, the switch for the programming mode, unassigned pins (Quartus places them anywhere; see the pin warnings), and a missing clock assignment.
