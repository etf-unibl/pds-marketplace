from pds_tools import rules

TITLE = "Even detector"
GOOD = "Issue #12 : Even detector\n\n- add design\n- add testbench\n\nSigned-off-by: Ana Anić <1+ana@users.noreply.github.com>\n"


def msgs(findings):
    return [f.message for f in rules.errors(findings)]


def test_good_commit_passes_ci_and_hook_rules():
    assert not rules.errors(rules.check_commit_message(GOOD, 12, TITLE, "Ana Anić", "1+ana@users.noreply.github.com", "12-even"))


def test_commit_title_whitespace_is_normalized_like_ci():
    msg = GOOD.replace("Issue #12 : Even detector", "Issue #12 : Even   detector")
    assert not rules.errors(rules.check_commit_message(msg, 12, TITLE))


def test_commit_wrong_issue_title():
    assert msgs(rules.check_commit_message(GOOD, 12, "Odd detector")) == ["The first line must be 'Issue #12 : Odd detector'."]


def test_commit_format_problems_are_all_reported():
    found = msgs(rules.check_commit_message("Issue 12: x\ntext\n", None, None, "A", "a@b"))
    assert len(found) == 4  # subject, blank line, items, sign-off


def test_commit_branch_mismatch_hook_rule():
    found = msgs(rules.check_commit_message(GOOD.replace("#12", "#13"), branch="12-even"))
    assert found == ["Issue #13 in the first line does not match the branch '12-even' (issue #12)."]


def test_signoff_case_insensitive_like_ci():
    msg = GOOD.replace("Signed-off-by", "signed-off-by")
    assert not rules.errors(rules.check_commit_message(msg, author_name="Ana Anić", author_email="1+ana@users.noreply.github.com"))


def test_trailers_are_not_change_items():
    msg = "Issue #12 : Even detector\n\nSigned-off-by: A <a@b>\n"
    assert "Describe the changes" in msgs(rules.check_commit_message(msg))[0]


def test_merge_commit_not_checked():
    assert not rules.errors(rules.check_commit_message("Merge branch 'assignments' into 12-even"))


def test_hook_comment_lines_ignored():
    msg = "Issue #12 : Even detector\n\n- x\n# Please enter the commit message\n"
    assert not rules.errors(rules.check_commit_message(msg))


def test_title_branch_assignee_paths():
    assert not rules.errors(rules.check_pr_title("Issue #12 :  Even detector", 12, TITLE))
    assert rules.errors(rules.check_pr_title("Issue #12: Even detector", 12, TITLE))
    assert not rules.errors(rules.check_branch("12-even", 12))
    assert rules.errors(rules.check_branch("even-12", 12))
    assert rules.errors(rules.check_assignee("bob", ["ana"], 12))
    found = rules.check_paths(["assignments/12/a.vhd", "README.md", None], 12)
    assert found[0].details["outside"] == ["README.md"]


PR_BODY = """## Opis
<!-- section:summary -->
Detektor parnosti.
<!-- /section:summary -->
## Izmjene
<!-- section:changes -->
<!-- /section:changes -->
- [x] Stil provjeren <!-- check:style -->
- [ ] Testbench prolazi <!-- check:testbench -->
"""


def test_pr_body_unticked_and_empty_summary():
    f = rules.check_pr_body(PR_BODY)
    assert f[0].details["unticked"] == ["testbench"]
    empty = PR_BODY.replace("Detektor parnosti.", "<!-- opis -->").replace("[ ]", "[x]")
    assert "is empty" in rules.check_pr_body(empty)[0].message
    assert rules.check_pr_body(PR_BODY.replace("[ ]", "[x]"))[0].ok


def test_issue_from_branch():
    assert rules.issue_from_branch("12-even") == "12"
    assert rules.issue_from_branch("assignments") is None


def test_spent_entries_like_time_tracking():
    valid, invalid = rules.spent_entries("/spent 1h30m FSM\n/SPENT 45min tb\n/spent 1,5h docs\n/spent 2\n/spent 25h too much\ntext")
    assert [v["hours"] for v in valid] == [1.5, 0.75, 1.5]
    assert valid[0]["note"] == "FSM"
    assert invalid == ["/spent 2", "/spent 25h too much"]
