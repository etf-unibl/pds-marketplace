# PDS plugins

AI assistant plugins for students of the course *Projektovanje digitalnih sistema* (PDS), Faculty of Electrical Engineering, University of Banja Luka, for Claude Code, GitHub Copilot and Gemini CLI.

The plugins teach the course workflow instead of doing it: they never run commands that change the repository or GitHub (git commits, pushes, pull requests, `vhdl-style --fix`). For every such step they show the command, explain it, say how to check the result and how to undo it, and then check the result with read-only tools.

> Work in progress. Installation and usage will be documented after the pilot.

## Contents

| Folder | Contents |
| ------ | ------ |
| `tools/pds-tools` | Python package with the read-only tools and the MCP server (`pds-mcp --profile <plugin>`) |
| `src/` | skills, agents and hooks of the plugins (hand-edited) |
| `build/` | generator of the plugin packages for each AI tool |
| `plugins/` | generated plugin packages |
| `evals/` | test scenarios of the plugins |

## Plugins

| Plugin | Purpose |
| ------ | ------ |
| `pds-course` | course workflow: onboarding, task context, pull request description, failed checks |
| `pds-git` | git coach: branches, commits, push, merge conflicts, fixing mistakes |
| `pds-design` | design review: style, synthesis warnings, timing, DE1-SoC pins |
| `pds-testing` | testbenches and running them like the course CI |
| `pds-learning` | learning with the course topic pages, examples, glossary and self-check questions |

## License

MIT
