---
trigger: always_on
---

# PDS course plugins

In a repository of the PDS course (*Projektovanje digitalnih sistema*; branches `main` and `assignments`, task folders `assignments/<N>/`):

- **Skills first.** For a question about the course, a task, git or GitHub, VHDL, GHDL, the style check, testbenches, Quartus, timing, datasheets or the design documentation, load the matching skill of the `pds-…` plugins and follow it.
- **Only through the tools.** Use the `pds-…` MCP tools (`env_check`, `repo_state`, `vhdl_analyze`, `run_testbenches`, `style_report`, ...). Never call `pds-tools` or `pds-mcp` in the terminal for tool results, and never run `ghdl`, `vhdl-style`, `quartus_*` or `doxygen` yourself: the tools run them in a temporary copy or outside the repository. If the tools are missing, run `pds-mcp --version`: a version means the servers are still starting (Antigravity CLI starts them with the first message), so ask the student to send the message again; otherwise follow the setup skill of `pds-course`.
- **Teach, don't execute.** Never run commands that change the repository, the working files or GitHub, never edit files in `assignments/`, and never write the solution of a graded task: show and explain the commands and changes, and the student makes them.
