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
    assert "ADVANCED_PHYSICAL_OPTIMIZATION OFF" in tcl  # minutes of Fitter time otherwise
    sdc = (tmp_path / "proj" / "board_top.sdc").read_text()
    assert "create_clock -name CLOCK_50 -period 20.0 [get_ports {CLOCK_50}]" in sdc and "derive_pll_clocks" in sdc
    # the constraints the student calculates are templates, commented out, with the port names of the design
    assert "# set_false_path -from [get_ports {SW[*]}]" in sdc and "# set_false_path -to [get_ports {LEDR[*]}]" in sdc
    assert "# set_output_delay -clock clk_virt -max <ns> [get_ports {dbg}]" in sdc
    assert not any(l.startswith(("set_input_delay", "set_output_delay", "set_false_path", "set_max_delay")) for l in sdc.splitlines())
    (tmp_path / "proj" / "board_top.qpf").write_text("")
    with pytest.raises(FileExistsError):
        q.project_create(str(folder), project_dir=str(tmp_path / "proj"), run=False)
    # overwrite keeps an SDC with the student's constraints and writes the template next to it
    edited = sdc + "set_false_path -from [get_ports {SW[*]}]\n"
    (tmp_path / "proj" / "board_top.sdc").write_text(edited)
    r = q.project_create(str(folder), project_dir=str(tmp_path / "proj"), run=False, overwrite=True)
    assert r["sdc_kept"] and (tmp_path / "proj" / "board_top.sdc").read_text() == edited
    assert (tmp_path / "proj" / "board_top.sdc.new").read_text() == sdc


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


def test_compile_job_runs_in_background(tmp_path, monkeypatch):
    # a full compilation outlasts the tool call timeout of AI tools (Copilot CLI: 180 s): it runs as a job
    import threading
    (tmp_path / "top.qpf").write_text("")
    release = threading.Event()

    def fake_compile(project_dir, flow, revision=None):
        release.wait(5)
        return {"ok": True, "project_dir": project_dir, "flow": flow, "steps": []}

    monkeypatch.setattr(q, "find_quartus", lambda: "quartus")
    monkeypatch.setattr(q, "compile", fake_compile)
    started = q.compile_start(str(tmp_path), "full")
    assert started["status"] == "running"
    again = q.compile_start(str(tmp_path), "synthesis")
    assert not again["ok"] and again["job"] == started["job"]  # one run per project folder
    r = q.job_wait(started["job"], wait=0)
    assert r["status"] == "running" and r["flow"] == "full" and r["stages_done"] == []
    release.set()
    r = q.job_wait(started["job"])
    assert r["status"] == "done" and r["ok"] and r["flow"] == "full"
    with pytest.raises(ValueError, match="no compile job"):
        q.job_wait("999")
