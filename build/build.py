#!/usr/bin/env python3
"""Generates the plugin packages from src/.

    python build/build.py            # write plugins/, .claude-plugin/marketplace.json and build/out/gemini/
    python build/build.py --check    # fail if the committed files are not up to date (CI)

Sources (hand-edited):
  src/shared/teach-rule.md, course-context.md,
  quartus-tools-rule.md                         included in skills with {{include <name>}}
  src/shared/guard.py                           hook script (Claude Code, Copilot CLI)
  src/plugins/<plugin>/plugin.json              name, displayName, description, profile, keywords
  src/plugins/<plugin>/skills/<skill>/SKILL.md  skills

Output:
  plugins/<plugin>/                 one folder for Claude Code (.claude-plugin/, hooks/, .mcp.json), Copilot CLI
                                    (plugin.json, copilot/) and Antigravity CLI (plugin.json, mcp_config.json,
                                    hooks.json), shared skills/ and scripts/
  .claude-plugin/marketplace.json   marketplace (Claude Code and Copilot CLI)
  build/out/gemini/<plugin>/        Gemini CLI extensions (published to branches gemini/<plugin> by CI)
"""

import json
import os
import re
import shutil
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "src")
VERSION = "0.1.9"
REPO = "https://github.com/etf-unibl/pds-marketplace"
AUTHOR = {"name": "Faculty of Electrical Engineering, University of Banja Luka", "url": "https://github.com/etf-unibl"}
MARKETPLACE = "pds-marketplace"

# Commands the Gemini policy denies (Claude Code and Copilot use guard.py, which classifies every command)
DENIED_PREFIXES = [
    "git add", "git commit", "git push", "git pull", "git merge", "git rebase", "git reset", "git restore", "git checkout",
    "git switch", "git stash", "git cherry-pick", "git revert", "git rm", "git mv", "git clean", "git tag", "git am",
    "git apply", "git clone", "git init", "git branch -d", "git branch -D", "git branch -m", "git branch -M",
    "git config --global", "git config user", "git config core", "git config --unset", "git remote add", "git remote remove",
    "git remote set-url", "gh pr create", "gh pr merge", "gh pr close", "gh pr edit", "gh pr comment", "gh pr review",
    "gh pr ready", "gh issue create", "gh issue edit", "gh issue close", "gh issue comment", "gh repo", "gh api -X",
    "gh api --method", "vhdl-style --fix",
]

# Antigravity CLI: hooks.json in the plugin root, command run in the plugin folder (sh -c / cmd /c)
AGY_MATCHER = ("run_command|shell_exec|send_command_input|write_to_file|replace_file_content|multi_replace_file_content|"
               "edit_notebook|file_change|write_blob|delete_directory|move|git_commit")
AGY_GUARD = "python3 scripts/guard.py agy || python scripts/guard.py agy || py scripts/guard.py agy"

GUARD_CMD = ('for p in python3 python py; do if "$p" -c "" >/dev/null 2>&1; then exec "$p" "${ROOT}/scripts/guard.py" CLIENT; fi; done; exit 0')


def read(path):
    with open(path, encoding="utf-8") as f:
        return f.read()


def render(text):
    def include(m):
        return read(os.path.join(SRC, "shared", m.group(1) + ".md")).strip()
    return re.sub(r"\{\{include ([\w-]+)\}\}", include, text)


def plugins():
    base = os.path.join(SRC, "plugins")
    for name in sorted(os.listdir(base)):
        meta = json.loads(read(os.path.join(base, name, "plugin.json")))
        meta["dir"] = os.path.join(base, name)
        yield meta


def mcp_servers(profile):
    return {f"pds-{profile}": {"command": "pds-mcp", "args": ["--profile", profile]}}


def build_files():
    """All generated files as {relative path: content}."""
    files = {}
    entries = []
    for p in plugins():
        name, out = p["name"], f"plugins/{p['name']}"
        skills = []
        for skill in sorted(os.listdir(os.path.join(p["dir"], "skills"))):
            text = render(read(os.path.join(p["dir"], "skills", skill, "SKILL.md")))
            # the plugin's own MCP tools are read-only: allow them without a prompt (Claude Code permission rule
            # for all tools of the server; other AI tools ignore the field)
            # a plugin whose tools also act (run a Tcl script, program the board) lists the tools that need no
            # confirmation in "auto_approve"; the others ask every time
            allowed = (", ".join(f"mcp__plugin_{name}_pds-{p['profile']}__{t}" for t in p["auto_approve"])
                       if p.get("auto_approve") else f"mcp__plugin_{name}_pds-{p['profile']}__*")
            text = text.replace("\n---\n", f"\nallowed-tools: {allowed}\n---\n", 1)
            files[f"{out}/skills/{skill}/SKILL.md"] = text
            skills.append(skill)
        files[f"{out}/scripts/guard.py"] = read(os.path.join(SRC, "shared", "guard.py"))
        files[f"{out}/.claude-plugin/plugin.json"] = dump({
            "name": name, "displayName": p["displayName"], "version": VERSION, "description": p["description"],
            "author": AUTHOR, "homepage": REPO, "repository": REPO, "license": "MIT", "keywords": p["keywords"]})
        files[f"{out}/.mcp.json"] = dump({"mcpServers": mcp_servers(p["profile"])})
        files[f"{out}/hooks/hooks.json"] = dump({"hooks": {"PreToolUse": [{
            "matcher": "Bash|PowerShell|Edit|Write|MultiEdit|NotebookEdit",
            "hooks": [{"type": "command", "command": GUARD_CMD.replace("${ROOT}", "${CLAUDE_PLUGIN_ROOT}").replace("CLIENT", "claude"), "timeout": 10}]}]}})
        # Copilot CLI reads plugin.json at the plugin root; hooks and MCP in their own files, so the
        # Claude Code hooks/hooks.json (different format) is not used by Copilot
        files[f"{out}/plugin.json"] = dump({
            "name": name, "description": p["description"], "version": VERSION, "author": AUTHOR, "license": "MIT",
            "keywords": p["keywords"],
            # skills as a list: Antigravity CLI rejects the whole plugin.json (silently, no guard) when it is a string
            "skills": ["skills/"], "hooks": "copilot/hooks.json", "mcpServers": "copilot/mcp.json"})
        files[f"{out}/copilot/mcp.json"] = dump({"mcpServers": mcp_servers(p["profile"])})
        guard_copilot = GUARD_CMD.replace("${ROOT}", "${COPILOT_PLUGIN_ROOT:-$PLUGIN_ROOT}").replace("CLIENT", "copilot")
        files[f"{out}/copilot/hooks.json"] = dump({"version": 1, "hooks": {"preToolUse": [{
            "type": "command", "bash": guard_copilot,
            "powershell": "$r = if ($env:COPILOT_PLUGIN_ROOT) { $env:COPILOT_PLUGIN_ROOT } else { $env:PLUGIN_ROOT }; "
                          "foreach ($p in 'python','py','python3') { if (Get-Command $p -ErrorAction SilentlyContinue) { "
                          "$input | & $p \"$r/scripts/guard.py\" copilot; exit 0 } }; exit 0",
            "timeoutSec": 10}]}})
        # Antigravity CLI (agy plugin install <folder>): mcp_config.json and hooks.json in the plugin root
        files[f"{out}/mcp_config.json"] = dump({"mcpServers": mcp_servers(p["profile"])})
        files[f"{out}/hooks.json"] = dump({"pds-student-guard": {"PreToolUse": [{
            "matcher": AGY_MATCHER, "hooks": [{"type": "command", "command": AGY_GUARD, "timeout": 10}]}]}})
        files[f"{out}/README.md"] = plugin_readme(p, skills)
        entries.append({"name": name, "source": f"./plugins/{name}", "description": p["description"],
                        "category": "education", "tags": p["keywords"]})
        # Gemini CLI extension
        g = f"build/out/gemini/{name}"
        for skill in skills:
            files[f"{g}/skills/{skill}/SKILL.md"] = files[f"{out}/skills/{skill}/SKILL.md"]
        files[f"{g}/gemini-extension.json"] = dump({
            "name": name, "version": VERSION, "description": p["description"], "contextFileName": "GEMINI.md",
            "mcpServers": mcp_servers(p["profile"])})
        files[f"{g}/GEMINI.md"] = (f"# {p['displayName']} (PDS course)\n\n" + p["description"] + "\n\n"
                                   + read(os.path.join(SRC, "shared", "teach-rule.md")) + "\n"
                                   + read(os.path.join(SRC, "shared", "course-context.md")))
        files[f"{g}/policies/guard.toml"] = gemini_policy()
        files[f"{g}/README.md"] = plugin_readme(p, skills)
    # instructor plugins: listed here, files in the private repository (install needs read access to it).
    # The two AI tools describe a plugin in a subdirectory of another repository differently, so the catalog
    # is written twice with the same name: Claude Code reads .claude-plugin/marketplace.json (git-subdir),
    # Copilot CLI reads .github/plugin/marketplace.json first (github + path; it rejects git-subdir)
    staff = json.loads(read(os.path.join(SRC, "marketplace", "instructor-plugins.json")))
    slug = re.sub(r"^https://github\.com/|\.git$", "", staff["repository"])
    claude_entries, copilot_entries = list(entries), [dict(e, source=e["source"][2:]) for e in entries]
    for p in staff["plugins"]:
        common = {"name": p["name"], "description": p["description"], "category": "education", "tags": ["pds", "instructor"]}
        claude_entries.append(dict(common, source={"source": "git-subdir", "url": staff["repository"],
                                                   "path": f"plugins/{p['name']}", "ref": staff["ref"]}))
        copilot_entries.append(dict(common, source={"source": "github", "repo": slug, "path": f"plugins/{p['name']}",
                                                    "ref": staff["ref"]}))
    catalog = {"name": MARKETPLACE, "owner": AUTHOR,
               "description": "AI assistant plugins of the PDS course (Projektovanje digitalnih sistema): student plugins that "
                              "teach the course workflow, and instructor plugins that only the course staff can install.",
               "version": VERSION}
    files[".claude-plugin/marketplace.json"] = dump(dict(catalog, plugins=claude_entries))
    files[".github/plugin/marketplace.json"] = dump(dict(catalog, plugins=copilot_entries))
    return files


def gemini_policy():
    lines = ["# Guard of the PDS student plugins: commands that change the repository or GitHub are",
             "# denied; the assistant shows and explains them, and the student runs them.", ""]
    msg = ("PDS plugin rule (teach, don't execute): show the student this command, explain it, say how to check "
           "and undo it; the student runs it. Do not try another way to run it.")
    for i, prefix in enumerate(DENIED_PREFIXES):
        lines += ["[[rule]]", 'toolName = "run_shell_command"', f'commandPrefix = "{prefix}"', 'decision = "deny"',
                  f"priority = {500 + i}", f'denyMessage = "{msg}"', ""]
    lines += ["# Files in assignments/ are graded work: explain the change, the student applies it", "[[rule]]",
              'toolName = ["write_file", "replace"]', 'argsPattern = "assignments[\\\\\\\\/]"', 'decision = "deny"',
              "priority = 600",
              'denyMessage = "PDS plugin rule: files in assignments/ are graded work; show the change, the student applies it."', ""]
    return "\n".join(lines)


def plugin_readme(p, skills):
    return (f"# {p['name']}\n\n{p['description']}\n\nPart of the [PDS plugins]({REPO}) marketplace. Skills: "
            + ", ".join(f"`{s}`" for s in skills) + f". Tools: `pds-mcp --profile {p['profile']}` from "
            "[pds-tools](../../tools/pds-tools) (install it in the course virtual environment).\n")


def dump(obj):
    return json.dumps(obj, indent=2, ensure_ascii=False) + "\n"


def main(argv):
    check = "--check" in argv
    files = build_files()
    managed = ["plugins", ".claude-plugin", os.path.join(".github", "plugin"), os.path.join("build", "out")]
    stale = []
    for rel, content in files.items():
        path = os.path.join(ROOT, rel)
        current = read(path) if os.path.exists(path) else None
        if current != content:
            stale.append(rel)
            if not check:
                os.makedirs(os.path.dirname(path), exist_ok=True)
                with open(path, "w", encoding="utf-8", newline="\n") as f:
                    f.write(content)
    wanted = {os.path.normpath(os.path.join(ROOT, r)) for r in files}
    extra = []
    for d in managed:
        for dirpath, _, names in os.walk(os.path.join(ROOT, d)):
            for n in names:
                full = os.path.normpath(os.path.join(dirpath, n))
                if full not in wanted:
                    extra.append(os.path.relpath(full, ROOT))
                    if not check:
                        os.remove(full)
    if check:
        tracked = [s for s in stale + extra if not s.replace(os.sep, "/").startswith("build/out/")]
        if tracked:
            print("Generated files are not up to date; run python build/build.py:\n  " + "\n  ".join(tracked))
            return 1
        print("Generated files are up to date.")
        return 0
    print(f"{len(files)} files, {len(stale)} written, {len(extra)} removed")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
