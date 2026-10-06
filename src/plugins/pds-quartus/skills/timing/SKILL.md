---
name: timing
description: Timing analysis and timing closure of a PDS design with Quartus (TimeQuest, quartus_sta) - setup and hold slack per clock over all corners, Fmax, the worst paths, unconstrained paths and missing constraints - and how to fix failing paths (constraints, pipelining, restructuring logic, register balancing). Use when the student asks about timing, Fmax, slack, critical paths or the timing analysis lecture.
---

# Timing analysis and closure

## Steps

1. The project must be fully compiled (`compile` skill, `flow: "full"`).
2. **Call `quartus_timing`** (it writes `pds_timing.tcl` in the project folder and runs `quartus_sta -t pds_timing.tcl`).
3. Read the result with the student:
   - **setup slack** (worst over the corners) and **TNS**: negative = a path is too slow for the clock period; **hold slack** negative = data changes too early (rare in a single-clock synchronous design; usually a constraint or clock problem);
   - **Fmax** per clock: the highest clock frequency the design meets (restricted Fmax includes device limits); compare with the constraint (50 MHz = 20 ns for `CLOCK_50`);
   - **worst paths**: `from_node` → `to_node`, data delay, clock skew: which logic between which registers is the critical path;
   - **unconstrained paths / check_timing**: a clock without `create_clock`, inputs and outputs without delays; a combinational design has no clock, so there is nothing to time unless a constraint is added.
4. **Closing timing** (explain, the student changes the VHDL): shorten the critical path - pipelining (registers between stages, more latency: lecture 14 `docs/topics/14-pipelining.md`), restructuring arithmetic or decision logic (fewer logic levels, shared operators, balanced trees: lecture 8), registering inputs and outputs, a relaxed or corrected constraint only when the requirement allows it. The timing lecture is `docs/topics/13-timing-analysis.md`.
5. Show the Tcl the tool used (`create_timing_netlist`, `read_sdc`, `update_timing_netlist`, `create_timing_summary`, `report_timing -setup -npaths 10 -detail summary`, `report_clock_fmax_summary`) and how to open the same reports in the GUI (**Tools > Timing Analyzer**), so the student can repeat the analysis.

{{include teach-rule}}

{{include course-context}}
