---
name: run
description: Run the testbenches of a PDS task exactly like the course CI (GHDL, VHDL-2008) and explain the results - compile errors, failed assertions, simulations stopped after 10 ms, files written by the testbench, waveforms. Use when the student wants to test their design or the testbench job failed.
---

# Running testbenches like CI

{{include teach-rule}}

{{include course-context}}

## Steps

1. `list_testbenches assignments/<N>`: each `*_tb.vhd` and whether the entity is named like the file (CI requirement).
2. `run_testbenches assignments/<N>`: runs in a temporary copy with the same GHDL commands as CI and returns, per testbench, pass/fail, the stage (compile or run), the messages with file and line, files the testbench wrote and the commands. Show the student the commands so they can run them too:

```
ghdl -i --std=08 *.vhd
ghdl -m --std=08 <name>_tb
ghdl -r --std=08 <name>_tb --stop-time=10ms --assert-level=error --wave=<name>_tb.ghw
```

3. Explain the results:
   - **compile errors**: read the GHDL message (file:line:column) and explain it; `vhdl_analyze` on single files helps;
   - **assertion error**: the message, the simulation time and what the testbench expected; then help find whether the design or the testbench is wrong (re-read the specification);
   - **stopped by --stop-time**: the clock or stimulus never stops; add `wait;` and stop the clock;
   - **unbound component** warnings: the component name or ports do not match the entity.
4. Waveforms: the student adds `--wave=<name>_tb.ghw` and opens the file in GTKWave, or simulates in ModelSim/Questa (`docs/simulation-and-testing.md`). Explain which signals to look at.

Never change the student's files; explain the fix.
