"""Check of the student's environment: tools, versions, git identity and course hooks (read-only)."""

import re
import shutil
import subprocess
import sys

from . import STYLE_TOOLS_VERSION, repo

TOOLS = [
    ("git", ["git", "--version"], True, "docs/git-setup.md"),
    ("ghdl", ["ghdl", "--version"], True, "docs/tools-setup.md (GHDL)"),
    ("vhdl-style", ["vhdl-style", "--version"], True, "docs/vhdl-code-style.md (python -m pip install -r requirements.txt in the course virtual environment)"),
    ("gh", ["gh", "--version"], False, "https://cli.github.com (optional, for pull requests from the terminal)"),
    ("quartus_sh", ["quartus_sh", "--version"], False, "docs/tools-setup.md (add <quartus>/bin64 to PATH)"),
    ("vsim", ["vsim", "-version"], False, "docs/tools-setup.md (ModelSim/Questa folder on PATH)"),
]


def _version(cmd):
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=60, encoding="utf-8", errors="replace")
    except (OSError, subprocess.TimeoutExpired):
        return None
    out = (r.stdout or r.stderr).strip().splitlines()
    return out[0] if out else ""


def env_check(path="."):
    tools = []
    for name, cmd, required, how in TOOLS:
        exe = shutil.which(cmd[0])
        entry = {"tool": name, "found": bool(exe), "required": required}
        if exe:
            entry["version"] = _version(cmd)
        else:
            entry["install"] = how
        tools.append(entry)
    style = next(t for t in tools if t["tool"] == "vhdl-style")
    if style["found"] and STYLE_TOOLS_VERSION not in (style.get("version") or ""):
        style["warning"] = f"The course uses vhdl-style-tools {STYLE_TOOLS_VERSION}; reinstall with python -m pip install -r requirements.txt."
    identity = {
        "user.name": repo.git(["config", "--get", "user.name"], cwd=path, check=False) or None,
        "user.email": repo.git(["config", "--get", "user.email"], cwd=path, check=False) or None,
    }
    problems = []
    if not identity["user.name"] or not identity["user.email"]:
        problems.append("git user.name / user.email are not set (docs/git-setup.md).")
    elif not re.search(r"@users\.noreply\.github\.com$", identity["user.email"] or ""):
        problems.append("user.email is not the GitHub noreply address; the course setup uses <id>+<login>@users.noreply.github.com (docs/git-setup.md).")
    root = repo.find_root(path)
    hooks = repo.git(["config", "--get", "core.hooksPath"], cwd=root, check=False) if root else None
    if root and hooks != ".githooks":
        problems.append("The course git hooks are not enabled in this repository: git config core.hooksPath .githooks")
    problems += [f"{t['tool']} is not installed ({t['install']})." for t in tools if t["required"] and not t["found"]]
    return {"ok": not problems, "python": sys.version.split()[0], "tools": tools, "git_identity": identity,
            "repository": root, "hooks_path": hooks, "problems": problems}
