import asyncio
import os
import shutil
import subprocess
import sys

import pytest

from pds_tools import hdl, topics

PAGE = """## 5. Sekvencijalne VHDL naredbe

**Video:** [Sekvencijalne VHDL naredbe](https://www.youtube.com/watch?v=oH_dKclt0WU) (59:41) · **Kod:** [`video-tutorials/part-2/video-tutorial-05`](../../video-tutorials/part-2/video-tutorial-05) · **Vezana uputstva:** x

### Sadržaj

| Vrijeme | Tema |
| ---: | ------ |
| [47:12](https://www.youtube.com/watch?v=oH_dKclt0WU&t=2832s) | Leč kola u `case` naredbi |

### Ključni pojmovi

- **Leč** (*latch*) - memorijski element koji sinteza nepoželjno generiše.
- **`after`** - kašnjenje dodjele signalu.

### Objašnjenje

Bez grane `else` sinteza generiše leč.

> **Napomena o grešci u videu:** Ulaznom portu se ne može dodijeliti vrijednost.

### Primjer

x

### Česte greške

- **`if` bez `else`**: leč.

### Provjera znanja

1. Zašto nastaje leč?
2. Šta je varijabla?

<details>
<summary>Odgovori</summary>

1. Izlaz nije dodijeljen u svim granama.
2. Objekat lokalan za proces.

</details>

### Dodatni materijali

- x
"""


def _git(cwd, *args):
    subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True)


@pytest.fixture
def course(tmp_path):
    """A course repository with the topic page on main and a working branch without docs (like assignments)."""
    root = tmp_path / "course"
    (root / "docs" / "topics").mkdir(parents=True)
    (root / "docs" / "topics" / "05-sequential-statements.md").write_text(PAGE, encoding="utf-8")
    (root / "docs" / "assignment-submission.md").write_text("# Predaja\n", encoding="utf-8")
    ex = root / "video-tutorials" / "part-2" / "video-tutorial-05" / "case_demo"
    ex.mkdir(parents=True)
    (ex / "case_demo.vhd").write_text("-- NOTE: corrected compared to the video\nentity case_demo is end case_demo;\n", encoding="utf-8")
    _git(root, "init", "-q", "-b", "main")
    _git(root, "-c", "user.name=t", "-c", "user.email=t@t", "add", ".")
    _git(root, "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-q", "-m", "docs")
    _git(root, "switch", "-q", "--orphan", "work")
    return root


def test_topics_from_git_ref_when_not_in_working_copy(course):
    lst = topics.list_topics(course)
    assert lst["source"] == "git main" and lst["topics"][0]["number"] == 5
    assert lst["topics"][0]["code_folder"] == "video-tutorials/part-2/video-tutorial-05"


def test_search_glossary_quiz_notes_examples(course):
    hits = topics.search_topics("leč case", course)["results"]
    assert hits[0]["section"] == "video" and hits[0]["url"].endswith("t=2832s")
    g = topics.glossary("latch", course)
    assert g["count"] == 1 and g["terms"][0]["term"] == "Leč" and g["terms"][0]["alt"] == "latch"
    q = topics.self_check(5, course)
    assert [x["question"] for x in q["questions"]] == ["Zašto nastaje leč?", "Šta je varijabla?"] and "answer" not in q["questions"][0]
    assert topics.self_check(5, course, reveal=True)["questions"][1]["answer"] == "Objekat lokalan za proces."
    assert topics.video_notes(course)["notes"][0]["kind"] == "Napomena o grešci u videu"
    ex = topics.examples(5, course)["examples"][5]["files"]
    assert ex == ["video-tutorials/part-2/video-tutorial-05/case_demo/case_demo.vhd"]
    r = topics.read_example(ex[0], course)
    assert r["notes"] and topics.read_example("docs/x.md", course)["ok"] is False
    assert topics.get_topic(5, "common_mistakes", course)["content"].startswith("- **`if` bez `else`**")
    assert "assignment-submission" in topics.course_doc(None, course)["documents"]


TB_DIR = os.path.join(os.path.dirname(__file__), "fixtures", "tb")


@pytest.mark.skipif(not shutil.which("ghdl"), reason="GHDL not installed")
def test_run_testbenches_like_ci_and_leave_folder_unchanged(tmp_path):
    folder = tmp_path / "12"
    shutil.copytree(TB_DIR, folder)
    before = sorted(os.listdir(folder))
    r = hdl.run_testbenches(str(folder))
    assert [(x["testbench"], x["passed"]) for x in r["results"]] == [("inv_tb", True)]
    assert sorted(os.listdir(folder)) == before
    (folder / "inv.vhd").write_text((folder / "inv.vhd").read_text().replace("not a", "a"))
    bad = hdl.run_testbenches(str(folder))
    assert bad["ok"] is False and bad["results"][0]["messages"][0]["severity"] == "error"
    a = hdl.analyze([str(folder / "inv.vhd")])
    assert a["ok"]


def test_list_testbenches_name_rule(tmp_path):
    (tmp_path / "x_tb.vhd").write_text("entity other_tb is end other_tb;")
    r = hdl.list_testbenches(str(tmp_path))
    assert r["ok"] is False and r["testbenches"][0]["entity"] == "other_tb"


def test_mcp_server_over_stdio(course):
    from mcp.client.session import ClientSession
    from mcp.client.stdio import StdioServerParameters, stdio_client

    async def run():
        params = StdioServerParameters(command=sys.executable, args=["-m", "pds_tools.mcp_server", "--profile", "learning"], cwd=str(course))
        async with stdio_client(params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                names = [t.name for t in (await session.list_tools()).tools]
                result = await session.call_tool("glossary", {"term": "leč"})
                return names, result

    names, result = asyncio.run(run())
    assert "topics_search" in names and "repo_state" not in names
    assert "Leč" in result.content[0].text


def test_fallback_workdir_skips_plugin_folder(course, tmp_path, monkeypatch):
    # Copilot CLI starts plugin servers in the plugin folder: that folder (even inside a git repository)
    # is skipped and PWD is used
    from pds_tools import mcp_server
    plugin = os.path.join(course, "plugin")
    os.makedirs(plugin)
    monkeypatch.chdir(plugin)
    monkeypatch.setenv("COPILOT_PLUGIN_ROOT", plugin)
    monkeypatch.setenv("PWD", str(course))
    monkeypatch.delenv("CLAUDE_PLUGIN_ROOT", raising=False)
    monkeypatch.setitem(sys.modules, "psutil", None)  # no parent processes: only the directory rules
    assert os.path.abspath(mcp_server.fallback_workdir()) == os.path.abspath(course)
    monkeypatch.delenv("COPILOT_PLUGIN_ROOT")
    assert os.path.abspath(mcp_server.fallback_workdir()) == os.path.abspath(plugin)
