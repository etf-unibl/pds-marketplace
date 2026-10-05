"""Course documents of the student's course repository: topic pages, guides and video examples.

The documents live on the main branch of the course repository (docs/, docs/topics/,
video-tutorials/). Students usually work on branches made from the assignments branch, where
these folders do not exist, so the files are read from the working copy if present and otherwise
from origin/main (or main) with git show. Nothing is cached or changed.

Topic pages have the same structure in both languages (Serbian and English template); section
names are mapped to these keys: contents, key_terms, explanation, example, common_mistakes,
self_check, further_material.
"""

import os
import re

from . import repo

SECTIONS = {
    "sadržaj": "contents", "contents": "contents",
    "ključni pojmovi": "key_terms", "key terms": "key_terms",
    "objašnjenje": "explanation", "explanation": "explanation",
    "primjer": "example", "example": "example",
    "česte greške": "common_mistakes", "common mistakes": "common_mistakes",
    "provjera znanja": "self_check", "self-check": "self_check",
    "dodatni materijali": "further_material", "further material": "further_material",
}
REFS = ("origin/main", "main")
NOTE = re.compile(r"^>\s*\*\*(Napomena o greš\w+ u videu|Note on (?:an error|errors) in the video|Napomena|Note):\*\*\s*(.*)$", re.M)


class Docs:
    """Access to the documents of one course repository (working copy or a git ref)."""

    def __init__(self, path="."):
        self.root = repo.find_root(path) or os.path.abspath(path)
        self.ref = None
        if not os.path.isdir(os.path.join(self.root, "docs", "topics")):
            for ref in REFS:
                if repo.git(["ls-tree", "--name-only", ref, "docs/topics/"], cwd=self.root, check=False):
                    self.ref = ref
                    break

    @property
    def available(self):
        return self.ref is not None or os.path.isdir(os.path.join(self.root, "docs", "topics"))

    @property
    def source(self):
        return f"git {self.ref}" if self.ref else "working copy"

    def list(self, folder):
        if self.ref:
            out = repo.git(["ls-tree", "--name-only", f"{self.ref}", folder.rstrip("/") + "/"], cwd=self.root, check=False)
            return sorted(os.path.basename(p) for p in out.splitlines())
        full = os.path.join(self.root, folder)
        return sorted(os.listdir(full)) if os.path.isdir(full) else []

    def list_tree(self, folder):
        """All file paths below folder (relative to the repository root)."""
        if self.ref:
            out = repo.git(["ls-tree", "-r", "--name-only", self.ref, folder.rstrip("/") + "/"], cwd=self.root, check=False)
            return sorted(out.splitlines())
        base = os.path.join(self.root, folder)
        return sorted(os.path.relpath(os.path.join(d, f), self.root).replace(os.sep, "/") for d, _, fs in os.walk(base) for f in fs)

    def read(self, path):
        if self.ref:
            return repo.show_file(self.root, self.ref, path)
        full = os.path.join(self.root, path)
        if not os.path.isfile(full):
            return None
        with open(full, encoding="utf-8", errors="replace") as f:
            return f.read()


def _unavailable(docs):
    return {"ok": False, "message": "The course documents were not found. Run this inside your course repository; "
            "if you cloned only the assignments branch, fetch main first (git fetch origin main)."}


def parse_page(text):
    """Splits a topic page into title, info line and sections (by '### ' headings)."""
    lines = text.split("\n")
    title = next((l[3:].strip() for l in lines if l.startswith("## ")), "")
    m = re.match(r"^(\d+)\.\s*(.*)$", title)
    page = {"number": int(m.group(1)) if m else None, "title": m.group(2) if m else title, "sections": {}}
    info = next((l for l in lines if l.startswith("**Video:**")), "")
    video = re.search(r"\]\((https://www\.youtube\.com/watch\?v=[\w-]+)\)\s*\(([\d:]+)", info)
    if video:
        page["video"], page["duration"] = video.group(1), video.group(2)
    code = re.search(r"\[`(video-tutorials/[^`]+)`\]", info)
    page["code_folder"] = code.group(1) if code else None
    current = None
    for line in lines:
        if line.startswith("### "):
            current = SECTIONS.get(line[4:].strip().lower(), line[4:].strip())
            page["sections"][current] = []
        elif current:
            page["sections"][current].append(line)
    page["sections"] = {k: "\n".join(v).strip() for k, v in page["sections"].items()}
    page["language"] = "sr" if "### Sadržaj" in text else "en"
    return page


def _pages(docs):
    pages = []
    for name in docs.list("docs/topics"):
        if not name.endswith(".md"):
            continue
        text = docs.read(f"docs/topics/{name}")
        if text:
            page = parse_page(text)
            page["file"] = f"docs/topics/{name}"
            page["text"] = text
            pages.append(page)
    return sorted(pages, key=lambda p: p["number"] or 0)


def list_topics(path="."):
    docs = Docs(path)
    if not docs.available:
        return _unavailable(docs)
    return {"ok": True, "source": docs.source, "topics": [
        {"number": p["number"], "title": p["title"], "file": p["file"], "video": p.get("video"), "duration": p.get("duration"),
         "code_folder": p["code_folder"], "language": p["language"]} for p in _pages(docs)]}


def get_topic(number, section=None, path="."):
    docs = Docs(path)
    if not docs.available:
        return _unavailable(docs)
    page = next((p for p in _pages(docs) if p["number"] == int(number)), None)
    if not page:
        return {"ok": False, "message": f"There is no topic page {number}."}
    result = {"ok": True, "number": page["number"], "title": page["title"], "file": page["file"], "video": page.get("video"),
              "code_folder": page["code_folder"], "sections": list(page["sections"])}
    if section:
        key = SECTIONS.get(section.lower(), section)
        if key not in page["sections"]:
            return {"ok": False, "message": f"Section {section} not found; sections: {', '.join(page['sections'])}"}
        result["content"] = page["sections"][key]
    else:
        result["content"] = page["text"]
    return result


def contents_entries(section_text, video=None):
    """Rows of the Contents table: {time, url, topic}."""
    rows = []
    for m in re.finditer(r"^\|\s*\[([\d:]+)\]\((\S+?)\)\s*\|\s*(.*?)\s*\|\s*$", section_text, re.M):
        rows.append({"time": m.group(1), "url": m.group(2), "topic": m.group(3)})
    return rows


def search_topics(query, path=".", limit=8):
    """Finds topic pages and video moments about a query (all words must appear in a paragraph)."""
    docs = Docs(path)
    if not docs.available:
        return _unavailable(docs)
    words = [w.lower() for w in re.findall(r"[\w'-]+", query) if len(w) > 1]
    if not words:
        return {"ok": False, "message": "Empty query."}
    hits = []
    for page in _pages(docs):
        for key, body in page["sections"].items():
            if key == "contents":
                continue  # the contents table is searched row by row below (video moments)
            for para in re.split(r"\n\s*\n", body):
                low = para.lower()
                if all(w in low for w in words):
                    score = sum(low.count(w) for w in words) + (3 if key in ("key_terms", "contents") else 0)
                    hits.append({"score": score, "topic": page["number"], "title": page["title"], "section": key,
                                 "text": para.strip()[:600], "file": page["file"]})
        for row in contents_entries(page["sections"].get("contents", "")):
            if all(w in row["topic"].lower() for w in words):
                hits.append({"score": 10, "topic": page["number"], "title": page["title"], "section": "video",
                             "text": f"{row['time']} {row['topic']}", "url": row["url"], "file": page["file"]})
    hits.sort(key=lambda h: -h["score"])
    seen, result = set(), []
    for h in hits:
        k = (h["topic"], h["section"], h["text"][:80])
        if k not in seen:
            seen.add(k)
            h.pop("score")
            result.append(h)
        if len(result) >= limit:
            break
    return {"ok": True, "query": query, "results": result, "source": docs.source}


TERM = re.compile(r"^-\s+\*\*(?P<term>.+?)\*\*\s*(?:\((?P<alt>[^)]*)\))?\s*-\s*(?P<desc>.+)$")


def glossary(term=None, path="."):
    """Key terms of all topic pages (term, alternative names, explanation, topic)."""
    docs = Docs(path)
    if not docs.available:
        return _unavailable(docs)
    entries = []
    for page in _pages(docs):
        for line in page["sections"].get("key_terms", "").splitlines():
            m = TERM.match(line.strip())
            if m:
                entries.append({"term": m.group("term").strip("`*"), "alt": re.sub(r"[*`]", "", m.group("alt") or "") or None,
                                "description": m.group("desc").strip(), "topic": page["number"], "title": page["title"]})
    if term:
        t = term.lower()
        entries = [e for e in entries if t in e["term"].lower() or t in (e["alt"] or "").lower()]
    return {"ok": True, "count": len(entries), "terms": entries}


def self_check(topic=None, path=".", reveal=False):
    """Self-check questions of the topic pages; answers only when reveal is True."""
    docs = Docs(path)
    if not docs.available:
        return _unavailable(docs)
    result = []
    for page in _pages(docs):
        if topic is not None and page["number"] != int(topic):
            continue
        body = page["sections"].get("self_check", "")
        q_part, _, a_part = body.partition("<details>")
        questions = re.findall(r"^\d+\.\s+(.*)$", q_part, re.M)
        answers = re.findall(r"^\d+\.\s+(.*)$", a_part, re.M)
        for i, q in enumerate(questions):
            item = {"topic": page["number"], "title": page["title"], "number": i + 1, "question": q}
            if reveal and i < len(answers):
                item["answer"] = answers[i]
            result.append(item)
    return {"ok": True, "questions": result, "answers_included": reveal}


def video_notes(path="."):
    """Notes about errors in the videos and outdated tool versions, per topic."""
    docs = Docs(path)
    if not docs.available:
        return _unavailable(docs)
    notes = []
    for page in _pages(docs):
        for m in NOTE.finditer(page["text"]):
            notes.append({"topic": page["number"], "title": page["title"], "kind": m.group(1), "text": m.group(2)})
    return {"ok": True, "notes": notes}


def examples(topic=None, path="."):
    """Example code of the video tutorials (verified code; fixes of video errors are marked NOTE)."""
    docs = Docs(path)
    if not docs.available:
        return _unavailable(docs)
    folders = {}
    for page in _pages(docs):
        if page["code_folder"] and (topic is None or page["number"] == int(topic)):
            folders[page["number"]] = {"title": page["title"], "folder": page["code_folder"],
                                       "files": [f for f in docs.list_tree(page["code_folder"])]}
    return {"ok": True, "examples": folders, "source": docs.source,
            "note": "Code in video-tutorials/ is the code from the videos; corrections of errors in the videos are marked with NOTE comments."}


def read_example(file, path="."):
    docs = Docs(path)
    if not file.startswith("video-tutorials/") or ".." in file:
        return {"ok": False, "message": "Only files in video-tutorials/ can be read with this tool."}
    text = docs.read(file)
    if text is None:
        return {"ok": False, "message": f"{file} not found."}
    return {"ok": True, "file": file, "content": text, "notes": [l.strip() for l in text.splitlines() if "NOTE:" in l]}


def run_example(folder, path="."):
    """Analyses and simulates a video-tutorial example folder from the course repository (taken from
    the working copy or origin/main into a temporary folder, so the student's checkout is not touched)."""
    import tempfile

    from . import hdl
    folder = folder.strip("/")
    if not folder.startswith("video-tutorials/") or ".." in folder:
        return {"ok": False, "message": "Give a folder in video-tutorials/ (see tutorial_examples)."}
    docs = Docs(path)
    files = [f for f in docs.list_tree(folder) if f.lower().endswith((".vhd", ".vhdl", ".csv", ".txt", ".dat"))]
    if not files:
        return {"ok": False, "message": f"No files in {folder}."}
    with tempfile.TemporaryDirectory(prefix="pds-example-") as tmp:
        for f in files:
            dest = os.path.join(tmp, os.path.relpath(f, folder))
            os.makedirs(os.path.dirname(dest), exist_ok=True)
            with open(dest, "w", encoding="utf-8", newline="\n") as out:
                out.write(docs.read(f) or "")
        # examples are grouped in sub-folders (one design each); run each sub-folder that has VHDL files
        results = []
        for d, _, fs in os.walk(tmp):
            vhdl = [x for x in fs if x.lower().endswith((".vhd", ".vhdl"))]
            if not vhdl:
                continue
            rel = os.path.relpath(d, tmp).replace(os.sep, "/")
            name = folder if rel == "." else f"{folder}/{rel}"
            if any(os.path.splitext(x)[0].lower().endswith("_tb") for x in vhdl):
                r = hdl.run_testbenches(d)
                results.append({"folder": name, "kind": "testbench", "ok": r.get("ok"), "results": r.get("results"), "message": r.get("message")})
            else:
                r = hdl.analyze([d])
                results.append({"folder": name, "kind": "analysis", "ok": r.get("ok"), "errors": r.get("errors"), "message": r.get("message")})
    return {"ok": all(r["ok"] for r in results), "source": docs.source, "examples": results,
            "note": "Examples without a testbench are only analysed (VHDL-2008). Code with NOTE comments contains corrections of errors in the video."}


def course_doc(name=None, path="."):
    """A course guide from docs/ (e.g. assignment-submission, simulation-and-testing); without a name, the list."""
    docs = Docs(path)
    if not docs.available:
        return _unavailable(docs)
    names = [n[:-3] for n in docs.list("docs") if n.endswith(".md")]
    if not name:
        return {"ok": True, "documents": names}
    name = name[:-3] if name.endswith(".md") else name
    if name not in names:
        return {"ok": False, "message": f"No document {name}; documents: {', '.join(names)}"}
    return {"ok": True, "document": f"docs/{name}.md", "content": docs.read(f"docs/{name}.md")}
