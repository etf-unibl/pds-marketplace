"""Design documentation: outline, review, skeleton (comments only), preview. The expected Doxygen behaviour
was checked with Doxygen 1.9.5 (the version of the course's GitHub Pages workflow)."""

import os
import shutil
import subprocess

import pytest

from pds_tools import docs

FIXTURES = os.path.join(os.path.dirname(__file__), "fixtures", "docs")


def repo_copy(tmp_path, name):
    """The fixture in assignments/12 of a new git repository (the skeleton only writes files of a repository)."""
    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)
    folder = tmp_path / "assignments" / "12"
    folder.mkdir(parents=True)
    shutil.copy(os.path.join(FIXTURES, name), folder / name)
    return str(folder / name)


def rules(result):
    return [(f["line"], f["rule"]) for f in result["files"][0]["findings"]]


def test_outline_keys():
    out = docs.outline(os.path.join(FIXTURES, "counter_mod.vhd"))
    keys = [e["key"] for e in out["elements"]]
    assert keys == ["entity:counter_mod", "generic:g_WIDTH", "generic:g_MOD", "port:clk_i", "port:rst_i", "port:en_i",
                    "port:count_o", "port:tc_o", "architecture:arch", "constant:c_LAST", "type:t_state", "signal:count_reg",
                    "signal:count_next", "signal:state", "function:is_last", "process:count_reg_proc", "process:line79",
                    "instance:sync_inst"]
    assert out["file_doc"] is None and not any(e["documented"] for e in out["elements"])


def test_check_finds_the_pitfalls():
    found = rules(docs.check(os.path.join(FIXTURES, "pitfalls.vhd")))
    assert (7, "multi_line_without_brief") in found       # no @brief: all of it becomes the details
    assert (12, "merged_comment") in found                # trailing --! joined with the --! line below
    assert (15, "brief_missing") in found                 # plain -- comment
    assert (19, "split_block") in found                   # blank line inside the comment
    assert (25, "shared_declaration") in found            # signal s1, s2
    assert (26, "merged_comment") in found
    assert (28, "long_brief") in found
    assert (32, "process_without_label") in found
    assert (50, "orphan_doc") in found                    # before 'end architecture'
    assert not any(rule == "file_doc_missing" for _, rule in found)
    q_o = next(f for f in docs.check(os.path.join(FIXTURES, "pitfalls.vhd"))["files"][0]["findings"] if f["line"] == 15)
    assert "plain `--` comment" in q_o["message"]


def test_check_folder_leaves_out_testbenches(tmp_path):
    (tmp_path / "x_tb.vhd").write_text("entity x_tb is\nend entity x_tb;\n")
    shutil.copy(os.path.join(FIXTURES, "counter_mod.vhd"), tmp_path)
    result = docs.check(str(tmp_path))
    assert [os.path.basename(f["path"]) for f in result["files"]] == ["counter_mod.vhd"]
    assert result["testbenches"]["files"] == ["x_tb.vhd"]


def test_skeleton_adds_comments_only(tmp_path):
    path = repo_copy(tmp_path, "counter_mod.vhd")
    original = open(path, encoding="utf-8").read()
    briefs = {"entity:counter_mod": "Modulo counter with a terminal count output", "port:clk_i": "Clock, rising edge",
              "signal:count_reg": "Current value of the counter", "port:nope": "x", "port:rst_i": "two\nlines"}
    preview = docs.skeleton(path, briefs)
    assert not preview["written"] and open(path, encoding="utf-8").read() == original
    assert set(preview["rejected_briefs"]) == {"port:nope", "port:rst_i"}
    result = docs.skeleton(path, briefs, write=True)
    text = open(path, encoding="utf-8").read()
    assert result["written"] and docs._strip_docs(text.splitlines()) == docs._strip_docs(original.splitlines())
    lines = text.splitlines()
    # entity: brief, details placeholder, blank line (course style: blank line above 'entity')
    e = lines.index("entity counter_mod is")
    assert lines[e - 1] == "" and lines[e - 2].startswith("--! (latency") and "@brief Modulo counter" in lines[e - 5]
    # ports: aligned trailing comments, TODO for the briefs not given; en_i keeps its plain comment
    clk = next(l for l in lines if l.startswith("    clk_i"))
    count = next(l for l in lines if l.startswith("    count_o"))
    assert clk.index("--!") == count.index("--!") and clk.endswith("--! Clock, rising edge")
    assert "--! TODO: one sentence on port rst_i" in next(l for l in lines if l.startswith("    rst_i"))
    assert next(l for l in lines if l.startswith("    en_i")).endswith("-- count enable")
    assert any(s["key"] == "port:en_i" and "--!" in s["reason"] for s in result["skipped"])
    assert all(len(l) <= docs.MAX_LINE for l in lines)
    assert result["realign"].startswith("Lines ")
    # running it again adds nothing; every element is documented except the skipped ones
    assert docs.skeleton(path, {}, write=True)["added"] == []
    left = {f["key"] for f in docs.check(path)["files"][0]["findings"] if f["rule"] == "brief_missing"}
    assert left == {"port:en_i"}


def test_skeleton_refuses_testbench_and_files_outside_a_repository(tmp_path):
    with pytest.raises(ValueError):
        docs.skeleton(str(tmp_path / "x_tb.vhd"))
    path = tmp_path / "plain" / "counter_mod.vhd"
    path.parent.mkdir()
    shutil.copy(os.path.join(FIXTURES, "counter_mod.vhd"), path)
    if subprocess.run(["git", "rev-parse"], cwd=path.parent, capture_output=True).returncode == 0:
        pytest.skip("the temporary folder is inside a git repository")
    with pytest.raises(ValueError):
        docs.skeleton(str(path))


def test_skeleton_does_not_join_comments(tmp_path):
    path = repo_copy(tmp_path, "pitfalls.vhd")

    def merged():
        return sorted(f["key"] for f in docs.check(path)["files"][0]["findings"] if f["rule"] == "merged_comment")

    before = merged()
    result = docs.skeleton(path, {}, write=True)
    skipped = {s["key"] for s in result["skipped"]}
    assert {"port:rst_i", "signal:s3", "port:q_o"} <= skipped  # comment joined with the one below, plain comment
    assert merged() == before == ["port:rst_i", "signal:s3"]  # the student's two, no new one


def test_preview_without_doxygen(tmp_path, monkeypatch):
    path = repo_copy(tmp_path, "counter_mod.vhd")
    (tmp_path / "assignments" / "Doxyfile").write_text("FILE_PATTERNS = *.vhd\n")
    monkeypatch.setattr(docs, "find_doxygen", lambda: None)
    result = docs.preview(os.path.dirname(path))
    assert result["ok"] is False and "doxygen.nl" in result["message"]


@pytest.mark.skipif(not docs.find_doxygen(), reason="Doxygen is not installed (PDS_DOXYGEN)")
def test_preview_builds_outside_the_repository(tmp_path):
    path = repo_copy(tmp_path, "counter_mod.vhd")
    (tmp_path / "assignments" / "Doxyfile").write_text(
        "OPTIMIZE_OUTPUT_VHDL = YES\nEXTRACT_ALL = YES\nFILE_PATTERNS = *.vhd\nRECURSIVE = YES\nGENERATE_LATEX = NO\n")
    docs.skeleton(path, {"entity:counter_mod": "Modulo counter"}, write=True)
    result = docs.preview(os.path.dirname(path))
    assert result["ok"], result
    assert not result["index"].startswith(str(tmp_path) + os.sep) and "-docs" in result["index"]
    assert [p["design_unit"] for p in result["pages"]] == ["counter_mod"]
