---
name: program
description: Programs the DE1-SoC board with a compiled PDS design (.sof over JTAG with the USB-Blaster) and helps when the board is not found - cable, power, driver, JTAG chain - and with testing the design on the board (switches, keys, LEDs, 7-segment displays). Use when the student wants to put the design on the board or the Programmer does not see it.
---

# Programming the DE1-SoC

## Steps

1. The design needs a full compilation (`compile` skill, `flow: "full"`) with every top-level port pinned (`pin_check`; the `project` skill assigns pins to ports named like the board signals). Unpinned outputs drive random pins: do not program a design with missing pins.
2. **`board_cables`**: is the USB-Blaster seen? If not: board switched on, USB cable in the USB-Blaster port (next to the power connector), USB-Blaster driver installed (`docs/tools-setup.md`, `<quartus>/drivers/usb-blaster` or `usb-blaster-ii`), on Linux the udev rule; check again.
3. **`board_program`** with `output_files/<top>.sof` (asks for confirmation). On the DE1-SoC the FPGA is the second device of the JTAG chain (after the HPS ARM), so the tool programs device 2. Programming is volatile: the design is lost when the board is switched off.
4. Test on the board with the student: which switch drives which signal, which LED or display shows what (`board_pins` lists the names and pins; KEY buttons are active-low, the 7-segment segments are active-low). Show the GUI path too: **Tools > Programmer**, **Hardware Setup**: USB-Blaster, **Auto Detect**, select the 5CSEMA5 device, add the `.sof`, **Start**; and the command `quartus_pgm -c "<cable>" -m JTAG -o "p;output_files/<top>.sof@2"`.
5. Behaviour differs from the simulation: check the pins and active levels first, then reset and clock (`CLOCK_50`), then latches and timing warnings of the compilation (`compile`, `timing` skills).

{{include quartus-tools-rule}}

{{include teach-rule}}

{{include course-context}}
