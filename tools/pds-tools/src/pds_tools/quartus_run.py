"""Running Intel Quartus Prime from the command line: finding the installation, creating a project for a
course design (DE1-SoC device, VHDL-2008, pins, clock constraint) with a Tcl script the user can read and
reuse, compiling, timing analysis with the worst paths, running Tcl scripts and programming the board.

The project folder is kept OUTSIDE the course repository (course rule, docs/simulation-and-testing.md):
the project only references the VHDL files of assignments/<N>, so nothing Quartus generates ends up in a
commit. Every tool returns the command lines it ran, so the student sees how to do the same by hand.
"""

import glob
import os
import re
import shutil
import subprocess
import tempfile
import threading
import time

from . import pins, quartus

DEVICE = pins.DEVICE                     # 5CSEMA5F31C6, DE1-SoC
FAMILY = "Cyclone V"
IO_STANDARD = "3.3-V LVTTL"              # SW, KEY, LEDR, HEX, GPIO and CLOCK_50 of the DE1-SoC
CLOCK_PORT = re.compile(r"^(clock_50|clk|clock|clk_i|i_clk|clk_in|clock_i)$", re.I)
ENTITY = re.compile(r"^\s*entity\s+(\w+)\s+is\b", re.I | re.M)
INSTANCE = re.compile(r"\bentity\s+work\.(\w+)|^\s*\w+\s*:\s*(?:component\s+)?(\w+)\s*(?:generic|port)\s+map", re.I | re.M)
TOOLS = ("quartus_sh", "quartus_map", "quartus_syn", "quartus_fit", "quartus_sta", "quartus_asm", "quartus_pgm")


def _exe(name, root=None):
    root = root or find_quartus()
    if not root:
        return None
    for cand in (os.path.join(root, name + ".exe"), os.path.join(root, name)):
        if os.path.isfile(cand):
            return cand
    return None


def find_quartus():
    """The Quartus bin folder: quartus_sh on PATH, QUARTUS_ROOTDIR, or the newest standard installation."""
    on_path = shutil.which("quartus_sh")
    if on_path:
        return os.path.dirname(on_path)
    roots = []
    if os.environ.get("QUARTUS_ROOTDIR"):
        roots += [os.path.join(os.environ["QUARTUS_ROOTDIR"], b) for b in ("bin64", "bin")]
    for base in ("C:/intelFPGA_lite", "C:/intelFPGA", "C:/altera_lite", "C:/altera", os.path.expanduser("~/intelFPGA_lite"),
                 os.path.expanduser("~/intelFPGA"), "/opt/intelFPGA_lite", "/opt/intelFPGA", "/opt/altera"):
        for ver in sorted(glob.glob(os.path.join(base, "*")), key=_version_key, reverse=True):
            roots += [os.path.join(ver, "quartus", b) for b in ("bin64", "bin")]
    for r in roots:
        if os.path.isfile(os.path.join(r, "quartus_sh.exe")) or os.path.isfile(os.path.join(r, "quartus_sh")):
            return os.path.normpath(r)
    return None


def _version_key(path):
    return [int(x) for x in re.findall(r"\d+", os.path.basename(path))] or [0]


def _run(cmd, cwd, timeout):
    try:
        r = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=timeout)
        return r.returncode, (r.stdout or "") + (r.stderr or "")
    except subprocess.TimeoutExpired:
        return -1, f"timed out after {timeout} s"


def _shown(cmd):
    return " ".join(f'"{c}"' if " " in c else c for c in [os.path.basename(cmd[0]).replace(".exe", "")] + cmd[1:])


def _messages(output):
    out = {"errors": [], "critical_warnings": [], "warnings": 0}
    for line in output.splitlines():
        line = line.strip()
        if line.startswith("Error") and "Quartus Prime" not in line:
            out["errors"].append(line[:300])
        elif line.startswith("Critical Warning"):
            out["critical_warnings"].append(line[:300])
        elif line.startswith("Warning"):
            out["warnings"] += 1
    out["errors"] = out["errors"][:30]
    out["critical_warnings"] = out["critical_warnings"][:20]
    return out


def _no_quartus():
    return {"ok": False, "message": "Quartus Prime was not found. Install Quartus Prime Lite with Cyclone V support "
                                    "(docs/tools-setup.md) and add <install>/quartus/bin64 to PATH, or set QUARTUS_ROOTDIR."}


def quartus_env():
    """Quartus installation: bin folder, version, Cyclone V support, programming cables."""
    root = find_quartus()
    if not root:
        return _no_quartus()
    code, out = _run([_exe("quartus_sh", root), "--version"], None, 60)
    version = next((l.strip() for l in out.splitlines() if l.strip().startswith("Version")), out.strip()[:120])
    devinfo = os.path.join(os.path.dirname(root), "common", "devinfo")  # <install>/quartus/common/devinfo
    cyclone_v = os.path.isdir(os.path.join(devinfo, "cyclonev"))
    return {"ok": cyclone_v, "bin": root, "version": version, "cyclone_v_support": cyclone_v,
            "tools": {t: bool(_exe(t, root)) for t in TOOLS},
            "on_path": bool(shutil.which("quartus_sh")),
            "note": None if cyclone_v else "Cyclone V support is missing: add it with the Quartus installer (the DE1-SoC uses a Cyclone V)."}


def _vhdl_sources(sources):
    files = []
    for s in sources if isinstance(sources, (list, tuple)) else [sources]:
        s = os.path.abspath(s)
        if os.path.isdir(s):
            files += sorted(os.path.join(s, f) for f in os.listdir(s) if f.lower().endswith((".vhd", ".vhdl")))
        elif os.path.isfile(s):
            files.append(s)
        else:
            raise FileNotFoundError(s)
    design = [f for f in files if not re.search(r"_tb\.vhdl?$", f, re.I)]
    if not design:
        raise ValueError("no VHDL design files (testbenches *_tb.vhd are not part of a Quartus project)")
    return design


def guess_top(files):
    """The entity no other file instantiates (the top level), or None if that is ambiguous."""
    defined, used = {}, set()
    for f in files:
        text = re.sub(r"--[^\n]*", "", open(f, encoding="utf-8", errors="replace").read())
        for e in ENTITY.findall(text):
            defined[e.lower()] = e
        for a, b in INSTANCE.findall(text):
            used.add((a or b).lower())
    tops = [v for k, v in defined.items() if k not in used]
    return tops[0] if len(tops) == 1 else None


def default_project_dir(sources, top):
    """<parent of the repository>/<repository>-quartus/<task folder>-<top>: outside the repository."""
    first = os.path.abspath(sources[0] if isinstance(sources, (list, tuple)) else sources)
    folder = first if os.path.isdir(first) else os.path.dirname(first)
    d = folder
    while d and not os.path.isdir(os.path.join(d, ".git")) and os.path.dirname(d) != d:
        d = os.path.dirname(d)
    if os.path.isdir(os.path.join(d, ".git")):
        return os.path.join(os.path.dirname(d), os.path.basename(d) + "-quartus", f"{os.path.basename(folder)}-{top}")
    return os.path.join(os.path.dirname(folder), f"quartus-{top}")


def _inside_repo(path):
    d = os.path.abspath(path)
    while os.path.dirname(d) != d:
        if os.path.isdir(os.path.join(d, ".git")):
            return d
        d = os.path.dirname(d)
    return None


def project_create(sources, top=None, project_dir=None, device=DEVICE, family=FAMILY, assign_pins=True,
                   clock_mhz=50.0, io_standard=IO_STANDARD, run=True, overwrite=False):
    """Creates a Quartus project for VHDL files or a task folder: device of the DE1-SoC, VHDL-2008, top-level
    entity, pins of the ports named like board signals (SW, KEY, LEDR, HEX0..5, CLOCK_50, GPIO), a clock
    constraint (SDC) for a clock port. Writes create_project.tcl and runs it with quartus_sh -t."""
    files = _vhdl_sources(sources)
    top = top or guess_top(files)
    if not top:
        raise ValueError("cannot tell the top-level entity; give `top`")
    project_dir = os.path.abspath(project_dir or default_project_dir(sources, top))
    repo = _inside_repo(project_dir)
    if repo:
        raise ValueError(f"{project_dir} is inside the git repository {repo}: keep the Quartus project outside the "
                         "repository (course rule), e.g. the default <repository>-quartus folder next to it")
    qpf = os.path.join(project_dir, f"{top}.qpf")
    if os.path.exists(qpf) and not overwrite:
        raise FileExistsError(f"{qpf} exists; use the project (compile) or pass overwrite=true to recreate it")
    os.makedirs(project_dir, exist_ok=True)
    top_text = ""
    for f in files:
        text = open(f, encoding="utf-8", errors="replace").read()
        if re.search(rf"^\s*entity\s+{re.escape(top)}\s+is\b", text, re.I | re.M):
            top_text = text
    entity, ports = pins.parse_ports(top_text) if top_text else (None, [])
    clock = next((p["name"] for p in ports if p["mode"] == "in" and p["indices"] is None and CLOCK_PORT.match(p["name"])), None)
    plan = pins.pin_plan(top_text) if (assign_pins and top_text) else {"assignments": [], "without_pin": []}
    tcl = ["# Quartus project for the PDS course (created by pds-tools); run again with: quartus_sh -t create_project.tcl",
           f"project_new {top} -overwrite" if overwrite else f"project_new {top}",
           f'set_global_assignment -name FAMILY "{family}"',
           f"set_global_assignment -name DEVICE {device}",
           f"set_global_assignment -name TOP_LEVEL_ENTITY {top}",
           "set_global_assignment -name PROJECT_OUTPUT_DIRECTORY output_files",
           "set_global_assignment -name VHDL_INPUT_VERSION VHDL_2008",
           "set_global_assignment -name NUM_PARALLEL_PROCESSORS ALL"]
    tcl += [f"set_global_assignment -name VHDL_FILE {{{f.replace(os.sep, '/')}}}" for f in files]
    tcl.append(f"set_global_assignment -name SDC_FILE {top}.sdc")
    pin_lines = plan.get("assignments", [])
    for line in pin_lines:
        tcl.append(line)
        target = line.split(" -to ", 1)[1]
        tcl.append(f'set_instance_assignment -name IO_STANDARD "{io_standard}" -to {target}')
    tcl += ["export_assignments", "project_close", ""]
    sdc = [f"# Timing constraints of {top} (PDS course)"]
    if clock:
        period = round(1000.0 / clock_mhz, 3)
        sdc.append(f"create_clock -name {clock} -period {period} [get_ports {{{clock}}}]")
    else:
        sdc.append("# no clock port found: a combinational design has no clock to constrain; add create_clock for a clock port")
    sdc += ["derive_clock_uncertainty", ""]
    with open(os.path.join(project_dir, "create_project.tcl"), "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(tcl))
    with open(os.path.join(project_dir, f"{top}.sdc"), "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(sdc))
    result = {"project_dir": project_dir, "top": top, "files": files, "device": device, "clock": clock,
              "clock_mhz": clock_mhz if clock else None, "pins_assigned": len(pin_lines),
              "ports_without_pin": plan.get("without_pin", []), "tcl": "\n".join(tcl), "sdc": "\n".join(sdc)}
    if not run:
        result.update(ok=True, ran=False, command=f"cd {project_dir} && quartus_sh -t create_project.tcl")
        return result
    sh = _exe("quartus_sh")
    if not sh:
        result.update(_no_quartus(), command=f"cd {project_dir} && quartus_sh -t create_project.tcl")
        return result
    code, out = _run([sh, "-t", "create_project.tcl"], project_dir, 300)
    result.update(ok=code == 0, ran=True, command=f"cd {project_dir} && quartus_sh -t create_project.tcl", **_messages(out))
    if code != 0:
        result["output_tail"] = out[-1500:]
    return result


FLOWS = {
    "synthesis": [["quartus_map"]],
    "fit": [["quartus_fit"]],
    "timing": [["quartus_sta"]],
    "assemble": [["quartus_asm"]],
    "full": [["quartus_sh", "--flow", "compile"]],
}


def _project(project_dir, revision=None):
    project_dir = os.path.abspath(project_dir)
    qpfs = sorted(glob.glob(os.path.join(project_dir, "*.qpf")))
    if not qpfs:
        raise FileNotFoundError(f"no Quartus project (.qpf) in {project_dir}")
    name = os.path.splitext(os.path.basename(qpfs[0]))[0]
    return project_dir, name, revision or name


def compile(project_dir, flow="synthesis", revision=None, timeout=1800):
    """Runs a Quartus flow: synthesis (quartus_map), fit, timing (quartus_sta), assemble or full
    (quartus_sh --flow compile: synthesis, fitter, assembler, timing). Returns the result, the errors and
    critical warnings, and for synthesis and full the synthesis review (latches, removed registers, ...)."""
    if flow not in FLOWS:
        raise ValueError(f"flow must be one of {', '.join(FLOWS)}")
    project_dir, name, rev = _project(project_dir, revision)
    if not find_quartus():
        return _no_quartus()
    steps = []
    for step in FLOWS[flow]:
        exe = _exe(step[0])
        cmd = [exe] + step[1:] + [name] + (["-c", rev] if rev != name else [])
        code, out = _run(cmd, project_dir, timeout)
        steps.append({"command": _shown(cmd), "ok": code == 0, **_messages(out)})
        if code != 0:
            steps[-1]["output_tail"] = out[-1500:]
            break
    result = {"ok": all(s["ok"] for s in steps), "project_dir": project_dir, "flow": flow, "steps": steps}
    if flow in ("synthesis", "full"):
        try:
            result["review"] = quartus.synth_summary(project_dir, rev)
        except Exception as e:  # noqa: BLE001 - the reports may be missing after a failed run
            result["review"] = {"ok": False, "message": str(e)}
    if flow in ("full", "assemble"):
        sof = glob.glob(os.path.join(project_dir, "output_files", f"{rev}.sof"))
        result["sof"] = sof[0] if sof else None
    return result


# A full compilation takes minutes; AI tools cancel a tool call after a few minutes (Copilot CLI: 180 s).
# compile_start runs the flow in a background thread of the tool server and job_wait waits for it in
# steps shorter than that, so no single tool call runs into the client's timeout.
JOB_WAIT = 90
_jobs = {}
_jobs_lock = threading.Lock()


def compile_start(project_dir, flow="synthesis", revision=None):
    """Starts compile() in the background and returns the job id; one job per project folder at a time."""
    if flow not in FLOWS:
        raise ValueError(f"flow must be one of {', '.join(FLOWS)}")
    project_dir, name, rev = _project(project_dir, revision)
    if not find_quartus():
        return _no_quartus()
    with _jobs_lock:
        for job_id, job in _jobs.items():
            if job["project_dir"] == project_dir and job["thread"].is_alive():
                return {"ok": False, "job": job_id, "status": "running", "flow": job["flow"],
                        "message": f"a {job['flow']} run of this project is still in progress: wait for it with quartus_job"}
        job_id = str(len(_jobs) + 1)
        job = {"project_dir": project_dir, "flow": flow, "revision": rev, "started": time.time(), "finished": None, "result": None}

        def work():
            try:
                job["result"] = compile(project_dir, flow, revision)
            except Exception as e:  # noqa: BLE001 - reported by job_wait
                job["result"] = {"ok": False, "error": type(e).__name__, "message": str(e)}
            job["finished"] = time.time()

        job["thread"] = threading.Thread(target=work, name=f"quartus-job-{job_id}", daemon=True)
        _jobs[job_id] = job
        job["thread"].start()
    return {"ok": True, "job": job_id, "status": "running", "flow": flow, "project_dir": project_dir}


def _stages_done(job):
    """Quartus stages (by their report files) finished since the job started."""
    done = []
    for stage, ext in (("synthesis", "map"), ("fitter", "fit"), ("assembler", "asm"), ("timing", "sta")):
        for folder in (os.path.join(job["project_dir"], "output_files"), job["project_dir"]):
            rpt = os.path.join(folder, f"{job['revision']}.{ext}.rpt")
            if os.path.exists(rpt) and os.path.getmtime(rpt) >= job["started"]:
                done.append(stage)
                break
    return done


def job_wait(job_id, wait=JOB_WAIT):
    """Waits up to wait seconds (at most JOB_WAIT) for a compile job; the result of compile() once it is done."""
    job = _jobs.get(str(job_id))
    if not job:
        raise ValueError(f"no compile job {job_id}: jobs last only as long as the tool server (a new AI tool "
                         "session starts a new one); run quartus_compile again")
    job["thread"].join(max(0, min(wait, JOB_WAIT)))
    if job["thread"].is_alive():
        return {"ok": True, "job": str(job_id), "status": "running", "flow": job["flow"], "project_dir": job["project_dir"],
                "elapsed_s": round(time.time() - job["started"]), "stages_done": _stages_done(job),
                "next": "Quartus is still running: call quartus_job with this job id again"}
    return {**job["result"], "job": str(job_id), "status": "done", "elapsed_s": round(job["finished"] - job["started"])}

STA_SCRIPT = """# Timing analysis of the PDS course (created by pds-tools); run with: quartus_sta -t {script}
project_open {name} -revision {rev}
create_timing_netlist
read_sdc
update_timing_netlist
check_timing -file pds_check_timing.txt
report_clock_fmax_summary -file pds_fmax.txt
create_timing_summary -setup -multi_corner -file pds_setup_summary.txt
create_timing_summary -hold -multi_corner -file pds_hold_summary.txt
report_timing -setup -npaths {paths} -detail summary -file pds_setup_paths.txt
report_timing -hold -npaths {paths} -detail summary -file pds_hold_paths.txt
report_ucp -file pds_unconstrained.txt
report_path -from [all_inputs] -to [all_outputs] -npaths {paths} -file pds_io_paths.txt
delete_timing_netlist
project_close
"""


def _tables(text):
    """Rows of the ';'-separated tables of a Quartus text report, as lists of cells."""
    rows = []
    for line in text.splitlines():
        if line.startswith(";") and not set(line) <= set(";+- "):
            cells = [c.strip() for c in line.strip().strip(";").split(";")]
            rows.append(cells)
    return rows


def _number(s):
    try:
        return float(re.sub(r"[^0-9.+-]", "", s))
    except ValueError:
        return None


def timing_analysis(project_dir, revision=None, paths=10, timeout=900):
    """Timing analysis of a fitted project with quartus_sta: setup and hold slack per clock (all corners),
    Fmax per clock, the worst setup and hold paths, unconstrained paths and check_timing warnings. Writes
    and runs pds_timing.tcl in the project folder (the student can run and edit it)."""
    project_dir, name, rev = _project(project_dir, revision)
    if not find_quartus():
        return _no_quartus()
    script = os.path.join(project_dir, "pds_timing.tcl")
    with open(script, "w", encoding="utf-8", newline="\n") as f:
        f.write(STA_SCRIPT.format(name=name, rev=rev, paths=int(paths), script="pds_timing.tcl"))
    cmd = [_exe("quartus_sta"), "-t", "pds_timing.tcl"]
    code, out = _run(cmd, project_dir, timeout)
    if code != 0:
        return {"ok": False, "command": _shown(cmd), **_messages(out), "output_tail": out[-1500:],
                "hint": "timing analysis needs a fitted design: run compile with flow 'full' (or 'fit') first"}

    def read(fname):
        p = os.path.join(project_dir, fname)
        return open(p, encoding="utf-8", errors="replace").read() if os.path.exists(p) else ""

    def summary(fname):
        out_rows = []
        for r in _tables(read(fname)):
            if len(r) >= 3 and _number(r[1]) is not None and r[0] not in ("Clock",):
                out_rows.append({"clock": r[0], "slack_ns": _number(r[1]), "tns_ns": _number(r[2])})
        return out_rows

    def path_rows(fname):
        rows, header = [], None
        for r in _tables(read(fname)):
            if r and r[0] in ("Slack", "Delay"):  # report_timing tables start with Slack, report_path with Delay
                header = r
                continue
            if header and len(r) == len(header) and _number(r[0]) is not None:
                rows.append(dict(zip([h.lower().replace(" ", "_") for h in header], r)))
        return rows

    fmax = [{"clock": r[2] if len(r) > 2 else r[-1], "fmax": r[0], "restricted_fmax": r[1] if len(r) > 1 else None}
            for r in _tables(read("pds_fmax.txt")) if r and re.search(r"MHz", r[0])]
    setup, hold = summary("pds_setup_summary.txt"), summary("pds_hold_summary.txt")
    worst_setup = min((s["slack_ns"] for s in setup), default=None)
    worst_hold = min((s["slack_ns"] for s in hold), default=None)
    check = [l.strip() for l in read("pds_check_timing.txt").splitlines() if re.search(r"Warning|unconstrained|no clock", l, re.I)][:20]
    return {"ok": (worst_setup is None or worst_setup >= 0) and (worst_hold is None or worst_hold >= 0),
            "command": _shown(cmd), "script": script, "setup": setup, "hold": hold, "fmax": fmax,
            "worst_setup_slack_ns": worst_setup, "worst_hold_slack_ns": worst_hold,
            "setup_paths": path_rows("pds_setup_paths.txt")[:paths], "hold_paths": path_rows("pds_hold_paths.txt")[:paths],
            "unconstrained": [l.strip() for l in read("pds_unconstrained.txt").splitlines() if l.strip().startswith(";")][:20],
            "check_timing": check,
            "pin_to_pin": path_rows("pds_io_paths.txt")[:paths],
            "note": "no clock is constrained (combinational design): there is no slack to check; pin_to_pin lists the longest "
                    "input-to-output delays, and set_max_delay -from [all_inputs] -to [all_outputs] <ns> in the SDC turns them into "
                    "checked paths" if not setup else None}


def tcl_run(script, tool="quartus_sh", project_dir=None, timeout=600):
    """Runs a Tcl script (file path or text) with quartus_sh -t or quartus_sta -t in the project folder.
    Use for project changes, assignments, custom reports; the script stays in the project folder."""
    if tool not in ("quartus_sh", "quartus_sta"):
        raise ValueError("tool must be quartus_sh or quartus_sta")
    if not find_quartus():
        return _no_quartus()
    cwd = os.path.abspath(project_dir) if project_dir else tempfile.mkdtemp(prefix="pds-tcl-")
    if _inside_repo(cwd):
        raise ValueError("run Tcl in the Quartus project folder outside the repository")
    if os.path.isfile(script):
        path = os.path.abspath(script)
    else:
        path = os.path.join(cwd, "pds_script.tcl")
        with open(path, "w", encoding="utf-8", newline="\n") as f:
            f.write(script)
    cmd = [_exe(tool), "-t", path]
    code, out = _run(cmd, cwd, timeout)
    return {"ok": code == 0, "command": _shown(cmd), "folder": cwd, **_messages(out), "output": out[-4000:]}


def program_cables():
    """Programming cables (USB-Blaster) that quartus_pgm sees, and the devices on the JTAG chain."""
    pgm = _exe("quartus_pgm")
    if not pgm:
        return _no_quartus()
    code, out = _run([pgm, "-l"], None, 60)
    cables = [re.sub(r"^\d+\)\s*", "", l.strip()) for l in out.splitlines() if re.match(r"^\s*\d+\)", l)]
    return {"ok": bool(cables), "cables": cables, "command": "quartus_pgm -l",
            "hint": None if cables else "no cable found: connect the board (USB-Blaster port), switch it on, install the USB-Blaster driver (docs/tools-setup.md)"}


def program_board(sof, cable=None, device_index=2, timeout=300):
    """Programs the FPGA of the DE1-SoC with a .sof file over JTAG (the FPGA is device 2 on the DE1-SoC chain,
    after the HPS). Volatile: the design is lost when the board is switched off."""
    pgm = _exe("quartus_pgm")
    if not pgm:
        return _no_quartus()
    sof = os.path.abspath(sof)
    if not os.path.isfile(sof):
        raise FileNotFoundError(sof)
    cable = cable or (program_cables().get("cables") or [None])[0]
    if not cable:
        return {"ok": False, "message": "no programming cable found", "hint": program_cables().get("hint")}
    cmd = [pgm, "-c", cable, "-m", "JTAG", "-o", f"p;{sof.replace(os.sep, '/')}@{device_index}"]
    code, out = _run(cmd, os.path.dirname(sof), timeout)
    return {"ok": code == 0, "command": _shown(cmd), **_messages(out), "output_tail": out[-1200:]}
