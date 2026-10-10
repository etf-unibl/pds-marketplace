"""Timing information from a component datasheet (PDF): where it is and the tables as they are printed.

The values are not interpreted here: datasheet tables differ between vendors (several columns per supply
voltage, temperature or part, merged cells, subscripts on a separate line), so the tables are returned
cleaned, with the page and the section, and the assistant explains them with the student.
"""

import os
import re

# Words of the sections and captions that hold timing information
TIMING_WORDS = ["timing requirements", "switching characteristics", "timing characteristics", "ac characteristics",
                "ac electrical characteristics", "timing specifications", "timing parameters", "timing diagram",
                "setup time", "set-up time", "hold time", "clock to output", "clock-to-output", "propagation delay",
                "access time", "output hold", "output valid", "data valid", "clock frequency", "clock period"]
# A timing symbol, e.g. tSU, tH, tCO, tPD, tAC, tOH, t_CK (subscript joined by clean())
SYMBOL = re.compile(r"\bt[_ ]?(?:[A-Z][A-Za-z0-9]{0,6}|su|h|hd|pd|w|co|cq|clk|oh|ac|ck|cl|ch|pw|en|dis|plh|phl|"
                    r"ds|dh|as|ah|rc|wc|cyc|sck|css|csh|dv|r|f)\b")
UNITS = re.compile(r"\b(ns|ps|µs|us|MHz|kHz)\b")
NUMBER = re.compile(r"^[-–+]?\d+(\.\d+)?$")
HEADING = re.compile(r"^(\d+(\.\d+)*\.?\s+|Table\s+\d+[.:\-]?\s*|TABLE\s+\d+)?[A-Z][\w ,/()\-–]{3,80}$")
FIGURE = re.compile(r"^(Figure|FIGURE|Fig\.)\s*\d+[\w.\-]*[.:]?\s+.*(Timing|Waveform|Diagram|Read|Write|Interface)", re.I)
NOTE = re.compile(r"^(\(\d+\)|Note\s*\d*[:.]|\d+\.\s+[A-Z])")

_cache = {}


def _open(path):
    """Page texts, metadata and bookmarks of a PDF (pdfium: fast, subscripts stay joined to their symbol),
    cached by path and modification time."""
    if not os.path.isfile(path):
        raise FileNotFoundError(f"No file {path}")
    key = (os.path.abspath(path), os.path.getmtime(path))
    if key not in _cache:
        import pypdfium2 as pdfium
        pdf = pdfium.PdfDocument(path)
        try:
            texts = [pdf[i].get_textpage().get_text_range().replace("\r\n", "\n") for i in range(len(pdf))]
            meta = pdf.get_metadata_dict()
            outline = []
            try:
                for b in pdf.get_toc():
                    dest = b.get_dest()
                    index = dest.get_index() if dest else None
                    outline.append({"level": b.level, "title": b.get_title().strip(),
                                    "page": index + 1 if index is not None else None})
            except Exception:  # noqa: BLE001 - bookmarks are optional
                outline = []
        finally:
            pdf.close()
        _cache.clear()
        _cache[key] = {"texts": texts, "meta": meta, "outline": outline}
    return _cache[key]


def _clean(cell):
    """One table cell as a line of text; a subscript on its own line is joined to its symbol
    ('t\\npd' -> 'tpd', 't Set-up time\\nsu' -> 'tsu Set-up time')."""
    if cell is None:
        return ""
    s = str(cell).strip()
    m = re.match(r"^([tfCV])(?:\s+(.*?))?\n([A-Za-z]{1,6}[′']?(?:\(\w+\))?)$", s, re.S)
    if m:
        desc = (m.group(2) or "").replace("\n", " ").strip()
        return f"{m.group(1)}{m.group(3)}" + (f" {desc}" if desc else "")
    return re.sub(r"\s*\n\s*", " ", s)


def _score(text):
    low = text.lower()
    if low.count("....") >= 5:
        return 0, []  # the table of contents
    words = [w for w in TIMING_WORDS if w in low]
    return len(words) * 3 + min(len(SYMBOL.findall(text)), 20) // 4 + min(len(UNITS.findall(text)), 20) // 4, words


def _headings(text):
    """Section headings and figure captions on a page."""
    heads, figures = [], []
    for line in text.splitlines():
        line = line.strip()
        if FIGURE.match(line):
            figures.append(line[:120])
        elif HEADING.match(line) and any(w in line.lower() for w in ("timing", "characteristics", "switching", "requirements", "ac ")):
            heads.append(line[:120])
    return heads, figures


def open_datasheet(path, limit=12):
    """Overview: title, pages, bookmarks, and the pages most likely to hold the timing information."""
    doc = _open(path)
    texts = doc["texts"]
    if not any(t.strip() for t in texts):
        return {"path": path, "pages": len(texts), "text": False,
                "message": "The PDF has no text layer (a scanned document): the tables cannot be read from it. "
                           "Ask the student for the page with the timing table as an image, or for the values."}
    first = [l.strip() for l in texts[0].splitlines() if l.strip()][:6]
    pages = []
    for i, t in enumerate(texts, 1):
        score, words = _score(t)
        if score >= 3:
            heads, figures = _headings(t)
            pages.append({"page": i, "score": score, "found": words[:6], "headings": heads[:6], "figures": figures[:6]})
    pages.sort(key=lambda p: -p["score"])
    outline = doc["outline"]
    timing_outline = [o for o in outline if any(w in o["title"].lower() for w in ("timing", "characteristic", "switching", "ac ", "interface"))]
    return {"path": path, "pages": len(texts), "text": True, "title": doc["meta"].get("Title") or " / ".join(first[:2]),
            "first_lines": first, "outline": timing_outline or outline[:40],
            "timing_pages": sorted(pages[:limit], key=lambda p: p["page"]),
            "next": "Read the tables with datasheet_timing (the pages above, or the ones the student points to)."}


def _numeric(cell):
    return bool(cell) and bool(NUMBER.match(cell.split(" ")[0]))


def _table(raw):
    """A pdfplumber table as {columns, rows}: header rows (before the first row with a number) joined
    into one label per column, merged text cells filled down, empty rows dropped."""
    raw = [r for r in raw if r and any(c not in (None, "") for c in r)]
    if not raw:
        return None
    width = max(len(r) for r in raw)
    raw = [list(r) + [None] * (width - len(r)) for r in raw]
    nhead = 0
    while nhead < min(len(raw), 3) and not any(_numeric(_clean(c)) for c in raw[nhead][1:]):
        nhead += 1
    columns = [""] * width
    for r in raw[:nhead]:
        left = ""
        for j, c in enumerate(r):
            # None in a header row: the cell on the left is merged over this column
            label = _clean(c) if c is not None else left
            left = label
            if label and not columns[j].endswith(label):
                columns[j] = (columns[j] + " " + label).strip()
    body = [[_clean(c) for c in r] for r in raw[nhead:]]
    # The columns before the values (parameter, symbol, condition, load, supply) are merged vertically:
    # fill them down. The values start at the first MIN/TYP/MAX column, else at the first numeric column.
    first_val = next((j for j, c in enumerate(columns) if re.search(r"\b(MIN|TYP|MAX)", c, re.I)), None)
    if first_val is None:
        first_val = next((j for j in range(1, width) if any(_numeric(r[j]) for r in body)), width)
    above = [""] * width
    rows, spans = [], 0
    for r in body:
        for j in range(first_val):
            if r[j]:
                above[j] = r[j]
                for k in range(j + 1, first_val):
                    above[k] = ""  # a new parameter starts its own sub-rows
            else:
                r[j] = above[j]
        # Several numbers in one value cell: the cell spans merged columns, which ones only the page shows
        spans += sum(1 for c in r[first_val:] if len(re.findall(r"\d+(?:\.\d+)?", c)) > 1 and not UNITS.search(c))
        rows.append(r)
    if not rows:
        return None
    table = {"columns": columns, "rows": rows}
    if spans:
        table["merged_values"] = (f"{spans} value cells hold several numbers (e.g. '50 160'): they span merged "
                                  "columns, and which columns they belong to is visible only on the page")
    return table


def timing_tables(path, pages=None, max_pages=6):
    """The timing tables of the given pages (or of the best-scoring pages) with headings, figure
    captions and footnotes; the page text where a page has no ruled table."""
    import pdfplumber
    doc = _open(path)
    texts = doc["texts"]
    if pages:
        pages = [p for p in pages if 1 <= p <= len(texts)]
    else:
        scored = sorted(((_score(t)[0], i) for i, t in enumerate(texts, 1)), reverse=True)
        pages = sorted(i for s, i in scored[:max_pages] if s >= 3)
    result = []
    with pdfplumber.open(path) as pdf:
        for n in pages:
            page = pdf.pages[n - 1]
            text = texts[n - 1]
            heads, figures = _headings(text)
            tables = []
            for raw in page.extract_tables():
                t = _table(raw)
                if t and (SYMBOL.search(" ".join(" ".join(r) for r in t["rows"]) + " ".join(t["columns"]))
                          or UNITS.search(" ".join(" ".join(r) for r in t["rows"]))):
                    tables.append(t)
            entry = {"page": n, "headings": heads, "figures": figures, "tables": tables,
                     "notes": [l.strip()[:300] for l in text.splitlines() if NOTE.match(l.strip())][:15]}
            if not tables:
                # No ruled table: the whole page text, so that no row is lost (symbols like tac3 or toh3 vary too much to filter)
                entry["text"] = text
            result.append(entry)
    return {"path": path, "pages": result,
            "reading": ("Tables as printed: columns are joined header labels (e.g. supply voltage, temperature range, "
                        "part or speed grade, MIN/TYP/MAX); merged text cells are filled down. Check a value on the page "
                        "itself before it is used (datasheet_page), and the test conditions (VCC, temperature, load capacitance). "
                        "A parameter not found here: datasheet_search for it, and if it is not in the datasheet, report it as not "
                        "found (what was searched, where); never estimate it.")}


def search(path, text, limit=30):
    """Lines that contain the text (case-insensitive), with their pages: a parameter, a symbol or a footnote."""
    doc = _open(path)
    # A short text (a symbol such as th or tAC) as a whole word, with optional spaces inside; longer text anywhere
    letters = [re.escape(c) for c in text.replace(" ", "")]
    edge = r"\b" if len(letters) <= 4 else ""
    pattern = re.compile(edge + r"\s?".join(letters) + edge, re.I)
    hits = []
    for i, t in enumerate(doc["texts"], 1):
        for line in t.splitlines():
            if pattern.search(line):
                hits.append({"page": i, "line": line.strip()[:300]})
                if len(hits) >= limit:
                    return {"path": path, "text": text, "hits": hits, "more": True}
    return {"path": path, "text": text, "hits": hits}


def page_text(path, page, layout=False):
    """The full text of one page. With layout, the text keeps the horizontal positions (spaces), so a value
    alone in its row stays under its column header (MIN, TYP, MAX)."""
    doc = _open(path)
    if not 1 <= page <= len(doc["texts"]):
        raise ValueError(f"page {page} is outside 1..{len(doc['texts'])}")
    if not layout:
        return {"path": path, "page": page, "text": doc["texts"][page - 1]}
    import pdfplumber
    with pdfplumber.open(path) as pdf:
        text = pdf.pages[page - 1].extract_text(layout=True) or ""
    lines = [line.rstrip() for line in text.splitlines()]
    return {"path": path, "page": page, "layout": True, "text": "\n".join(l for l in lines if l.strip())}


def board_devices(device=None):
    """Timing notes of the DE1-SoC devices (checked against the board documents and named datasheet
    revisions): the list of devices, or the notes of one."""
    path = os.path.join(os.path.dirname(__file__), "data", "de1_soc_timing.md")
    with open(path, encoding="utf-8") as f:
        text = f.read()
    intro, *parts = re.split(r"^## ", text, flags=re.M)
    sections = {p.split("\n", 1)[0].strip(): "## " + p.strip() for p in parts}
    if not device:
        return {"devices": list(sections), "rule": intro.split("\n", 2)[-1].strip()}
    key = device.strip().lower()
    matches = [k for k in sections if key == k or key in k]
    if not matches:
        return {"ok": False, "devices": list(sections),
                "message": f"No notes for '{device}'. Devices with notes: {', '.join(sections)}. For any other part only "
                           "its datasheet counts (the student provides it)."}
    return {"device": matches[0], "notes": sections[matches[0]], "rule": intro.split("\n", 2)[-1].strip()}
