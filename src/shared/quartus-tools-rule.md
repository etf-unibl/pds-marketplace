## Quartus only through the tools (mandatory)

- Run Quartus only through the `pds-quartus` tools: `quartus_env`, `quartus_project_create`, `quartus_compile`, `quartus_job`, `quartus_timing`, `synth_summary`, `quartus_tcl`, `board_cables`, `board_program`. They do more than the bare commands (the timing tool, for example, also reports the input-to-output delays of a combinational design, which the default compilation flow does not).
- If a tool you need is not in your tool list, search for it by its exact name (e.g. `quartus_timing`) before doing anything else.
- **Never replace a tool with `quartus_sh`, `quartus_map`, `quartus_fit`, `quartus_sta`, `quartus_pgm` or a Tcl script of your own in the shell**, not even when the tool cannot be found. If it still cannot be found, say so: no result is better than a different one presented as the tool's. Ask the student to repeat the request naming the tool ("use the pds-quartus `quartus_timing` tool"), or to start a new session if that does not help.
- Showing the commands the tools ran, so the student can run them by hand, stays part of every answer.
