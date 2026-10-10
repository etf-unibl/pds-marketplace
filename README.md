# PDS marketplace

AI assistant plugins of the course *Projektovanje digitalnih sistema* (PDS), Faculty of Electrical Engineering, University of Banja Luka, for **Claude Code**, **GitHub Copilot CLI** and **Antigravity CLI**.

**Students:** installation and use — [srpski](docs/students.sr.md) · [English](docs/students.en.md)

The student plugins teach the course workflow instead of doing it: they never run commands that change the repository or GitHub, and never edit graded work. For every such step they show the command, explain it, say how to check the result and how to undo it.

## Plugins

| Plugin | For | Purpose |
| ------ | ------ | ------ |
| `pds-course` | students | setup check, task context, submission, failed checks, time tracking |
| `pds-git` | students | git coach: branches, commits, push, merge conflicts, fixing mistakes |
| `pds-design` | students | design review: style, synthesis warnings, DE1-SoC pins |
| `pds-testing` | students | testbenches and running them like the course CI |
| `pds-learning` | students | tutor with the course topic pages, video moments, examples, glossary and self-check quiz |
| `pds-quartus` | students and staff | Intel Quartus Prime from the command line: project for a design (DE1-SoC, VHDL-2008, pins, clock constraint), synthesis and full compilation, timing analysis and closure, timing constraints (SDC) the student calculates and writes, Tcl, programming the board |
| `pds-template`, `pds-admin`, `pds-assignments`, `pds-verification`, `pds-review`, `pds-materials` | course staff | instructor plugins; their files are in a private repository, so only the course staff can install them |

Add the marketplace once and install plugins by name, e.g. in Claude Code:

```
/plugin marketplace add etf-unibl/pds-marketplace
/plugin install pds-learning@pds-marketplace
```

## Repository

| Folder | Contents |
| ------ | ------ |
| `docs/` | user documentation (students) |
| `tools/pds-tools` | Python package with the read-only tools and the MCP server (`pds-mcp --profile <plugin>`) |
| `src/` | skills, guard hook and shared texts of the plugins (hand-edited); `src/marketplace/` lists the instructor plugins |
| `build/` | generator of the plugin packages and the marketplace catalogs |
| `plugins/` | generated plugin packages (Claude Code, Copilot CLI and Antigravity CLI in one folder each) |
| `.claude-plugin/marketplace.json`, `.github/plugin/marketplace.json` | the catalog for Claude Code and for Copilot CLI (Copilot does not accept `git-subdir` sources) |
| `evals/` | scenario tests of the plugins with the real AI tools |

Development: edit `src/`, run `python build/build.py`, test with `python -m pytest` in `tools/pds-tools` and the evals; CI checks that the generated files are current. Releases of `pds-tools` are tagged `v<version>`; the student guides install from the tag.

## License

MIT
