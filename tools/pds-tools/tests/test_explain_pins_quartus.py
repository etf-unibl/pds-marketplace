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
