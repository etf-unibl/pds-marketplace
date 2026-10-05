"""GHDL analysis, testbench runs exactly like the course CI, and the style check (without --fix).

The CI commands (testbench job of verif.yml on the assignments branch) are

    ghdl -i --std=08 --workdir=<tmp> *.vhd
    ghdl -m --std=08 --workdir=<tmp> <tb>
    ghdl -r --std=08 --workdir=<tmp> <tb> --stop-time=10ms --assert-level=error --wave=waves/<tb>.ghw

run in assignments/<N>. Here they run in a temporary copy of the folder, so nothing is written
into the student's working copy (some GHDL back ends write executables into the current folder,
and testbenches may write data files); files a testbench writes are reported instead.
"""

import os
import re
import shutil
import subprocess
import tempfile

from . import CI_STOP_TIME, VHDL_STD

MESSAGE = re.compile(r"^(?P<file>[^:\n]+?(?:\.vhdl?|\.vhd)):(?P<line>\d+):(?P<col>\d+):\s*(?P<rest>.*)$", re.I)
ASSERTION = re.compile(r"^@(?P<time>[^:]+):\((?P<kind>assertion|report) (?P<severity>note|warning|error|failure)\):\s*(?P<text>.*)$", re.I)


def find_ghdl():
    return shutil.which("ghdl")


def _no_ghdl():
    return {"ok": False, "error": "GHDL not found",
            "message": "GHDL is not installed or not on PATH. Install it (see docs/tools-setup.md of the course repository) and open a new terminal."}


def ci_commands(testbench, stop_time=CI_STOP_TIME):
    """The commands CI runs, for showing to students."""
    return [f"ghdl -i --std={VHDL_STD} *.vhd",
            f"ghdl -m --std={VHDL_STD} {testbench}",
            f"ghdl -r --std={VHDL_STD} {testbench} --stop-time={stop_time} --assert-level=error --wave={testbench}.ghw"]


def parse_messages(output):
    """GHDL output as a list of {file, line, column, severity, message} (assertions included)."""
    result = []
    for raw in output.splitlines():
        m = MESSAGE.match(raw.strip())
        if not m:
            if raw.strip().startswith("ghdl:error:") or raw.strip().startswith("ghdl: "):
                result.append({"file": None, "line": None, "column": None, "severity": "error", "message": raw.strip()[len("ghdl:"):].strip()})
            continue
        rest = m.group("rest")
        entry = {"file": os.path.basename(m.group("file")), "line": int(m.group("line")), "column": int(m.group("col"))}
        a = ASSERTION.match(rest)
        if a:
            entry.update(severity=a.group("severity").lower(), message=a.group("text"), time=a.group("time"), kind=a.group("kind").lower())
        elif rest.lower().startswith("warning:"):
            entry.update(severity="warning", message=rest[len("warning:"):].strip())
        elif rest.lower().startswith("note:"):
            entry.update(severity="note", message=rest[len("note:"):].strip())
        else:
            entry.update(severity="error", message=re.sub(r"^error:\s*", "", rest, flags=re.I))
        result.append(entry)
    return result


def _vhdl_files(folder):
    return sorted(f for f in os.listdir(folder) if f.lower().endswith((".vhd", ".vhdl")))


def list_testbenches(folder):
    """Testbench files of a folder (*_tb.vhd, as CI) and whether the entity is named like the file."""
    if not os.path.isdir(folder):
        return {"ok": False, "message": f"Folder {folder} does not exist."}
    benches = []
    for name in _vhdl_files(folder):
        stem = os.path.splitext(name)[0]
        if not stem.lower().endswith("_tb"):
            continue
        with open(os.path.join(folder, name), encoding="utf-8", errors="replace") as f:
            text = re.sub(r"--[^\n]*", "", f.read())
        entities = re.findall(r"\bentity\s+(\w+)\s+is\b", text, re.I)
        benches.append({"file": name, "entity": entities[0] if entities else None,
                        "entity_matches_file": bool(entities) and entities[0].lower() == stem.lower()})
    return {"ok": all(b["entity_matches_file"] for b in benches), "folder": folder, "testbenches": benches,
            "note": "CI simulates every *_tb.vhd file; the testbench entity must have the same name as the file."}


def _run(cmd, cwd, timeout):
    try:
        r = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=timeout)
        return r.returncode, r.stdout + r.stderr
    except subprocess.TimeoutExpired as e:
        return None, ((e.stdout or "") if isinstance(e.stdout, str) else "") + f"\n(stopped after {timeout} s)"


def analyze(paths, std=VHDL_STD):
    """Analyses VHDL files (or all files of a folder) into a temporary library, in dependency order."""
    ghdl = find_ghdl()
    if not ghdl:
        return _no_ghdl()
    files = []
    for p in paths if isinstance(paths, (list, tuple)) else [paths]:
        if os.path.isdir(p):
            files += [os.path.join(p, f) for f in _vhdl_files(p)]
        else:
            files.append(p)
    if not files:
        return {"ok": False, "message": "No VHDL files given."}
    with tempfile.TemporaryDirectory(prefix="pds-ghdl-") as work:
        _run([ghdl, "-i", f"--std={std}", f"--workdir={work}", *files], None, 120)
        pending, errors = list(files), {}
        while pending:
            failed = []
            for f in pending:
                code, out = _run([ghdl, "-a", f"--std={std}", f"--workdir={work}", f], None, 120)
                if code == 0:
                    errors.pop(f, None)
                else:
                    failed.append(f)
                    errors[f] = parse_messages(out)
            if len(failed) == len(pending):
                break
            pending = failed
    messages = [m for f in files for m in errors.get(f, [])]
    return {"ok": not messages, "std": f"VHDL-20{std}" if std == "08" else std, "files": [os.path.basename(f) for f in files],
            "errors": [m for m in messages if m["severity"] == "error"], "warnings": [m for m in messages if m["severity"] == "warning"],
            "command": f"ghdl -a --std={std} <file>.vhd"}


def run_testbenches(folder, testbenches=None, stop_time=CI_STOP_TIME, timeout=300):
    """Runs the testbenches of a folder like CI and reports, per testbench, pass/fail and messages."""
    ghdl = find_ghdl()
    if not ghdl:
        return _no_ghdl()
    listing = list_testbenches(folder)
    if "testbenches" not in listing:
        return listing
    names = [os.path.splitext(b["file"])[0] for b in listing["testbenches"]]
    if testbenches:
        names = [n for n in names if n in testbenches]
    if not names:
        return {"ok": False, "message": "No *_tb.vhd testbench in the folder.", "folder": folder}
    results = []
    with tempfile.TemporaryDirectory(prefix="pds-tb-") as tmp:
        copy = os.path.join(tmp, "src")
        shutil.copytree(folder, copy)
        before = {os.path.relpath(os.path.join(d, f), copy): os.path.getmtime(os.path.join(d, f)) for d, _, fs in os.walk(copy) for f in fs}
        work = os.path.join(tmp, "work")
        os.makedirs(work)
        _, import_out = _run([ghdl, "-i", f"--std={VHDL_STD}", f"--workdir={work}", *_vhdl_files(copy)], copy, 120)
        for tb in names:
            code, make_out = _run([ghdl, "-m", f"--std={VHDL_STD}", f"--workdir={work}", tb], copy, timeout)
            if code != 0:
                results.append({"testbench": tb, "passed": False, "stage": "compile", "messages": parse_messages(make_out)})
                continue
            code, run_out = _run([ghdl, "-r", f"--std={VHDL_STD}", f"--workdir={work}", tb, f"--stop-time={stop_time}", "--assert-level=error"], copy, timeout)
            messages = parse_messages(run_out)
            stopped = "simulation stopped by --stop-time" in run_out
            results.append({"testbench": tb, "passed": code == 0, "stage": "run", "messages": messages,
                            "stopped_by_stop_time": stopped,
                            **({"note": f"The simulation did not stop by itself and was stopped after {stop_time}; stop the clock and end the stimulus process with 'wait;'."} if stopped else {})})
        written = []
        for d, _, fs in os.walk(copy):
            for f in fs:
                rel = os.path.relpath(os.path.join(d, f), copy)
                if rel.endswith((".o", ".cf", ".exe")) or rel == "e~" or os.path.basename(rel).startswith("e~"):
                    continue
                if rel not in before or os.path.getmtime(os.path.join(d, f)) != before[rel]:
                    with open(os.path.join(d, f), encoding="utf-8", errors="replace") as fh:
                        written.append({"file": rel.replace(os.sep, "/"), "preview": fh.read(2000)})
    return {"ok": all(r["passed"] for r in results), "folder": folder, "results": results, "files_written_by_testbenches": written,
            "commands": {r["testbench"]: ci_commands(r["testbench"], stop_time) for r in results},
            "note": "Run in a temporary copy of the folder with the same GHDL commands as the course CI."}


def style_report(target, cwd=None):
    """Runs the course style check (vhdl-style, never with --fix) and returns the violations."""
    exe = shutil.which("vhdl-style")
    if not exe:
        return {"ok": False, "error": "vhdl-style not found",
                "message": "Install the style tools in the course virtual environment: python -m pip install -r requirements.txt (see docs/vhdl-code-style.md), then activate the environment."}
    code, out = _run([exe, target], cwd, 300)
    violations = []
    for line in out.splitlines():
        m = re.match(r"^\s+(?P<file>\S+?\.vhdl?):(?P<line>\d+): (?P<rule>\S+) -- (?P<message>.*)$", line)
        if m:
            violations.append({"file": m.group("file"), "line": int(m.group("line")), "rule": m.group("rule"), "message": m.group("message")})
    summary = [l for l in out.splitlines() if "file(s) checked" in l or l.startswith("ERROR") or l.startswith("Note:")]
    return {"ok": code == 0, "violations": violations, "summary": summary, "command": f"vhdl-style {target}",
            "fix_hint": f"Many violations can be fixed automatically with 'vhdl-style --fix {target}' (it rewrites the files; run it yourself and review the changes with git diff)."}
