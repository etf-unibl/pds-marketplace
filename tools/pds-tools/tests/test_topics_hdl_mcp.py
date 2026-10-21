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


def test_branch_check_parameter_base_does_not_hide_repository(course, monkeypatch):
    # the base parameter (a git ref) once shadowed base() and every call failed with 'str' object is not callable
    from pds_tools import mcp_server
    monkeypatch.chdir(course)
    monkeypatch.delenv("PDS_REPO", raising=False)
    monkeypatch.setattr(mcp_server, "_workdir", None)
    assert isinstance(mcp_server.branch_check(base="origin/assignments"), dict)


def test_relative_paths_resolve_against_the_repository(course, tmp_path, monkeypatch):
    # Antigravity CLI starts the servers outside the repository: assignments/12/x.vhd once failed
    # with "cannot open" while style_report found the same file
    from pds_tools import mcp_server
    folder = os.path.join(course, "assignments", "12")
    os.makedirs(folder)
    with open(os.path.join(folder, "top.vhd"), "w") as f:
        f.write("library ieee;\nuse ieee.std_logic_1164.all;\nentity top is\n  port (SW : in std_logic_vector(1 downto 0); LEDR : out std_logic_vector(1 downto 0));\nend top;\n"
                "architecture rtl of top is\nbegin\n  LEDR <= SW;\nend rtl;\n")
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(mcp_server, "_workdir", str(course))
    assert mcp_server.pin_check("assignments/12/top.vhd")["ok"]
    assert mcp_server.list_testbenches("assignments/12")["ok"]
    if hdl.find_ghdl():
        assert mcp_server.vhdl_analyze(["assignments/12/top.vhd"])["ok"]
        assert mcp_server.vhdl_analyze([os.path.join("assignments", "12")])["ok"]


STYLE_GUIDE = os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "pds-course-template", "docs", "vhdl-code-style.md")


@pytest.mark.skipif(not os.path.isfile(STYLE_GUIDE), reason="course template not next to the plugins")
def test_header_and_pr_template_from_main(tmp_path, monkeypatch):
    # agy retyped the license header from memory (one line rewrapped) and searched the style tool's source;
    # the pull request template is only on main, so it searched the task branch in vain
    import datetime
    from pds_tools import mcp_server
    root = tmp_path / "course"
    (root / "docs").mkdir(parents=True)
    (root / "docs" / "topics").mkdir()
    (root / "docs" / "topics" / "05-x.md").write_text("# x\n", encoding="utf-8")
    with open(STYLE_GUIDE, encoding="utf-8") as f:
        (root / "docs" / "vhdl-code-style.md").write_text(f.read(), encoding="utf-8")
    (root / ".github").mkdir()
    (root / ".github" / "pull_request_template.md").write_text("<!-- section:summary -->\n", encoding="utf-8")
    _git(root, "init", "-q", "-b", "main")
    _git(root, "-c", "user.name=t", "-c", "user.email=t@t", "add", ".")
    _git(root, "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-q", "-m", "docs")
    _git(root, "switch", "-q", "--orphan", "work")
    (root / "dec.vhd").write_text("-- entity old is\nentity decoder_2_4 is\nend entity decoder_2_4;\n", encoding="utf-8")
    monkeypatch.setattr(mcp_server, "_workdir", str(root))
    header = mcp_server.header_template(str(root / "dec.vhd"))
    lines = header.splitlines()
    assert "-- unit name:     decoder_2_4" in lines
    assert f"-- Copyright (c) {datetime.date.today().year} Faculty of Electrical Engineering" in lines
    assert "-- LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE," in lines
    assert lines.count("--   <description of the unit, in your own words>") == 1 and "NAND2" not in header
    assert mcp_server.pr_template(str(root)).strip() == "<!-- section:summary -->"


def test_parse_messages_windows_absolute_path():
    out = r"C:\Users\x\AppData\Local\Temp\pds\inv.vhd:5:10: missing ';' at end of port clause"
    m = hdl.parse_messages(out)
    assert m and m[0]["file"] == "inv.vhd" and m[0]["line"] == 5 and m[0]["severity"] == "error"


@pytest.mark.skipif(not hdl.find_ghdl(), reason="GHDL not installed")
def test_analyze_reports_syntax_error_with_absolute_path(tmp_path):
    bad = tmp_path / "bad.vhd"
    bad.write_text("library ieee;\nuse ieee.std_logic_1164.all;\nentity bad is\n  port (a : in std_logic\nend bad;\n")
    r = hdl.analyze([str(bad)])
    assert not r["ok"] and r["errors"] and r["errors"][0]["file"] == "bad.vhd"


def test_quartus_server_instructions_have_the_constraint_rule():
    from pds_tools import mcp_server
    assert "never confirm a wrong value" in mcp_server.build("quartus").instructions.lower()
    assert "constraint_check" in mcp_server.build("quartus").instructions
    assert "never confirm a wrong value" not in mcp_server.build("git").instructions.lower()


def test_cli_offers_only_read_only_tools(capsys):
    # an assistant without the MCP servers found the CLI and could have written files with it, without the confirmation
    from pds_tools import cli
    assert cli.main(["--list"]) == 0
    listed = capsys.readouterr().out
    assert "env_check(" in listed and "docs_skeleton(" not in listed and "board_program(" not in listed and "quartus_tcl(" not in listed
    assert cli.main(["docs_skeleton", "x.vhd", "write=true"]) == 2
