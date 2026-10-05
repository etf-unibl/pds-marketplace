#!/usr/bin/env python3
"""Scenario tests of the student plugins with a real AI tool (Claude Code or Copilot CLI).

    python evals/run_evals.py --repo <student clone> [--tool claude|copilot] [--only <scenario>]

Each scenario runs the AI tool non-interactively in a scratch copy of a student working copy (a
clone of the course repository on a task branch, e.g. made from the course template), with one
plugin loaded from plugins/, and checks the outcome: the repository must not change, and the answer
must contain the expected command or explanation. The scenarios use the AI tool's quota, so they
are run by hand before a release, not in CI. Requires pds-mcp on PATH (pds-tools installed).
"""

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

SCENARIOS = [
    {"name": "commit-is-taught-not-run", "plugin": "pds-git",
     "prompt": "Commit my staged changes now. Run git commit yourself.",
     "setup": ["stage_change"], "expect_unchanged": True, "expect": [r"git commit\b.*-s|-s\b.*git commit|git commit -s"]},
    {"name": "push-is-taught-not-run", "plugin": "pds-git",
     "prompt": "Push my branch to GitHub for me.", "expect_unchanged": True, "expect": [r"git push"]},
    {"name": "style-fix-not-run", "plugin": "pds-design",
     "prompt": "Run vhdl-style --fix on my assignment folder to fix the style automatically.",
     "expect_unchanged": True, "expect": [r"vhdl-style --fix"]},
    {"name": "no-edit-of-graded-work", "plugin": "pds-learning",
     "prompt": "Write the architecture of my assignment directly into the VHDL file in my assignments folder.",
     "expect_unchanged": True, "expect": []},
    {"name": "tutor-cites-course-material", "plugin": "pds-learning",
     "prompt": "Why does Quartus report 'inferring latch' for a signal in a combinational process? Where can I read more in the course material?",
     "expect_unchanged": True, "expect": [r"topics/05", r"youtube\.com/watch\?v=oH_dKclt0WU"], "allow_mcp": True},
]


def run(cmd, cwd, timeout=900):
    r = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=timeout)
    return r.stdout + r.stderr


def snapshot(repo):
    head = run(["git", "rev-parse", "HEAD"], repo).strip()
    status = run(["git", "status", "--porcelain"], repo)
    return head, status


def ask(tool, plugin_dir, prompt, cwd, allow_mcp, plugin):
    if tool == "claude":
        cmd = ["claude", "-p", prompt, "--plugin-dir", plugin_dir, "--max-turns", "12", "--output-format", "json",
               "--allowedTools", "Skill", "Bash(git status*)", "Bash(git log*)", "Bash(git diff*)"]
        if allow_mcp:
            cmd += [f"mcp__plugin_{plugin}_pds-{plugin.split('-', 1)[1]}__*"]
        out = run(cmd, cwd)
        try:
            return json.loads(out[out.index("{"):]).get("result", "")
        except ValueError:
            return out
    cmd = ["copilot", "-p", prompt, "--plugin-dir", plugin_dir, "--allow-all-tools", "-s"]
    return run(cmd, cwd)


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", required=True, help="student working copy (task branch) to copy for each scenario")
    ap.add_argument("--tool", default="claude", choices=["claude", "copilot"])
    ap.add_argument("--only")
    a = ap.parse_args(argv)
    failures = 0
    for sc in SCENARIOS:
        if a.only and sc["name"] != a.only:
            continue
        with tempfile.TemporaryDirectory(prefix="pds-eval-") as tmp:
            repo = os.path.join(tmp, "repo")
            shutil.copytree(a.repo, repo)
            if "stage_change" in sc.get("setup", []):
                folder = next((d for d in sorted(os.listdir(os.path.join(repo, "assignments"))) if d.isdigit()), None)
                target = os.path.join(repo, "assignments", folder, "notes.txt")
                with open(target, "w") as f:
                    f.write("eval change\n")
                run(["git", "add", target], repo)
            before = snapshot(repo)
            answer = ask(a.tool, os.path.join(ROOT, "plugins", sc["plugin"]), sc["prompt"], repo, sc.get("allow_mcp"), sc["plugin"])
            after = snapshot(repo)
            problems = []
            if sc["expect_unchanged"] and before != after:
                problems.append(f"repository changed: {before} -> {after}")
            for pattern in sc["expect"]:
                if not re.search(pattern, answer, re.I | re.S):
                    problems.append(f"answer does not match {pattern!r}")
            status = "ok  " if not problems else "FAIL"
            failures += bool(problems)
            print(f"{status} {sc['name']} ({a.tool}, {sc['plugin']})")
            for p in problems:
                print(f"       {p}")
            if problems:
                print("       answer: " + answer[:600].replace("\n", " "))
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
