# pds-tools

Helpers and the MCP server behind the AI plugins of the PDS course (*Projektovanje digitalnih sistema*, Faculty of Electrical Engineering, University of Banja Luka).

The package does not change the course repository or GitHub. It reads the git state, the course documents and Quartus reports, analyses VHDL with GHDL in a temporary library and checks texts against the course rules. Commands that change state are only explained. Two exceptions write files: the Quartus tools write the Quartus project outside the repository, and `docs_skeleton` adds documentation comments (`--!`, never code) to a design file when the student confirms it.

| Module | Contents |
| ------ | ------ |
| `rules` | submission rules, the same as the CI check (`pr_rules.py`) and the git hooks |
| `repo` | read-only git state of the working copy |
| `github` | read-only GitHub access: issue context, pull request checks and CI annotations |
| `hdl` | GHDL analysis (VHDL-2008), testbench runs like CI, `vhdl-style` without `--fix` |
| `quartus` | summaries of existing Quartus reports (warnings, resources, timing) |
| `quartus_run` | Quartus projects outside the repository, compilation, timing analysis, Tcl, programming the board |
| `pins` | DE1-SoC pin table and checks of top-level ports |
| `datasheet` | timing tables and pages of component datasheets (PDF), notes on the DE1-SoC devices |
| `docs` | Doxygen documentation of designs: outline, review against the course requirements and Doxygen's pitfalls, skeleton (comments only), local HTML preview |
| `topics` | topic pages, glossary, self-check questions and example code of the course repository |
| `explain` | explanations of the commands of the course workflow (Serbian and English) |
| `env` | check of the student's tools and git setup |

## Usage

```
pds-mcp --profile git          # MCP server (stdio) with the tools of one plugin
pds-mcp --list                 # profiles and tools
pds-tools topics_search latch  # the same tools from the command line, JSON output
```

Profiles: `course`, `git`, `design`, `testing`, `learning`, `quartus`, `datasheet`, `docs` (and `all`).

## Requirements

- Python 3.10 or newer, run inside the course repository
- `git`; GHDL for the VHDL tools; `vhdl-style` (course `requirements.txt`) for the style check; optional `gh` for GitHub access with your login
- Quartus Prime Lite for the `quartus` profile; Doxygen for the documentation preview (`docs_preview`; GitHub Pages uses 1.9.5)
