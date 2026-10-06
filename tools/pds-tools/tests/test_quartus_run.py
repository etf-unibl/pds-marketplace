import os
import subprocess

import pytest

from pds_tools import quartus_run as q

TOP = """library ieee;
use ieee.std_logic_1164.all;
entity board_top is
  port (CLOCK_50 : in  std_logic;
        SW       : in  std_logic_vector(1 downto 0);
        LEDR     : out std_logic_vector(1 downto 0);
        dbg      : out std_logic);
end entity board_top;
architecture rtl of board_top is
begin
  u0 : entity work.half port map (a => SW(0), y => dbg);
  LEDR <= SW;
end architecture rtl;
"""
HALF = "entity half is port (a : in bit; y : out bit); end entity;\narchitecture r of half is begin y <= a; end architecture;\n"


@pytest.fixture
def task(tmp_path):
    repo = tmp_path / "pds-2026"
    folder = repo / "assignments" / "12"
    folder.mkdir(parents=True)
    subprocess.run(["git", "init", "-q", str(repo)], check=True)
    (folder / "board_top.vhd").write_text(TOP)
    (folder / "half.vhd").write_text(HALF)
    (folder / "board_top_tb.vhd").write_text("entity board_top_tb is end;\n")
    return repo, folder


def test_sources_top_and_default_folder(task):
    repo, folder = task
    files = q._vhdl_sources(str(folder))
    assert sorted(os.path.basename(f) for f in files) == ["board_top.vhd", "half.vhd"]  # testbench left out
    assert q.guess_top(files) == "board_top"
    d = q.default_project_dir(str(folder), "board_top")
    assert d == os.path.join(str(repo.parent), "pds-2026-quartus", "12-board_top") and not q._inside_repo(d)


def test_project_files_without_quartus(task, tmp_path):
    repo, folder = task
    with pytest.raises(ValueError, match="inside the git repository"):
        q.project_create(str(folder), project_dir=str(repo / "quartus"), run=False)
    r = q.project_create(str(folder), project_dir=str(tmp_path / "proj"), run=False)
    assert r["ok"] and r["top"] == "board_top" and r["clock"] == "CLOCK_50" and r["ports_without_pin"] == ["dbg"]
    tcl = (tmp_path / "proj" / "create_project.tcl").read_text()
    assert "set_global_assignment -name DEVICE 5CSEMA5F31C6" in tcl and "VHDL_INPUT_VERSION VHDL_2008" in tcl
    assert "set_location_assignment PIN_AB12 -to SW[0]" in tcl and 'IO_STANDARD "3.3-V LVTTL" -to SW[0]' in tcl
    assert "board_top_tb" not in tcl and tcl.count("VHDL_FILE") == 2
    sdc = (tmp_path / "proj" / "board_top.sdc").read_text()
    assert "create_clock -name CLOCK_50 -period 20.0 [get_ports {CLOCK_50}]" in sdc
    (tmp_path / "proj" / "board_top.qpf").write_text("")
    with pytest.raises(FileExistsError):
        q.project_create(str(folder), project_dir=str(tmp_path / "proj"), run=False)


def test_report_tables():
    text = ("+------+\n; Setup Summary ;\n+------+\n; Clock ; Slack  ; End Point TNS ;\n+------+\n"
            "; clk   ; 18.840 ; 0.000         ;\n+------+\n")
    rows = q._tables(text)
    assert ["clk", "18.840", "0.000"] in rows and q._number("18.840") == 18.84 and q._number("n/a") is None


def test_tcl_refuses_repository(task):
    repo, folder = task
    if not q.find_quartus():
        pytest.skip("Quartus not installed")
    with pytest.raises(ValueError):
        q.tcl_run("puts hi", project_dir=str(repo))
