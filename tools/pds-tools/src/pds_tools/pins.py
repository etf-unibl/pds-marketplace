"""DE1-SoC pin table and checks of top-level ports against it.

The table is the course file DE1_SoC_pin_assigments.csv (video tutorial 7), which Quartus imports
with Assignments > Import Assignments. Ports of the top-level entity are connected to the board
only when their names match the names in the file (SW, KEY, LEDR, HEX0, ...), with vectors
indexed like SW[0]. Nothing here changes a project: pin_plan() returns text to copy.
"""

import csv
import io
import re
from importlib import resources

# Board peripherals: direction from the FPGA's point of view and notes for students
PERIPHERALS = {
    "CLOCK_50": {"direction": "in", "description": "50 MHz clock oscillator"},
    "SW": {"direction": "in", "description": "slide switches (up = '1')"},
    "KEY": {"direction": "in", "description": "push buttons, active low (pressed = '0'), debounced on the board"},
    "LEDR": {"direction": "out", "description": "red LEDs (lit for '1')"},
    "HEX0": {"direction": "out", "description": "seven-segment display 0, segments active low (lit for '0'), index 0..6 = segments a..g"},
    "HEX1": {"direction": "out", "description": "seven-segment display 1, segments active low"},
    "HEX2": {"direction": "out", "description": "seven-segment display 2, segments active low"},
    "HEX3": {"direction": "out", "description": "seven-segment display 3, segments active low"},
    "HEX4": {"direction": "out", "description": "seven-segment display 4, segments active low"},
    "HEX5": {"direction": "out", "description": "seven-segment display 5, segments active low"},
    "GPIO_0": {"direction": "inout", "description": "40-pin expansion header JP1 (36 I/O pins)"},
    "GPIO_1": {"direction": "inout", "description": "40-pin expansion header JP2 (36 I/O pins)"},
}
SOURCE = "DE1_SoC_pin_assigments.csv (video-tutorials/part-2/video-tutorial-07 of the course repository)"
DEVICE = "5CSEMA5F31C6"


def _load():
    text = resources.files("pds_tools").joinpath("data/de1_soc_pins.csv").read_text(encoding="ascii")
    pins = []
    rows = [r for r in csv.reader(io.StringIO(text)) if r and not r[0].startswith("#")]
    for name, location, *_ in rows:
        name, location = name.strip(), location.strip()
        if name == "To" or not location.startswith("PIN_"):
            continue
        m = re.match(r"^([A-Za-z0-9_]+?)(?:\[(\d+)\])?$", name)
        group, index = m.group(1), int(m.group(2)) if m.group(2) is not None else None
        info = PERIPHERALS.get(group, {})
        pins.append({"signal": name, "pin": location, "group": group, "index": index,
                     "direction": info.get("direction", "inout"), "description": info.get("description", "")})
    return pins


PINS = _load()
BY_NAME = {p["signal"].upper(): p for p in PINS}


def board_pins(filter_text=None):
    """Pins whose signal name, group or pin contains filter_text (case-insensitive); all without a filter."""
    if not filter_text:
        result = PINS
    else:
        f = filter_text.upper()
        result = [p for p in PINS if f in p["signal"].upper() or f in p["pin"].upper() or f == p["group"].upper()]
    groups = sorted({p["group"] for p in result})
    return {"device": DEVICE, "source": SOURCE, "count": len(result), "groups": {g: PERIPHERALS.get(g, {}) for g in groups}, "pins": result}


PORT_DECL = re.compile(
    r"([A-Za-z][\w\s,]*?)\s*:\s*(in|out|inout|buffer)\s+([\w.]+)\s*(?:\(\s*([^)]*?)\s*\))?\s*(?:;|$)", re.I)
RANGE = re.compile(r"^\s*(\d+)\s+(downto|to)\s+(\d+)\s*$", re.I)


def parse_ports(vhdl_text):
    """Ports of the first entity in a VHDL text: list of {name, mode, type, indices}.

    indices is None for a scalar, a list of integers for a vector with a literal range and
    "unknown" when the range depends on generics.
    """
    text = re.sub(r"--[^\n]*", "", vhdl_text)
    m = re.search(r"\bentity\s+(\w+)\s+is(.*?)\bend\b", text, re.I | re.S)
    if not m:
        return None, []
    body = m.group(2)
    p = re.search(r"\bport\s*\((.*)\)\s*;", body, re.I | re.S)
    if not p:
        return m.group(1), []
    ports = []
    for decl in _split_top_level(p.group(1)):
        d = PORT_DECL.match(decl.strip() + ";")
        if not d:
            continue
        names = [n.strip() for n in d.group(1).split(",") if n.strip()]
        rng = d.group(4)
        if rng is None:
            indices = None
        else:
            r = RANGE.match(rng)
            if r:
                a, b = int(r.group(1)), int(r.group(3))
                indices = list(range(min(a, b), max(a, b) + 1))
            else:
                indices = "unknown"
        for n in names:
            ports.append({"name": n, "mode": d.group(2).lower(), "type": d.group(3).lower(), "indices": indices})
    return m.group(1), ports


def _split_top_level(text):
    """Splits a port list at ';' outside parentheses."""
    parts, depth, cur = [], 0, []
    for ch in text:
        if ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
        if ch == ";" and depth == 0:
            parts.append("".join(cur))
            cur = []
        else:
            cur.append(ch)
    if "".join(cur).strip():
        parts.append("".join(cur))
    return parts


def _port_signals(port):
    if port["indices"] is None:
        return [port["name"]]
    if port["indices"] == "unknown":
        return []
    return [f"{port['name']}[{i}]" for i in port["indices"]]


def pin_check(vhdl_text):
    """Checks the top-level ports of a VHDL text against the board pin names.

    Reports, for each port, which bits have a board pin (and which pin), which do not, and
    direction problems (e.g. KEY declared as an output). Ports without a pin are not errors in
    general (internal top levels, testbenches), but the top level that is programmed into the
    board needs a pin for every bit.
    """
    entity, ports = parse_ports(vhdl_text)
    if entity is None:
        return {"ok": False, "message": "No entity declaration found."}
    results, problems = [], []
    for port in ports:
        signals = _port_signals(port)
        mapped = {s: BY_NAME[s.upper()]["pin"] for s in signals if s.upper() in BY_NAME}
        missing = [s for s in signals if s.upper() not in BY_NAME]
        group = port["name"].upper()
        info = PERIPHERALS.get(group) or next((v for k, v in PERIPHERALS.items() if k.upper() == group), None)
        entry = {"port": port["name"], "mode": port["mode"], "bits": signals or port["indices"], "pins": mapped, "without_pin": missing}
        if port["indices"] == "unknown":
            entry["note"] = "the range depends on generics; give the bit names to check them"
        if info and info["direction"] != "inout" and port["mode"] != info["direction"]:
            problems.append(f"Port {port['name']} is declared '{port['mode']}', but {group} on the board is an {info['direction']}put ({info['description']}).")
        if not mapped and port["indices"] is None and f"{group}[0]" in BY_NAME:
            problems.append(f"Port {port['name']} is a scalar, but the pin file names the board signal {group}[0]; declare std_logic_vector(0 downto 0) and use {port['name']}(0).")
        results.append(entry)
    all_mapped = all(not r["without_pin"] for r in results) and bool(results)
    return {"ok": not problems, "entity": entity, "all_ports_have_pins": all_mapped, "ports": results, "problems": problems,
            "hint": "Ports are connected to the board only when their names match the pin file (SW, KEY, LEDR, HEX0..HEX5, CLOCK_50, GPIO_0/1). Import the file with Assignments > Import Assignments."}


def pin_plan(vhdl_text):
    """Quartus assignments (Tcl, as in the .qsf file) for the ports that match board signals.

    Returns text only; the student adds it to the project (or imports the CSV file instead).
    """
    check = pin_check(vhdl_text)
    if not check.get("entity"):
        return check
    lines = [f"set_location_assignment {pin} -to {sig}" for p in check["ports"] for sig, pin in p["pins"].items()]
    return {"entity": check["entity"], "assignments": lines, "without_pin": [s for p in check["ports"] for s in p["without_pin"]],
            "how_to_use": "Recommended: Assignments > Import Assignments with the course CSV file. Alternative: add these lines to <project>.qsf or enter the pins in Assignments > Pin Planner, then recompile."}
