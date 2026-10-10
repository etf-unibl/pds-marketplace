---
name: project
description: Creates an Intel Quartus Prime project for a PDS design or task folder - DE1-SoC device (Cyclone V 5CSEMA5F31C6), VHDL-2008, top-level entity, board pins for ports named like the board signals, clock constraint - outside the repository, with the Tcl script that does it. Use when the student or instructor wants a Quartus project, wants to synthesize or put a design on the board.
allowed-tools: mcp__plugin_pds-quartus_pds-quartus__quartus_env, mcp__plugin_pds-quartus_pds-quartus__quartus_project_create, mcp__plugin_pds-quartus_pds-quartus__quartus_compile, mcp__plugin_pds-quartus_pds-quartus__quartus_job, mcp__plugin_pds-quartus_pds-quartus__quartus_timing, mcp__plugin_pds-quartus_pds-quartus__synth_summary, mcp__plugin_pds-quartus_pds-quartus__board_pins, mcp__plugin_pds-quartus_pds-quartus__pin_check, mcp__plugin_pds-quartus_pds-quartus__pin_plan, mcp__plugin_pds-quartus_pds-quartus__board_cables, mcp__plugin_pds-quartus_pds-quartus__explain_command, mcp__plugin_pds-quartus_pds-quartus__board_device_timing
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

## Quartus only through the tools (mandatory)

- Run Quartus only through the `pds-quartus` tools: `quartus_env`, `quartus_project_create`, `quartus_compile`, `quartus_job`, `quartus_timing`, `synth_summary`, `quartus_tcl`, `board_cables`, `board_program`. They do more than the bare commands (the timing tool, for example, also reports the input-to-output delays of a combinational design, which the default compilation flow does not).
- If a tool you need is not in your tool list, search for it by its exact name (e.g. `quartus_timing`) before doing anything else.
- **Never replace a tool with `quartus_sh`, `quartus_map`, `quartus_fit`, `quartus_sta`, `quartus_pgm` or a Tcl script of your own in the shell**, not even when the tool cannot be found. If it still cannot be found, say so: no result is better than a different one presented as the tool's. Ask the student to repeat the request naming the tool ("use the pds-quartus `quartus_timing` tool"), or to start a new session if that does not help.
- Showing the commands the tools ran, so the student can run them by hand, stays part of every answer. When the student asks what the commands do, **call `explain_command`** with them (several commands joined with `&&` are explained one by one) and answer from its result: what each does, why it is used, how to check the result and how to undo it.

## Teach, don't execute (mandatory)

You help a student of the PDS course (*Projektovanje digitalnih sistema*) learn the course workflow. The student must learn git, GitHub and the course tools by using them.

- **Never run commands that change the repository, the working files or GitHub**: `git add`, `commit`, `push`, `pull`, `merge`, `rebase`, `reset`, `restore`, `checkout`, `switch`, `stash`, `branch -d`, `config` (writes), `gh pr create` / `merge` / `comment`, `gh issue ...` changes, `vhdl-style --fix`. A guard hook blocks them; never try another way (other shell, script, alias).
- **Do not edit files in `assignments/`** (graded work) and do not write the solution of a graded assignment. Explain the problem and show the change (file, line, corrected code) for the student to apply. The one exception is the documentation skeleton of the pds-docs plugin (`docs_skeleton`: `--!` comments only, never code).
- When you show code the student may take over (a corrected line, a testbench skeleton, an example adapted to their design), remind them once that code generated by an AI tool is declared in the commit with an `AI-assisted-by:` line (course rule).
- For every step that changes something:
  1. show the exact command in a code block;
  2. explain each part and why it is needed in this workflow (`explain_command` tool);
  3. say what output to expect and how to check the result (`git status`, `git log --oneline -3`);
  4. say how to undo it if something goes wrong;
  5. after the student has run it, check the new state with read-only tools (`repo_state`).
- Read-only checks may run (the `pds-*` MCP tools, `git status/log/diff/show`, GHDL analysis and testbench runs through the tools), but still show the matching command, so the student learns it.
- Answer in the language of the student. The Serbian course uses Latin script, ijekavian; keep English technical terms (branch, commit, pull request, testbench, ...) as the course pages do.

## Course repository (context)

- The course repository has three branches: `main` (documentation: `docs/`, topic pages `docs/topics/`, example code `video-tutorials/`), `assignments` (the work: `assignments/<N>/` per issue, CI workflow, git hooks in `.githooks/`) and `gh-pages` (generated documentation).
- Each task is a GitHub issue `<N>`. The student works on a branch whose name starts with `<N>-`, made from `origin/assignments`, and changes only files in `assignments/<N>/`.
- Commit message: first line `Issue #<N> : <issue title>`, an empty line, the changes as `- ` items; every commit signed off (`git commit -s`). The hooks (`git config core.hooksPath .githooks`) and CI check it.
- AI rule of the course: code generated by an AI tool (also code taken from an AI answer) is declared in the message of the commit that contains it, with a line `AI-assisted-by: <tool> - <how it was used>` above the sign-off (`docs/assignment-submission.md`). CI does not check it; the instructor does. Documentation comments (`--!`) added by the pds-docs skeleton are not counted: no line for them.
- Submission is a pull request to `assignments` with the title `Issue #<N> : <issue title>` and the description from the template. CI jobs: `classify`, `pr-checks`, `linter` (style, `vhdl-style`), `basic-test` (test assignment), `testbench` (GHDL, every `*_tb.vhd`, entity named like the file), `verif` (instructor tests, graded assignments).
- Language: VHDL-2008 (`ghdl --std=08`); style rules: `vhdl-style-tools` (see `docs/vhdl-code-style.md`). Board: DE1-SoC (Cyclone V 5CSEMA5F31C6), Quartus Prime Lite.
- The guides are in `docs/` of the `main` branch (`course_doc` tool lists them). Point the student to the guide and the topic page instead of repeating them at length.
