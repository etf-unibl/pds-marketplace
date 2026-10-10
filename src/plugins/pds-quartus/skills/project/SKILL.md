---
name: project
description: Creates an Intel Quartus Prime project for a PDS design or task folder - DE1-SoC device (Cyclone V 5CSEMA5F31C6), VHDL-2008, top-level entity, board pins for ports named like the board signals, clock constraint - outside the repository, with the Tcl script that does it. Use when the student or instructor wants a Quartus project, wants to synthesize or put a design on the board.
---

# Quartus project

## Steps

1. `quartus_env`: Quartus found, version, Cyclone V support. If missing, point to `docs/tools-setup.md` (Quartus Prime Lite with Cyclone V, `quartus/bin64` on `PATH`).
2. Sources: the task folder `assignments/<N>` or the VHDL files (testbenches `*_tb.vhd` are left out automatically). Top-level entity: detected (the entity no other file instantiates); ask when it is ambiguous.
3. **Call `quartus_project_create`** with the sources (and `top` if needed); **leave `project_dir` out**, so the project gets the default folder, unless the student asks for another folder outside the repository. It keeps the project **outside the repository** (course rule, `docs/simulation-and-testing.md`): by default `<repository>-quartus/<task>-<top>` next to the repository, so generated files never end up in a commit. It refuses a folder inside the repository. Pins: ports named like board signals (`SW`, `KEY`, `LEDR`, `HEX0`..`HEX5`, `CLOCK_50`, `GPIO_0/1`) get their pins and 3.3-V LVTTL; report `ports_without_pin` (fine for an internal block; the top level on the board needs every port pinned, see `pin_check` / `pin_plan` and the board names in `board_pins`). Clock: a port named like `CLOCK_50`/`clk` gets `create_clock` at `clock_mhz` (50 MHz = the board oscillator).
4. Show the student the generated `create_project.tcl` and explain the lines that matter (`set_global_assignment -name DEVICE/TOP_LEVEL_ENTITY/VHDL_INPUT_VERSION/VHDL_FILE/SDC_FILE`, `set_location_assignment PIN_.. -to SW[0]`, `IO_STANDARD`, `ADVANCED_PHYSICAL_OPTIMIZATION OFF`, which saves minutes of Fitter time on a small design): the same project can be made by hand with **File > New Project Wizard**, or again from the script with `quartus_sh -t create_project.tcl`.
5. Next step: the `compile` skill. The VHDL files stay where they are; the project only references them, so edits in `assignments/<N>` are picked up by the next compilation.

## Notes

- The project folder is the student's own working folder outside the repository; creating and compiling there does not change the repository. Edits of the VHDL files in `assignments/` remain the student's (graded work).
- Pass only the sources (and `top` when it is ambiguous). **Do not pass `overwrite` or `assign_pins` unless the student asked**: `overwrite: true` re-creates an existing project and discards the assignments made in it since (pins, settings); if the project exists, say so and ask, or compile it as it is.
- For a different board or device pass the device and leave pins to the student (`assign_pins: false`).
- The generated `<top>.sdc` has the clock of the design (a board fact) and commented templates of the constraints the student adds and calculates; point to the `constraints` skill. On a re-created project an edited SDC is kept (`sdc_kept`, template in `<top>.sdc.new`).

{{include quartus-tools-rule}}

{{include teach-rule}}

{{include course-context}}
