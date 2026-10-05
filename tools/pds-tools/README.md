# pds-tools

Read-only helpers and the MCP server behind the AI plugins of the PDS course (*Projektovanje digitalnih sistema*, Faculty of Electrical Engineering, University of Banja Luka).

The package never changes the course repository or GitHub. It reads the git state, the course documents and Quartus reports, analyses VHDL with GHDL in a temporary library and checks texts against the course rules. Commands that change state are only explained.

| Module | Contents |
| ------ | ------ |
| `rules` | submission rules, the same as the CI check (`pr_rules.py`) and the git hooks |
| `repo` | read-only git state of the working copy |
| `github` | read-only GitHub access: issue context, pull request checks and CI annotations |
| `hdl` | GHDL analysis (VHDL-2008), testbench runs like CI, `vhdl-style` without `--fix` |
| `quartus` | summaries of existing Quartus reports (warnings, resources, timing) |
| `pins` | DE1-SoC pin table and checks of top-level ports |
| `topics` | topic pages, glossary, self-check questions and example code of the course repository |
| `explain` | explanations of the commands of the course workflow (Serbian and English) |
| `env` | check of the student's tools and git setup |

## Usage

```
pds-mcp --profile git          # MCP server (stdio) with the tools of one plugin
pds-mcp --list                 # profiles and tools
pds-tools topics_search latch  # the same tools from the command line, JSON output
```

Profiles: `course`, `git`, `design`, `testing`, `learning` (and `all`).

## Requirements

- Python 3.10 or newer, run inside the course repository
- `git`; GHDL for the VHDL tools; `vhdl-style` (course `requirements.txt`) for the style check; optional `gh` for GitHub access with your login
