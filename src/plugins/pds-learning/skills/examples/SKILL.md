---
name: examples
description: Walk the student through the example code of the PDS video lectures (video-tutorials/) - what each design and architecture does, how it maps to the video, which errors of the video are corrected (NOTE comments), and run it with GHDL like CI. Use when the student wants to study, compare or run an example from a lecture.
---

# Lecture examples

{{include teach-rule}}

## Steps

1. `tutorial_examples` (all lectures) or `tutorial_examples <n>`: the example folder and files of a lecture. The code is on the `main` branch; the tools read it from there, so the student does not need to switch branches.
2. `tutorial_example_read <file>`: read the code with the student. Explain the structure (entity, architectures, configuration), what each architecture shows, and link the part of the video (`topic_get <n> contents` has the timestamps).
3. **Corrections**: lines with `NOTE:` comments correct an error of the video; `video_notes` lists all corrections per topic. Always point them out, so the student does not copy the error from the video.
4. `tutorial_example_run <folder>`: analyses the example and runs its testbenches with GHDL (VHDL-2008, like CI) in a temporary folder. Use it to show that the code works, and to let the student experiment: suggest a change (e.g. remove `else` to see the latch warning, break an expected value to see the testbench fail) that the student makes in their own copy and checks.
5. For synthesis results (RTL Viewer, ALMs, Fmax), the student compiles the example in Quartus; then use the `synthesis` skill of the `pds-design` plugin or explain the reports.

The examples are learning material, not solutions: do not adapt an example into the solution of a graded task.
