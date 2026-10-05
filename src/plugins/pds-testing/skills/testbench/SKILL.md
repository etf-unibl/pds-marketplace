---
name: testbench
description: Teach the student how to write a self-checking VHDL testbench for a PDS task - structure, stimulus and checks with assert/severity error, test vector tables (records), procedures, file-based vectors (textio), clock and reset, ending the simulation - following topics 6, 12 and 15 of the course. Use when the student writes or asks about a testbench.
---

# Writing a testbench

{{include teach-rule}}

{{include course-context}}

The testbench is part of the student's work: teach the patterns and review their testbench; do not write the testbench of a graded task for them. Small examples that are not the task itself are fine, best taken from the course examples (`tutorial_examples 6`, `12`, `15`).

## What CI expects (`testbench` job)

- file `assignments/<N>/<name>_tb.vhd` with entity `<name>_tb` (same name as the file), no ports;
- failures reported with `assert <condition> report "..." severity error;` (a `note` or `warning` does not fail the job);
- the simulation ends by itself: stop the clock after the last test and end the stimulus process with `wait;` (otherwise it is stopped after 10 ms);
- VHDL-2008 (`ghdl --std=08`).

## Patterns to teach (with the topic that explains them)

| Pattern | Topic |
| ------ | ------ |
| UUT instance, stimulus process, `wait for`, `assert ... severity error`, checking after the outputs settle | 6 (`topic_get 6 explanation`) |
| test vector table: `record` + array constant, loop over `'range` | 12 |
| clock process, reset pulse `reset <= '1', '0' after T/2;`, writing results to a file (`std.textio`) | 12 |
| procedures that wrap a transaction (`writemem`, `readmem`), checking the output (not the input) at the right time | 15 |

## Review checklist for the student's testbench

- every expected value is checked with `severity error`, and the check compares the design **output**;
- checks happen after the output settles (after the clock edge or delay), not at the same instant as the input change;
- all relevant input combinations or cases of the specification are covered (suggest missing ones);
- the simulation stops by itself.

Then run it with the `run` skill. A good test also fails for a broken design: suggest the student breaks the design on purpose once and sees the testbench report it.
