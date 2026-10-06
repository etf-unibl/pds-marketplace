---
name: tcl
description: Helps write, explain and run Tcl scripts for Intel Quartus Prime (quartus_sh, quartus_sta) in the PDS course - project setup and settings, pin and I/O assignments, SDC timing constraints, custom timing reports, batch flows - and runs them in the Quartus project folder after confirmation. Use when the student or instructor asks about Quartus Tcl, scripting, automating Quartus or SDC constraints.
---

# Quartus Tcl

## Steps

1. Find out the goal (a setting, assignments for many pins, a constraint, a report, a repeatable flow) and the tool it needs:
   - `quartus_sh -t` - project and assignments: `project_open`/`project_new`, `set_global_assignment -name ...`, `set_location_assignment PIN_.. -to <port>`, `set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to <port>`, `export_assignments`, `project_close`; flows with `load_package flow` and `execute_flow -compile`;
   - `quartus_sta -t` - timing: `project_open`, `create_timing_netlist`, `read_sdc`, `update_timing_netlist`, `report_timing`, `create_timing_summary`, `report_clock_fmax_summary`;
   - SDC (the `.sdc` file, read by the fitter and the timing analyzer): `create_clock -period 20.0 [get_ports CLOCK_50]`, `derive_clock_uncertainty`, `set_input_delay` / `set_output_delay`, `set_false_path`.
   The project skill's `create_project.tcl` and the timing skill's `pds_timing.tcl` in the project folder are working examples to start from.
2. Write the script with a comment per block, explain every command and its options, and say what output to expect.
3. Run it only when the student or instructor wants: **`quartus_tcl`** (file or text, `tool: quartus_sh|quartus_sta`, `project_dir`). Running a script asks for confirmation every time, because a script can change the project. It runs in the project folder outside the repository; for a script that changes the project, suggest keeping a copy of the `.qsf` first.
4. Read the output with the user; for errors, explain the Tcl or Quartus message and correct the script. Show how to run the same by hand: `quartus_sh -t <script>.tcl` in the project folder.

Tcl scripts are not part of the submission: the course `.gitignore` ignores `*.tcl` in the repository, and the project folder is outside it.

{{include teach-rule}}

{{include course-context}}
