"""Design documentation of the PDS course: Doxygen comments (--!) in VHDL files.

outline: the documented elements of a file (file, entity, generics, ports, architecture, declarations,
processes, instances) and the --! comment Doxygen attaches to each. check: the course requirements
(docs/design-documentation.md) and the pitfalls of Doxygen's VHDL parser, verified with Doxygen 1.9.5
(the version of the course's GitHub Pages workflow). skeleton: inserts a draft of the missing comments,
with the brief descriptions the assistant wrote and TODO placeholders for everything the student
writes; it only adds --! comments and verifies that no code changed. preview: the HTML documentation
built locally with the course Doxyfile, outside the repository.
"""

import difflib
import os
import re
import shutil
import subprocess

from . import repo

CI_DOXYGEN = "1.9.5"  # mattnotmitt/doxygen-action@v1.9.5 in .github/workflows/gh-pages.yml

DOC = re.compile(r"^\s*--!")
TODO = re.compile(r"\bTODO\b")
COMMAND = re.compile(r"^[@\\](\w+)\s*(.*)$")
KEYWORDS_END = {"process", "if", "loop", "case", "generate", "component", "record", "function", "procedure", "block",
                "units", "for", "protected", "package", "entity", "architecture"}

# Course requirements (docs/design-documentation.md, "Šta je potrebno dokumentovati")
REQUIRED_BRIEF = {"entity", "architecture", "package", "generic", "port", "process"}
RECOMMENDED_BRIEF = {"signal", "constant", "type", "subtype", "component", "function", "procedure", "instance", "alias",
                     "variable"}
REQUIRED_DETAILS = {"entity", "architecture"}
RECOMMENDED_DETAILS = {"package"}

DETAILS_HINT = {
    "entity": "what the circuit does, how it is used (inputs, outputs, reset, enable) and its timing "
              "(latency in clock cycles, when the outputs are valid)",
    "architecture": "how the circuit is implemented (structure, registers, state machine) and why",
    "package": "what the package provides and where it is used",
}
# The placeholder lines of a detailed description (short lines: the course limit is 132 characters)
DETAILS_TODO = {
    "entity": ["@details TODO: describe in your own words what the circuit does,",
               "how it is used (inputs, outputs, reset, enable) and its timing",
               "(latency in clock cycles, when the outputs are valid)."],
    "architecture": ["@details TODO: describe in your own words how the circuit is implemented",
                     "(structure, registers, state machine) and why."],
    "package": ["@details TODO: describe in your own words what the package provides and where it is used."],
}
MAX_LINE = 132  # [LineLength] of the course style (vhdl-style, length_001)
# Documented with a comment at the end of the line (single-line declarations)
TRAILING_KINDS = ("port", "generic", "signal", "constant", "variable")
# The course style requires a blank line above these (VSG type_010, function_006, ...)
BLANK_ABOVE = ("type", "subtype", "function", "procedure", "component", "alias")


def _split(text):
    """Lines without line ends, the line end of the file and whether the file ends with one."""
    nl = "\r\n" if "\r\n" in text else "\n"
    return text.splitlines(), nl, text.endswith(("\n", "\r"))


def _code(line):
    """The code part of a line (before a comment), with string literals kept intact."""
    in_str = False
    for i, ch in enumerate(line):
        if ch == '"':
            in_str = not in_str
        elif not in_str and line.startswith("--", i):
            return line[:i]
    return line


def _comment(line):
    """The comment of a line (from --), or ''."""
    return line[len(_code(line)):]


def _kind_of_line(line):
    t = line.strip()
    if not t:
        return "blank"
    if t.startswith("--!"):
        return "doc"
    if t.startswith("--"):
        return "comment"
    return "code"


def _doc_text(line):
    return re.sub(r"^\s*--!\s?", "", line).rstrip()


def _parse_doc(texts):
    """brief, details and flags of the text lines of one --! comment."""
    lines = [t.strip() for t in texts]
    brief, details, has_brief_cmd = None, [], False
    i = 0
    while i < len(lines):
        m = COMMAND.match(lines[i])
        if m and m.group(1) == "brief":
            has_brief_cmd = True
            part = [m.group(2)]
            i += 1
            while i < len(lines) and lines[i] and not COMMAND.match(lines[i]):
                part.append(lines[i])
                i += 1
            brief = " ".join(p for p in part if p).strip() or None
            continue
        if m and m.group(1) == "details":
            details.append(m.group(2))
        elif m and m.group(1) == "file":
            pass
        elif lines[i]:
            details.append(lines[i])
        i += 1
    details = [d for d in details if d]
    if not has_brief_cmd and len([t for t in lines if t and not COMMAND.match(t)]) == 1 and not any(
            COMMAND.match(t) for t in lines):
        brief, details = details[0], []  # a single --! line is the brief
    return {"brief": brief, "details": " ".join(details) or None,
            "multi_line_without_brief": not has_brief_cmd and brief is None and len(details) > 1}


def _preceding(lines, s):
    """The --! lines Doxygen attaches to the element starting at line s (blank lines and plain -- comments
    between are skipped, as Doxygen does), without a @file block; and whether a blank line splits them."""
    j, blocks, current = s - 1, [], []
    while j >= 0:
        k = _kind_of_line(lines[j])
        if k == "doc":
            current.insert(0, j)
        elif k == "blank":
            if current:
                blocks.insert(0, current)
                current = []
        elif k == "comment":
            pass
        else:
            break
        j -= 1
    if current:
        blocks.insert(0, current)
    for b, block in enumerate(blocks):
        if any("@file" in lines[x] or "\\file" in lines[x] for x in block):
            blocks = blocks[b + 1:]
            break
    doc = [x for b in blocks for x in b]
    # A --! comment at the end of the code line just above joins these lines into one block (Doxygen 1.9.5):
    # the element above loses its comment
    merged = j if doc and j >= 0 and doc[0] == j + 1 and _comment(lines[j]).lstrip().startswith("--!") else None
    return doc, len(blocks) > 1, merged


class _Parser:
    """Line-based reader of the documented VHDL elements (enough for course designs, not a full parser)."""

    def __init__(self, lines):
        self.lines = lines
        self.code = [_code(l) for l in lines]
        self.elements = []

    def add(self, kind, name, start, end=None, scope=None, names=None, mode=None):
        self.elements.append({"kind": kind, "name": name, "line": start, "end": end if end is not None else start,
                              "scope": scope, "names": names or [name], "mode": mode})

    def statement_end(self, i):
        """Index of the line where the statement starting at line i ends (first ';' outside parentheses)."""
        depth = 0
        for j in range(i, len(self.lines)):
            for ch in self.code[j]:
                if ch == "(":
                    depth += 1
                elif ch == ")":
                    depth -= 1
                elif ch == ";" and depth <= 0:
                    return j
        return len(self.lines) - 1

    def skip_to(self, i, pattern):
        for j in range(i, len(self.lines)):
            if re.match(pattern, self.code[j].strip(), re.I):
                return j
        return len(self.lines) - 1

    def interface(self, i, col, kind, scope):
        """generic ( ... ) or port ( ... ) starting at line i, column col: one element per declaration.
        Returns the line where the clause ends."""
        depth, started, chars = 0, False, []  # (line, char) of the clause content
        for j in range(i, len(self.lines)):
            text = self.code[j]
            for c in range(col if j == i else 0, len(text)):
                ch = text[c]
                if ch == "(":
                    depth += 1
                    if depth == 1 and not started:
                        started = True
                        continue
                elif ch == ")":
                    depth -= 1
                    if started and depth == 0:
                        self._interface_elements(chars, kind, scope)
                        return j
                if started:
                    chars.append((j, ch))
        self._interface_elements(chars, kind, scope)
        return len(self.lines) - 1

    def _interface_elements(self, chars, kind, scope):
        depth, part = 0, []
        parts = []
        for j, ch in chars:
            if ch == "(":
                depth += 1
            elif ch == ")":
                depth -= 1
            if ch == ";" and depth == 0:
                parts.append(part)
                part = []
            else:
                part.append((j, ch))
        parts.append(part)
        for part in parts:
            text = "".join(ch for _, ch in part)
            if ":" not in text:
                continue
            lines_of = [j for j, ch in part if not ch.isspace()]
            names_text, rest = text.split(":", 1)
            names = [n.strip() for n in names_text.replace("\n", " ").split(",") if n.strip()]
            names = [re.sub(r"^(signal|constant|variable)\s+", "", n, flags=re.I) for n in names]
            mode = re.match(r"\s*(in|out|inout|buffer|linkage)\b", rest, re.I)
            self.add(kind, names[0], lines_of[0], lines_of[-1], scope, names, mode.group(1).lower() if mode else None)

    def run(self):
        lines, i, scope, region = self.lines, 0, None, None
        n = len(lines)
        while i < n:
            t = self.code[i].strip()
            low = t.lower()
            if not t:
                i += 1
                continue
            m = re.match(r"^entity\s+(\w+)\s+is\b", t, re.I)
            if m:
                scope, region = ("entity", m.group(1)), "entity"
                self.add("entity", m.group(1), i)
                i += 1
                continue
            m = re.match(r"^architecture\s+(\w+)\s+of\s+(\w+)\s+is\b", t, re.I)
            if m:
                scope, region = ("architecture", m.group(1)), "decl"
                self.add("architecture", m.group(1), i, scope=m.group(2))
                i += 1
                continue
            m = re.match(r"^package\s+body\s+(\w+)", t, re.I)
            if m:
                i = self.skip_to(i + 1, r"^end(\s+package\s+body)?(\s+\w+)?\s*;") + 1
                scope = region = None
                continue
            m = re.match(r"^package\s+(\w+)\s+is\b", t, re.I)
            if m:
                scope, region = ("package", m.group(1)), "decl"
                self.add("package", m.group(1), i)
                i += 1
                continue
            if region == "entity":
                m = re.search(r"\b(generic|port)\s*\(", self.code[i], re.I)
                if m and not re.search(r"\bmap\b", self.code[i], re.I):
                    i = self.interface(i, m.start(), m.group(1).lower(), scope[1]) + 1
                    continue
                if re.match(r"^end\b", low):
                    scope = region = None
                i += 1
                continue
            if region == "decl":
                if re.match(r"^begin\b", low):
                    region = "body"
                    i += 1
                    continue
                if re.match(r"^end\b", low) and scope and scope[0] == "package":
                    scope = region = None
                    i += 1
                    continue
                m = re.match(r"^(signal|constant|subtype|alias|shared\s+variable)\s+(.+?)\s*:", t, re.I)
                if m and m.group(1).lower() != "subtype":
                    kind = "variable" if "variable" in m.group(1).lower() else m.group(1).lower()
                    names = [x.strip() for x in m.group(2).split(",")]
                    end = self.statement_end(i)
                    self.add(kind, names[0], i, end, scope[1], names)
                    i = end + 1
                    continue
                m = re.match(r"^(type|subtype)\s+(\w+)\b", t, re.I)
                if m:
                    self.add(m.group(1).lower(), m.group(2), i, scope=scope[1])
                    if re.search(r"\brecord\b", low) and not re.search(r"\bend\s+record\b", low):
                        i = self.skip_to(i + 1, r"^end\s+record\b") + 1
                    elif re.search(r"\bprotected\b", low):
                        i = self.skip_to(i + 1, r"^end\s+protected\b") + 1
                    else:
                        i = self.statement_end(i) + 1
                    continue
                m = re.match(r"^component\s+(\w+)", t, re.I)
                if m:
                    self.add("component", m.group(1), i, scope=scope[1])
                    i = self.skip_to(i + 1, r"^end\s+component\b") + 1
                    continue
                m = re.match(r"^(?:(?:pure|impure)\s+)?(function|procedure)\s+(\w+)", t, re.I)
                if m:
                    self.add(m.group(1).lower(), m.group(2), i, scope=scope[1])
                    end = self.statement_end(i)
                    body = any(re.search(r"\bis\b", self.code[j], re.I) for j in range(i, end + 1))
                    if body:
                        end = self.skip_to(i + 1, rf"^end(\s+{m.group(1)})?(\s+{m.group(2)})?\s*;")
                    i = end + 1
                    continue
                i = self.statement_end(i) + 1
                continue
            if region == "body":
                m = re.match(r"^end\b\s*(\w+)?", low)
                if m and (m.group(1) is None or m.group(1) not in KEYWORDS_END or m.group(1) == "architecture"):
                    scope = region = None
                    i += 1
                    continue
                m = re.match(r"^(?:(\w+)\s*:\s*)?(?:postponed\s+)?process\b", t, re.I)
                if m:
                    self.add("process", m.group(1), i, scope=scope[1])
                    i = self.skip_to(i + 1, r"^end\s+(postponed\s+)?process\b") + 1
                    continue
                m = re.match(r"^(\w+)\s*:\s*(.*)$", t)
                if m and not re.match(r"^(for|if|case|block)\b", m.group(2), re.I):
                    end = self.statement_end(i)
                    text = " ".join(self.code[i:end + 1]).lower()
                    if re.search(r"\b(port|generic)\s+map\b", text):
                        self.add("instance", m.group(1), i, end, scope[1])
                        i = end + 1
                        continue
                if re.search(r"\bgenerate\b|\bbegin\b", low) or re.match(r"^end\s+generate\b", low):
                    i += 1
                    continue
                i = self.statement_end(i) + 1
                continue
            i += 1
        return self.elements


def _key(e, seen):
    name = e["name"] or f"line{e['line'] + 1}"
    key = f"{e['kind']}:{name}"
    if key in seen:
        key = f"{key}@{e['line'] + 1}"
    seen.add(key)
    return key


def _elements(lines):
    elements, seen = _Parser(lines).run(), set()
    by_end = {e["end"]: e for e in elements}
    for e in elements:
        e["key"] = _key(e, seen)
        e["merged_into"] = None
        doc_lines, split, merged = _preceding(lines, e["line"])
        trailing = _comment(lines[e["end"]]).strip() if e["end"] < len(lines) else ""
        if not trailing.startswith("--!") and e["end"] != e["line"]:
            trailing = _comment(lines[e["line"]]).strip()
        e["texts"] = [_doc_text(lines[j]) for j in doc_lines]
        e["own_trailing"] = re.sub(r"^--!\s?", "", trailing) if trailing.startswith("--!") else None
        e["doc_lines"] = [j + 1 for j in doc_lines]
        e["trailing_doc"] = trailing.startswith("--!")
        e["split_block"] = split
        e["merged_from"] = by_end.get(merged) if merged is not None else None
        before = lines[e["line"] - 1].strip() if e["line"] > 0 else ""
        e["plain_comment"] = not e["texts"] and not e["trailing_doc"] and (
            before.startswith("--") or trailing.startswith("--"))
        e["plain_trailing"] = trailing.startswith("--") and not trailing.startswith("--!")
    for e in elements:
        prev = e["merged_from"]
        if prev is not None and prev is not e and prev["own_trailing"] is not None:
            # Doxygen joins the comment at the end of the line above with these lines and attaches all to e
            e["texts"] = [prev["own_trailing"]] + e["texts"]
            prev["own_trailing"] = None
            prev["merged_into"] = e["key"]
    for e in elements:
        texts = e["texts"] + ([e["own_trailing"]] if e["own_trailing"] is not None else [])
        e["doc"] = _parse_doc(texts) if texts else None
        e["todo"] = any(TODO.search(t) for t in texts)
    return elements


def _file_doc(lines):
    for i, l in enumerate(lines):
        if DOC.match(l) and ("@file" in l or "\\file" in l):
            block = [i]
            j = i + 1
            while j < len(lines) and _kind_of_line(lines[j]) == "doc":
                block.append(j)
                j += 1
            doc = _parse_doc([_doc_text(lines[x]) for x in block])
            return {"line": i + 1, "brief": doc["brief"], "todo": any(TODO.search(lines[x]) for x in block)}
    return None


def _read(path):
    with open(path, encoding="utf-8", errors="replace", newline="") as f:
        return f.read()


def _public(e):
    doc = e["doc"] or {}
    return {"key": e["key"], "kind": e["kind"], "name": e["name"], "line": e["line"] + 1,
            **({"names": e["names"]} if len(e["names"]) > 1 else {}), **({"mode": e["mode"]} if e["mode"] else {}),
            "brief": doc.get("brief"), "details": doc.get("details"),
            **({"todo": True} if e["todo"] else {}),
            "documented": bool(doc.get("brief") or doc.get("details"))}


def outline(path):
    """The documented elements of a VHDL file and the --! comment Doxygen attaches to each."""
    lines, _, _ = _split(_read(path))
    elements = _elements(lines)
    return {"path": path, "file_doc": _file_doc(lines), "elements": [_public(e) for e in elements],
            "testbench": _is_testbench(path),
            "keys": "Use these keys in docs_skeleton's briefs (one sentence each)."}


def _is_testbench(path):
    return bool(re.search(r"_tb\.vhdl?$", path, re.I))


def _orphans(lines, elements):
    """--! blocks that no element follows (Doxygen drops them without a warning) or that stand before a
    library / use clause (they document the library, not the design)."""
    starts = {e["line"] for e in elements} | {e["end"] for e in elements}
    found, i = [], 0
    while i < len(lines):
        if _kind_of_line(lines[i]) != "doc":
            i += 1
            continue
        j = i
        while j < len(lines) and _kind_of_line(lines[j]) in ("doc", "blank", "comment"):
            j += 1
        block_text = " ".join(lines[i:j])
        if "@file" in block_text or "\\file" in block_text:
            i = j
            continue
        nxt = _code(lines[j]).strip().lower() if j < len(lines) else ""
        if j >= len(lines) or re.match(r"^(end\b|begin\b|\)|library\b|use\b|context\b)", nxt):
            if j not in starts:
                what = "a library / use clause" if re.match(r"^(library|use|context)\b", nxt) else (
                    f"'{_code(lines[j]).strip()}'" if j < len(lines) else "the end of the file")
                found.append({"line": i + 1, "next": what})
        i = j
    return found


def _check_text(path, text):
    lines, _, _ = _split(text)
    elements = _elements(lines)
    findings = []

    def add(line, rule, level, message, key=None):
        findings.append({"line": line, "rule": rule, "level": level, "message": message, **({"key": key} if key else {})})

    fd = _file_doc(lines)
    if not fd:
        add(1, "file_doc_missing", "required", "No `--! @file` comment: the file has no page of its own in the "
            "documentation. Add `--! @file` and `--! @brief <one sentence>` after the file header.")
    elif not fd["brief"]:
        add(fd["line"], "file_brief_missing", "required", "The `@file` comment has no `@brief`.")
    elif fd["todo"]:
        add(fd["line"], "todo_left", "required", "The file comment still has a TODO placeholder.")
    for e in elements:
        doc, key, line, kind = e["doc"] or {}, e["key"], e["line"] + 1, e["kind"]
        label = f"{kind} `{e['name']}`" if e["name"] else f"{kind} at line {line}"
        if e["todo"]:
            add(line, "todo_left", "required", f"The comment of {label} still has a TODO placeholder: write it in your own words.", key)
        if e["split_block"]:
            add(e["doc_lines"][0], "split_block", "required", f"A blank line splits the comment of {label}: Doxygen joins the "
                "parts badly (e.g. `@details` shown as text in the brief, warning 'unknown command'). Keep the --! lines together.", key)
        if doc.get("multi_line_without_brief"):
            add(e["doc_lines"][0] if e["doc_lines"] else line, "multi_line_without_brief", "required",
                f"The comment of {label} has several --! lines but no `@brief`: Doxygen shows all of it as the detailed "
                "description and the summary tables stay empty. Start with `--! @brief <one sentence>`, then `--! @details ...`.", key)
        if e["merged_into"]:
            add(line, "merged_comment", "required", f"The --! comment at the end of this line joins the --! lines below it: "
                f"Doxygen attaches both to `{e['merged_into'].split(':', 1)[1]}` and {label} stays undocumented. Keep one "
                "style in a clause: either every comment at the end of its line, or every comment on its own line above.", key)
        if kind == "process" and not e["name"]:
            add(line, "process_without_label", "recommended", "The process has no label: Doxygen lists it as `PROCESS_<n>`. "
                "Give it a label that says what it does (e.g. `count_reg : process (clk_i) is`).", key)
        if len(e["names"]) > 1 and kind in ("signal", "constant", "port", "generic", "variable"):
            add(line, "shared_declaration", "recommended", f"`{', '.join(e['names'])}` share one declaration: Doxygen attaches the "
                f"comment only to `{e['names'][0]}`, the others stay undocumented. Declare each on its own line with its own comment.", key)
        missing_brief = not doc.get("brief") and not doc.get("multi_line_without_brief") and not e["merged_into"]
        if missing_brief and (kind in REQUIRED_BRIEF or kind in RECOMMENDED_BRIEF):
            level = "required" if kind in REQUIRED_BRIEF else "recommended"
            hint = " It has a plain `--` comment: Doxygen reads only `--!` comments." if e["plain_comment"] else ""
            add(line, "brief_missing", level, f"{label[0].upper() + label[1:]} has no brief description.{hint}", key)
        if kind in REQUIRED_DETAILS | RECOMMENDED_DETAILS and not doc.get("details"):
            level = "required" if kind in REQUIRED_DETAILS else "recommended"
            add(line, "details_missing", level, f"{label[0].upper() + label[1:]} has no detailed description (`@details`): "
                f"{DETAILS_HINT[kind]}.", key)
        brief = doc.get("brief") or ""
        if brief and (len(brief) > 120 or re.search(r"[.!?]\s+[A-ZČĆŽŠĐ]", brief)):
            add(line, "long_brief", "recommended", f"The brief of {label} is longer than one sentence: Doxygen shows all of it "
                "in the summary tables. Keep one sentence there and move the rest to `@details`.", key)
    for o in _orphans(lines, elements):
        add(o["line"], "orphan_doc", "required", f"This --! comment is followed by {o['next']}, not by a design element: Doxygen "
            "drops it (or attaches it to the library) without a warning. Put it right before the element it describes.")
    findings.sort(key=lambda f: f["line"])
    counts = {}
    for f in findings:
        counts[f["level"]] = counts.get(f["level"], 0) + 1
    return {"path": path, "elements": len(elements), "findings": findings, "counts": counts}


def check(path):
    """Course documentation requirements and Doxygen pitfalls of a VHDL file or of every design file
    (*_tb.vhd left out, as in the course Doxyfile) of a folder."""
    if os.path.isdir(path):
        files = sorted(os.path.join(path, f) for f in os.listdir(path) if re.search(r"\.vhdl?$", f, re.I))
    else:
        files = [path]
    if not files:
        raise FileNotFoundError(f"no VHDL files in {path}")
    results, testbenches = [], []
    for f in files:
        if _is_testbench(f):
            testbenches.append(os.path.basename(f))
            continue
        results.append(_check_text(f, _read(f)))
    out = {"files": results, "ok": True,
           "note": ("Checked: the course requirements (docs/design-documentation.md) and Doxygen's VHDL pitfalls, verified "
                    f"with Doxygen {CI_DOXYGEN} (GitHub Pages). Whether a description is correct, clear and complete is for "
                    "you to judge from the code: give advice, never rewrite the student's text.")}
    if testbenches:
        out["testbenches"] = {"files": testbenches, "note": "Testbenches are not in the generated documentation "
                              "(EXCLUDE_PATTERNS of the Doxyfile); they still need comments on what is tested and how."}
    return out


# ---- skeleton ----

def _validate_brief(key, text):
    if not isinstance(text, str):
        return "not a string"
    t = text.strip()
    if "\n" in t or "\r" in t:
        return "more than one line (a brief is one sentence)"
    if len(t) < 3 or len(t) > 120:
        return "a brief is one sentence of at most 120 characters"
    if "--" in t or t.startswith(("@", "\\")) or re.search(r"[@\\](details|brief|file|note|warning)\b", t):
        return "no comment markers or Doxygen commands in a brief (the details are the student's)"
    if TODO.search(t):
        return "leave out the brief instead of writing TODO: the tool writes the placeholder"
    return None


def _strip_docs(lines):
    """The code of a file without its --! comments (to verify that the skeleton changed no code)."""
    out = []
    for line in lines:
        if DOC.match(line):
            continue
        comment = _comment(line)
        if comment.lstrip().startswith("--!"):
            line = line[:len(line) - len(comment)]
        line = line.rstrip()
        if line:
            out.append(line)
    return out


def skeleton(path, briefs=None, write=False):
    """A draft of the missing documentation of a design file: --! comments with the given briefs (one
    sentence each, written by the assistant from the code) and TODO placeholders for the detailed
    descriptions and every brief not given. Adds comments only (existing comments and code stay as
    they are, verified). write=False returns the diff for the student to see first."""
    if not re.search(r"\.vhdl?$", path, re.I):
        raise ValueError(f"{path} is not a VHDL file")
    if _is_testbench(path):
        raise ValueError("testbenches are not part of the generated documentation (EXCLUDE_PATTERNS of the Doxyfile); "
                         "the skeleton is only for design files")
    if not os.path.isfile(path):
        raise FileNotFoundError(path)
    if not repo.find_root(os.path.dirname(os.path.abspath(path))):
        raise ValueError(f"{path} is not in a git repository: the skeleton is for the files of the course repository")
    briefs = dict(briefs or {})
    original = _read(path)
    lines, nl, final_nl = _split(original)
    elements = _elements(lines)
    keys = {e["key"]: e for e in elements} | {"file": None}
    rejected = {k: "unknown key (see docs_outline)" for k in briefs if k not in keys}
    for k, v in list(briefs.items()):
        if k in keys:
            reason = _validate_brief(k, v)
            if reason:
                rejected[k] = reason
    briefs = {k: v.strip() for k, v in briefs.items() if k not in rejected}

    before, trailing, after = {}, {}, {}  # line index -> lines to insert before / the line with its comment / lines after
    added, skipped, todos = [], [], 0
    pending = []  # (element, brief, added entry) of the trailing comments, placed once the comments above lines are known
    pending_ends = set()

    def joins_above(i):
        """The line above line i ends with a --! comment (the student's or a new one): Doxygen would join it with
        a comment inserted above line i."""
        return i > 0 and (_comment(lines[i - 1]).lstrip().startswith("--!") or i - 1 in pending_ends)

    def brief_of(key, what):
        nonlocal todos
        if key in briefs:
            return briefs[key], False
        todos += 1
        return f"TODO: one sentence on {what}", True

    def above(i, indent, block_lines, blank):
        """Comment lines above line i; blank: with a blank line between them and the element (the course style
        requires one above entity, architecture, type, function, ...; Doxygen still attaches the comment)."""
        block = [f"{indent}--! {t}" for t in block_lines]
        if blank:
            block.append("")
            if i > 0 and _kind_of_line(lines[i - 1]) != "blank" and not before.get(i):
                block.insert(0, "")
        before.setdefault(i, []).extend(block)

    if not _file_doc(lines):
        first = next((i for i, l in enumerate(lines) if _kind_of_line(l) == "code"), len(lines))
        text, todo = brief_of("file", "what this file contains")
        above(first, "", ["@file", f"@brief {text}"], True)
        added.append({"key": "file", "line": first + 1, "todo": todo})
    for e in elements:
        key, doc, i = e["key"], e["doc"] or {}, e["line"]
        indent = re.match(r"^\s*", lines[i]).group(0)
        label = f"{e['kind']} {e['name']}" if e["name"] else e["kind"]
        if e["kind"] in DETAILS_HINT:
            if not doc:
                text, todo = brief_of(key, f"the {label}")
                above(i, indent, [f"@brief {text}"] + DETAILS_TODO[e["kind"]], True)
                todos += 1
                added.append({"key": key, "line": i + 1, "todo": todo, "details": "TODO"})
            elif doc.get("brief") and not doc.get("details") and e["doc_lines"] and not e["split_block"]:
                last = e["doc_lines"][-1] - 1
                after.setdefault(last, []).extend(f"{indent}--! {t}" for t in DETAILS_TODO[e["kind"]])
                todos += 1
                added.append({"key": key, "line": last + 2, "todo": True, "details": "TODO"})
            elif doc and key in briefs:
                skipped.append({"key": key, "reason": "already documented: the student's comment is not changed"})
            continue
        if e["merged_into"]:
            skipped.append({"key": key, "reason": f"its --! comment at the end of the line is joined to the comment of "
                                                  f"`{e['merged_into'].split(':', 1)[1]}` below (Doxygen attaches both there): "
                                                  "the student fixes that first (docs_check, merged_comment)"})
            continue
        if doc:
            if key in briefs:
                skipped.append({"key": key, "reason": "already documented: the student's comment is not changed"})
            continue
        if len(e["names"]) > 1:
            skipped.append({"key": key, "reason": f"`{', '.join(e['names'])}` share one declaration: Doxygen would document "
                                                  "only the first name. The student splits the declaration first."})
            continue
        end = e["end"]
        if sum(1 for x in elements if x["line"] <= e["line"] <= x["end"] or x["line"] <= end <= x["end"]) > 1:
            skipped.append({"key": key, "reason": "shares its line with another declaration: a comment there would document "
                                                  "the other one. The student puts each declaration on its own line first."})
            continue
        if e["plain_trailing"]:
            skipped.append({"key": key, "reason": "has a plain `--` comment at the end of its line: the student changes `--` to "
                                                  "`--!` and the comment becomes its brief (Doxygen reads only --! comments)"})
            continue
        trailing_style = e["kind"] in TRAILING_KINDS and (e["kind"] in ("port", "generic") or i == end)
        blank = e["kind"] in BLANK_ABOVE
        if not trailing_style and not blank and joins_above(i):
            skipped.append({"key": key, "reason": "the line above ends with a --! comment: a comment above this line would be "
                                                  "joined to it (Doxygen attaches both here). The student documents it by hand."})
            continue
        what = {"port": f"port {e['name']} (meaning, active level, encoding)",
                "generic": f"generic {e['name']} (meaning, unit, range)",
                "process": f"what process {e['name']} does" if e["name"] else "what this process does"}.get(
            e["kind"], f"the role of {label}")
        text, todo = brief_of(key, what)
        entry = {"key": key, "line": i + 1, "todo": todo}
        added.append(entry)
        if e["kind"] == "process" and not e["name"]:
            skipped.append({"key": key, "reason": "the process has no label (Doxygen shows PROCESS_<n>): suggest one to the student"})
        if trailing_style:
            pending.append((e, text, entry))
            pending_ends.add(end)
        else:
            above(i, indent, [text], blank)

    # Trailing comments in one column per group of consecutive declarations, one space after the longest (the course
    # style aligns them: VSG entity_020 and the declaration rules). A blank or comment line, or a comment inserted above
    # a declaration, starts a new group. A comment that would make the line too long goes above the declaration, unless
    # the line above ends with a --! comment (Doxygen would join them): then it is left to the student.
    ends = {x["end"] for x in elements if x["kind"] in TRAILING_KINDS}
    realign = set()
    while pending:
        columns, moved = {}, None
        for e, text, entry in pending:
            lo = hi = e["end"]
            while lo - 1 in ends and not before.get(lo) and lo - 1 not in after:
                lo -= 1
            while hi + 1 in ends and not before.get(hi + 1) and hi not in after:
                hi += 1
            col = max(len(_code(lines[x]).rstrip()) + 1 for x in range(lo, hi + 1))
            if col + 4 + len(text) > MAX_LINE:
                moved = (e, text, entry)
                break
            columns[e["end"]] = (col, lo, hi)
        if moved:
            pending.remove(moved)
            e, text, entry = moved
            pending_ends.discard(e["end"])
            if joins_above(e["line"]):
                added.remove(entry)
                todos -= entry["todo"]
                skipped.append({"key": e["key"], "reason": "too long for the end of the line, and a comment above would be "
                                                           "joined to the --! comment of the line above: the student documents it"})
            else:
                above(e["line"], re.match(r"^\s*", lines[e["line"]]).group(0), [text], False)
            continue
        for e, text, entry in pending:
            col, lo, hi = columns[e["end"]]
            code = _code(lines[e["end"]]).rstrip()
            trailing[e["end"]] = code + " " * (col - len(code)) + f"--! {text}"
            for x in range(lo, hi + 1):
                if x not in pending_ends and _comment(lines[x]).strip() and len(_code(lines[x])) != col:
                    realign.add(x + 1)
        break

    new, moved_to = [], {}
    for i, line in enumerate(lines + [None]):
        new.extend(before.get(i, []))
        if line is None:
            break
        moved_to[i + 1] = len(new) + 1
        new.append(trailing.get(i, line))
        new.extend(after.get(i, []))
    if _strip_docs(new) != _strip_docs(lines):
        raise RuntimeError("internal check failed: the skeleton would change code; nothing was written")
    text = nl.join(new) + (nl if final_nl else "")
    diff = "".join(difflib.unified_diff([l + "\n" for l in lines], [l + "\n" for l in new], "a/" + os.path.basename(path),
                                        "b/" + os.path.basename(path), n=1))
    result = {"path": path, "written": False, "added": added, "skipped": skipped, "todo_placeholders": todos,
              "diff": diff[:20000] or "(nothing to add: every element is already documented)",
              **({"rejected_briefs": rejected} if rejected else {}),
              **({"realign": f"Lines {', '.join(str(moved_to[x]) for x in sorted(realign))} keep the student's comment in another column than "
                             "the new comments next to them: vhdl-style reports it, vhdl-style --fix aligns them."} if realign else {})}
    if write and added:
        with open(path, "w", encoding="utf-8", newline="") as f:
            f.write(text)
        result["written"] = True
    result["next"] = ("Show the diff. " + ("The student fills every TODO in their own words; docs_check lists what is left. "
                      if todos else "") + "Then: vhdl-style on the task folder and docs_preview to see the pages. "
                      "The skeleton's comments need no AI-assisted-by line in the commit.")
    return result


# ---- preview ----

def find_doxygen():
    """The doxygen executable: PDS_DOXYGEN, the PATH, or the default Windows install folder."""
    for c in (os.environ.get("PDS_DOXYGEN"), shutil.which("doxygen"),
              os.path.join(os.environ.get("ProgramFiles", r"C:\Program Files"), "doxygen", "bin", "doxygen.exe")):
        if c and os.path.isfile(c):
            return c
    return None


def preview(target=None, root=None, timeout=300):
    """The HTML documentation built with the course Doxyfile (assignments/Doxyfile), as GitHub Pages builds
    it, into <repository>-docs next to the repository. target: a task folder or file to build only that,
    or None for all of assignments/."""
    root = repo.find_root(os.path.abspath(target if target and os.path.isdir(target) else
                                          os.path.dirname(os.path.abspath(target)) if target else (root or ".")))
    if not root:
        raise ValueError("not in a git repository: run it in the course repository")
    root = os.path.normpath(root)
    work = os.path.join(root, "assignments")
    doxyfile = os.path.join(work, "Doxyfile")
    if not os.path.isfile(doxyfile):
        raise FileNotFoundError("assignments/Doxyfile is missing: it is on the assignments branch and the task branches "
                                "made from it (git switch to your task branch)")
    exe = find_doxygen()
    if not exe:
        return {"ok": False, "error": "doxygen not found",
                "message": "Doxygen is not installed (or not on the PATH). Install it from https://www.doxygen.nl/download.html "
                           "(Windows: the setup program, or `winget install DimitriVanHeesch.Doxygen`), open a new terminal and "
                           f"start the AI tool again. GitHub Pages uses Doxygen {CI_DOXYGEN}.",
                "guide": "docs/design-documentation.md, Lokalni pregled dokumentacije"}
    out = os.path.join(os.path.dirname(root), os.path.basename(root) + "-docs")
    os.makedirs(out, exist_ok=True)
    log = os.path.join(out, "warnings.txt")
    if os.path.exists(log):
        os.remove(log)
    cfg = _read(doxyfile)
    cfg += f'\nOUTPUT_DIRECTORY = "{out}"\nWARN_LOGFILE = "{log}"\nQUIET = YES\n'
    if target:
        cfg += f'INPUT = "{os.path.abspath(target)}"\n'
    r = subprocess.run([exe, "-"], input=cfg, text=True, capture_output=True, cwd=work, timeout=timeout)
    version = subprocess.run([exe, "--version"], text=True, capture_output=True).stdout.split()[0:1]
    warnings = []
    if os.path.exists(log):
        for line in _read(log).splitlines():
            if line.strip() and "has become obsolete" not in line and "doxygen -u" not in line:
                warnings.append(line.replace(root.replace("\\", "/") + "/", "").replace(root + os.sep, ""))
    index = os.path.join(out, "html", "index.html")
    pages = []
    files = ([os.path.join(target, f) for f in os.listdir(target)] if target and os.path.isdir(target) else [target] if target else [])
    for f in files:
        if f and re.search(r"\.vhdl?$", f, re.I) and not _is_testbench(f):
            lines, _, _ = _split(_read(f))
            for e in _elements(lines):
                if e["kind"] in ("entity", "package"):
                    page = os.path.join(out, "html", "class" + e["name"].lower().replace("_", "__") + ".html")
                    if os.path.exists(page):
                        pages.append({"design_unit": e["name"], "page": page})
    result = {"ok": r.returncode == 0 and os.path.exists(index), "index": index, "pages": pages,
              "doxygen": version[0] if version else None, "warnings": warnings[:50],
              "command": "cd assignments; doxygen Doxyfile   (the course guide; writes assignments/html, not committed)",
              "note": f"Built into {out}, outside the repository. Open the index (or a page) in a web browser; "
                      "the design units are in the menu Design Unit List."}
    if result["doxygen"] and result["doxygen"] != CI_DOXYGEN:
        result["version_note"] = (f"Doxygen {result['doxygen']} here, {CI_DOXYGEN} on GitHub Pages: the pages may look slightly "
                                  "different; check the published page after the merge.")
    if r.returncode != 0:
        result["error"] = (r.stderr or r.stdout)[-2000:]
    return result
