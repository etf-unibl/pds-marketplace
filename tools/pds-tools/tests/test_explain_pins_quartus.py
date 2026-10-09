import os

import pytest

from pds_tools import explain, pins, quartus, repo

FIX = os.path.join(os.path.dirname(__file__), "fixtures")


@pytest.mark.parametrize("cmd,changes", [
    ("git status", False), ("git log --oneline -3", False), ("git diff --staged", False), ("git fetch origin", False),
    ("git branch --show-current", False), ("git config --get user.email", False), ("git remote -v", False),
    ("git commit -s", True), ("git push -u origin 12-x", True), ("git add assignments/12", True), ("git branch 12-x", True),
    ("git switch -c 12-x origin/assignments", True), ("git config user.email a@b", True), ("git stash", True),
    ("gh pr view", False), ("gh pr create", True), ("gh api repos/o/r/issues/1", False),
    ("gh api -X POST repos/o/r/issues", True), ("gh api repos/o/r/issues -f title=x", True),
    ("vhdl-style 12", False), ("vhdl-style --fix 12", True), ("ghdl -a --std=08 x.vhd", False),
])
def test_guard_classification(cmd, changes):
    assert explain.is_state_changing(cmd) is changes


def test_explain_matches_most_specific_and_languages():
    assert explain.explain_command("git commit --amend -s")["matched"] == "git commit --amend"
    sr = explain.explain_command("git checkout -b 12-x", "sr")
    assert sr["matched"] == "git checkout -b" and "granu" in sr["does"]
    assert explain.explain_command("git status")["changes_repository"] is False
    assert not explain.explain_command("git bisect start")["ok"]


def test_explain_quartus_commands():
    chained = explain.explain_command("quartus_sh -t create_project.tcl && quartus_sh --flow compile top && quartus_sta -t pds_timing.tcl")
    assert chained["ok"] and [p["matched"] for p in chained["parts"]] == ["quartus_sh -t", "quartus_sh --flow compile", "quartus_sta -t"]
    full_path = explain.explain_command(r'"C:\intelFPGA_lite\23.1std\quartus\bin64\quartus_map.exe" top')
    assert full_path["matched"] == "quartus_map" and full_path["changes_repository"] is False
    assert "project folder outside the repository" in full_path["rule"]
    pgm = explain.explain_command('quartus_pgm -c "DE-SoC [USB-1]" -m JTAG -o "p;output_files/top.sof@2"', "sr")
    assert pgm["matched"] == "quartus_pgm -c" and "ploču" in pgm["undo"]
    assert explain.explain_command("quartus_sta top")["matched"] == "quartus_sta"
    assert not explain.is_state_changing("quartus_sh --flow compile top")  # the guard lets the tools run Quartus


def test_repo_git_refuses_writes(tmp_path):
    for args in (["commit", "-m", "x"], ["push"], ["branch", "new"], ["branch", "-D", "x"], ["config", "user.name", "x"], ["remote", "add", "o", "u"]):
        with pytest.raises(repo.GitError):
            repo.git(args, cwd=tmp_path)


TOP = """
library ieee;
use ieee.std_logic_1164.all;
entity top is
  port (
    CLOCK_50 : in  std_logic;
    KEY      : in  std_logic_vector(3 downto 0);  -- buttons
    SW       : in  std_logic_vector(9 downto 0);
    LEDR     : out std_logic;
    HEX0     : in  std_logic_vector(6 downto 0);
    dbg      : out std_logic_vector(1 downto 0)
  );
end top;
"""


def test_pin_table():
    t = pins.board_pins("HEX0")
    assert t["count"] == 7 and t["pins"][0]["pin"] == "PIN_AE26"
    assert pins.BY_NAME["CLOCK_50"]["pin"] == "PIN_AF14"
    assert len(pins.PINS) == 147


def test_pin_check_reports_scalar_direction_and_missing():
    r = pins.pin_check(TOP)
    by = {p["port"]: p for p in r["ports"]}
    assert by["KEY"]["pins"]["KEY[0]"] == "PIN_AA14"
    assert by["dbg"]["without_pin"] == ["dbg[0]", "dbg[1]"]
    text = " ".join(r["problems"])
    assert "LEDR" in text and "std_logic_vector(0 downto 0)" in text
    assert "HEX0 is declared 'in'" in text
    plan = pins.pin_plan(TOP)
    assert "set_location_assignment PIN_AF14 -to CLOCK_50" in plan["assignments"]


def test_quartus_reports():
    r = quartus.synth_summary(os.path.join(FIX, "quartus"))
    assert r["ok"] and r["revision"] == "qdemo"
    assert r["summary"]["Total registers"] == "8"
    ids = {w["id"] for w in r["design_warnings"]}
    assert {"10631", "10492"} <= ids
    latch = next(w for w in r["design_warnings"] if w["id"] == "10631")
    assert latch["file"] == "qdemo.vhd" and latch["line"] == 19 and latch["topic"] == 5
    t = r["timing"]
    assert t["fmax"][0]["fmax"] == "611.62 MHz" and t["met"] is True
    assert t["has_unconstrained"] is True and t["unconstrained"]["Unconstrained Input Ports"]["setup"] == "11"


GUARD = os.path.join(os.path.dirname(__file__), "..", "..", "..", "src", "shared", "guard.py")
COMMANDS = ["git status", "git -C repo status", "git -C repo commit -m x", "GIT_DIR=x git push", "/usr/bin/git.exe log",
            "git branch -a", "git branch --contains abc", "git branch new", "git stash list", "git stash pop",
            "git remote show origin", "git remote add x y", "git config --list", "git config core.hooksPath .githooks",
            "gh pr checks", "gh pr merge 3", "gh api repos/a/b", "gh api -X PATCH repos/a/b", "vhdl-style 12", "vhdl-style --fix 12",
            "ghdl -r x", "python run.py", "git", "git --version"]


def _guard():
    import importlib.util
    spec = importlib.util.spec_from_file_location("guard", GUARD)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_guard_and_explain_classify_the_same():
    guard = _guard()
    for cmd in COMMANDS:
        assert guard.is_state_changing(cmd) == explain.is_state_changing(cmd), cmd


@pytest.mark.parametrize("data,denied", [
    ({"tool_name": "Bash", "tool_input": {"command": "git status && git commit -s"}}, True),
    ({"tool_name": "Bash", "tool_input": {"command": "cd x; git log --oneline -3 | head"}}, False),
    ({"tool_name": "PowerShell", "tool_input": {"command": "powershell -Command \"git push origin 12-x\""}}, True),
    ({"tool_name": "Bash", "tool_input": {"command": "bash -c 'git add .'"}}, True),
    ({"tool_name": "Bash", "tool_input": {"command": "echo $(git rev-parse HEAD)"}}, False),
    ({"toolName": "bash", "toolArgs": "{\"command\": \"git rebase main\"}"}, True),
    ({"toolName": "powershell", "toolArgs": {"command": "ghdl -a --std=08 x.vhd"}}, False),
    ({"tool_name": "Edit", "tool_input": {"file_path": r"C:\repo\assignments\12\x.vhd"}}, True),
    ({"tool_name": "Write", "tool_input": {"file_path": "/repo/notes/todo.md"}}, False),
    ({"toolName": "edit", "toolArgs": {"path": "assignments/12/x_tb.vhd"}}, True),
    # Antigravity CLI (payloads recorded from agy 1.2.17)
    ({"toolCall": {"name": "run_command", "args": {"CommandLine": "git commit -m x", "Cwd": "C:\\r"}}}, True),
    ({"toolCall": {"name": "run_command", "args": {"CommandLine": "git status", "Cwd": "C:\\r"}}}, False),
    ({"toolCall": {"name": "replace_file_content", "args": {"TargetFile": "C:\\r\\assignments\\12\\x.vhd"}}}, True),
    ({"toolCall": {"name": "write_to_file", "args": {"TargetFile": "C:\\r\\notes.md"}}}, False),
    ({"toolCall": {"name": "git_commit", "args": {}}}, True),
])
def test_guard_decisions(data, denied):
    assert _guard().decide(data)[0] is denied


def test_guard_output_formats(tmp_path):
    import json
    import subprocess
    import sys
    payload = json.dumps({"tool_name": "Bash", "tool_input": {"command": "git push"}})
    out = subprocess.run([sys.executable, GUARD, "claude"], input=payload, capture_output=True, text=True)
    assert json.loads(out.stdout)["hookSpecificOutput"]["permissionDecision"] == "deny" and out.returncode == 0
    out = subprocess.run([sys.executable, GUARD, "copilot"], input=json.dumps({"toolName": "bash", "toolArgs": {"command": "git push"}}), capture_output=True, text=True)
    assert json.loads(out.stdout)["permissionDecision"] == "deny"
    out = subprocess.run([sys.executable, GUARD, "claude"], input=json.dumps({"tool_name": "Bash", "tool_input": {"command": "git status"}}), capture_output=True, text=True)
    assert out.stdout == ""
    # Antigravity always needs a decision: deny, or its normal permission prompt (ask)
    agy = {"toolCall": {"name": "run_command", "args": {"CommandLine": "git push"}}}
    out = subprocess.run([sys.executable, GUARD, "agy"], input=json.dumps(agy), capture_output=True, text=True)
    assert json.loads(out.stdout)["decision"] == "deny" and json.loads(out.stdout)["reason"]
    agy["toolCall"]["args"]["CommandLine"] = "ghdl -a --std=08 x.vhd"
    out = subprocess.run([sys.executable, GUARD, "agy"], input=json.dumps(agy), capture_output=True, text=True)
    assert json.loads(out.stdout) == {"decision": "ask"}
