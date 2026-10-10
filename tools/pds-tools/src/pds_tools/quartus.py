"""Summaries of existing Quartus reports (synthesis warnings, resources, timing).

Quartus writes the reports (<revision>.flow.rpt, .map.rpt, .fit.summary, .sta.rpt,
.sta.summary) into the project folder or into output_files/. These functions only read them;
the student compiles the project in Quartus (or with quartus_sh --flow compile).
"""

import glob
import os
import re

# Synthesis messages that usually mean a design error, with the topic page that explains them
KNOWN_WARNINGS = {
    "10631": {"meaning": "latch inferred: a signal keeps its value in some path of a combinational process",
              "fix": "assign the signal in every branch (else / when others) or give it a default value at the start of the process",
              "topic": 5},
    "10492": {"meaning": "incomplete sensitivity list: simulation and synthesis will differ",
              "fix": "add the signal to the sensitivity list (or use process(all) in VHDL-2008)", "topic": 5},
    "10540": {"meaning": "signal is assigned but never read", "fix": "remove it or connect it", "topic": None},
    "10541": {"meaning": "signal is read but never assigned, it gets a default value", "fix": "assign the signal", "topic": None},
    "10036": {"meaning": "object declared but never read", "fix": "remove the declaration or use it", "topic": None},
    "13024": {"meaning": "output pin stuck at VCC or GND", "fix": "check the logic driving the output", "topic": 8},
    "21074": {"meaning": "design contains input pins that do not drive logic", "fix": "check that every input is used", "topic": None},
    "332060": {"meaning": "node used as a clock but not constrained (often a derived or gated clock)", "fix": "use one clock with an enable signal", "topic": 9},
}
MESSAGE = re.compile(r"^(?P<kind>Critical Warning|Warning|Error) \((?P<id>\d+)\): (?P<text>.*?)(?: File: (?P<file>.*?) Line: (?P<line>\d+))?\s*$")


def find_reports(project_dir="."):
    """Report files of the project (project folder and output_files/), newest revision first."""
    found = {}
    for folder in (project_dir, os.path.join(project_dir, "output_files")):
        for path in glob.glob(os.path.join(folder, "*.flow.rpt")):
            rev = os.path.basename(path)[:-len(".flow.rpt")]
            found[rev] = folder
    revisions = sorted(found, key=lambda r: -os.path.getmtime(os.path.join(found[r], r + ".flow.rpt")))
    return [{"revision": r, "folder": found[r]} for r in revisions]


def _read(path):
    if not os.path.isfile(path):
        return None
    with open(path, encoding="utf-8", errors="replace") as f:
        return f.read()


def _table(text, title):
    """Rows of a ';'-separated report table that follows the line with title."""
    idx = text.find("; " + title)
    if idx < 0:
        return []
    rows = []
    for line in text[idx:].splitlines()[1:]:
        if line.startswith("+"):
            if rows:
                continue
            continue
        if not line.startswith(";"):
            if rows:
                break
            continue
        cells = [c.strip() for c in line.strip().strip(";").split(";")]
        rows.append(cells)
        if len(rows) > 200:
            break
    return rows


def flow_summary(text):
    summary = {}
    for cells in _table(text, "Flow Summary"):
        if len(cells) == 2:
            summary[cells[0]] = cells[1]
    return summary


def messages(text, ids=None):
    result = []
    for line in (text or "").splitlines():
        m = MESSAGE.match(line)
        if m and (ids is None or m.group("id") in ids):
            entry = {"kind": m.group("kind"), "id": m.group("id"), "text": m.group("text").strip()}
            if m.group("file"):
                entry["file"] = os.path.basename(m.group("file"))
                entry["line"] = int(m.group("line"))
            if m.group("id") in KNOWN_WARNINGS:
                entry.update(KNOWN_WARNINGS[m.group("id")])
            result.append(entry)
    return result


def timing(sta_text, sta_summary):
    result = {"fmax": [], "slack": [], "unconstrained": {}}
    for model in ("Slow 1100mV 85C Model", "Slow 1100mV 0C Model"):
        header_seen = False
        for cells in _table(sta_text or "", f"{model} Fmax Summary"):
            if cells and cells[0] == "Fmax":
                header_seen = True
                continue
            if header_seen and len(cells) >= 3 and "MHz" in cells[0]:
                result["fmax"].append({"model": model, "fmax": cells[0], "restricted_fmax": cells[1], "clock": cells[2], "note": cells[3] if len(cells) > 3 else ""})
    for m in re.finditer(r"Type\s*:\s*(?P<type>.+?)\nSlack\s*:\s*(?P<slack>-?[\d.]+)\nTNS\s*:\s*(?P<tns>-?[\d.]+)", sta_summary or ""):
        result["slack"].append({"type": m.group("type").strip(), "slack": float(m.group("slack")), "tns": float(m.group("tns"))})
    for cells in _table(sta_text or "", "Unconstrained Paths Summary"):
        if len(cells) == 3 and cells[0] != "Property":
            result["unconstrained"][cells[0]] = {"setup": cells[1], "hold": cells[2]}
    result["met"] = bool(result["slack"]) and all(s["slack"] >= 0 for s in result["slack"])
    result["has_unconstrained"] = any(v["setup"] not in ("0", "") for v in result["unconstrained"].values())
    return result


def synth_summary(project_dir=".", revision=None):
    """Flow summary, warnings that point to design errors and timing of a compiled project."""
    reports = find_reports(project_dir)
    if not reports:
        return {"ok": False, "message": "No Quartus reports found (<revision>.flow.rpt in the project folder or output_files/). Compile the project first."}
    rep = next((r for r in reports if r["revision"] == revision), reports[0])
    base = os.path.join(rep["folder"], rep["revision"])
    flow = _read(base + ".flow.rpt") or ""
    synth = _read(base + ".map.rpt") or ""
    sta = _read(base + ".sta.rpt")
    all_messages = messages(synth)
    important = [m for m in all_messages if m["id"] in KNOWN_WARNINGS or m["kind"] != "Warning"]
    result = {"ok": True, "revision": rep["revision"], "folder": rep["folder"], "summary": flow_summary(flow),
              "design_warnings": important, "other_warning_count": len(all_messages) - len(important)}
    if sta is not None:
        result["timing"] = timing(sta, _read(base + ".sta.summary"))
        qsf = _read(os.path.join(project_dir, rep["revision"] + ".qsf")) or ""
        has_sdc = os.path.exists(os.path.join(project_dir, rep["revision"] + ".sdc")) or "SDC_FILE" in qsf
        if not has_sdc and not result["timing"]["fmax"]:
            result["timing"]["note"] = "Without an SDC file the timing analysis assumes a 1 GHz clock; see topic 13."
    regs = result["summary"].get("Total registers")
    if regs == "0":
        result["note"] = "Total registers is 0: the design is purely combinational (expected for combinational tasks)."
    return result
