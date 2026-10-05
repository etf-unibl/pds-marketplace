"""Submission rules of the course, the same as the CI check and the git hooks.

Source of truth (keep in sync):
  - .github/scripts/pr_rules.py on the main branch of the course template (pr-checks job),
  - .githooks/commit-msg and .githooks/pre-commit on the assignments branch.

Every check returns a list of Finding objects; an empty list of errors means the rule holds.
The functions only look at the texts they get, they never contact GitHub or run git.
"""

import re
from dataclasses import dataclass, field

SUBJECT = re.compile(r"^Issue #(\d+) : (.+)$")
ITEM = re.compile(r"^\s*-\s+\S")
TRAILER = re.compile(r"^[A-Za-z-]+: ")
BRANCH_ISSUE = re.compile(r"^(\d+)-")
MERGE_SUBJECT = re.compile(r"^(Merge |fixup! |squash! |amend! )")


@dataclass
class Finding:
    rule: str
    ok: bool
    message: str
    details: dict = field(default_factory=dict)

    def as_dict(self):
        return {"rule": self.rule, "ok": self.ok, "message": self.message, **({"details": self.details} if self.details else {})}


def norm(text):
    """Collapses whitespace, as the CI check does before comparing titles."""
    return " ".join((text or "").split())


def expected_title(issue, issue_title):
    return f"Issue #{issue} : {issue_title}"


def issue_from_branch(branch):
    """Issue number at the start of a branch name ("12-nand2" -> "12"), or None."""
    m = BRANCH_ISSUE.match(branch or "")
    return m.group(1) if m else None


def check_pr_title(title, issue, issue_title):
    want = expected_title(issue, issue_title)
    if norm(title) == norm(want):
        return [Finding("title", True, "title")]
    return [Finding("title", False, f"The pull request title must be '{want}'.", {"expected": want, "actual": title})]


def check_branch(branch, issue):
    if (branch or "").startswith(f"{issue}-"):
        return [Finding("branch", True, f"branch {branch}")]
    return [Finding("branch", False, f"The branch name '{branch}' must start with '{issue}-' (create the branch from issue #{issue}).")]


def check_assignee(author, assignees, issue):
    if author in assignees:
        return [Finding("assignee", True, f"{author} is assigned to issue #{issue}")]
    return [Finding("assignee", False, f"Issue #{issue} is not assigned to {author}. Check the issue number in the title.")]


def check_paths(paths, issue):
    """Changed paths (new and previous names of renamed files) must be in assignments/<N>/."""
    outside = sorted({p for p in paths if p and not p.startswith(f"assignments/{issue}/")})
    if outside:
        return [Finding("paths", False, f"Only files in assignments/{issue}/ may be changed. Changed outside: {', '.join(outside)}", {"outside": outside})]
    return [Finding("paths", True, f"all changes are in assignments/{issue}/")]


def commit_items(message):
    """The '- ' change items of a commit message (lines after the second one, trailers excluded)."""
    lines = message.replace("\r\n", "\n").split("\n")
    return [l.strip() for l in lines[2:] if ITEM.match(l) and not TRAILER.match(l)]


def check_commit_message(message, issue=None, issue_title=None, author_name=None, author_email=None, branch=None):
    """Checks one commit message.

    With issue and issue_title the first line must match exactly (CI rule); without them only the
    format is checked and, if a branch is given, the issue number must match the branch (hook rule).
    The sign-off is checked when the author name and e-mail are given.
    """
    message = message.replace("\r\n", "\n")
    lines = [l for l in message.split("\n") if not l.startswith("#")]
    findings = []
    subject = lines[0] if lines else ""
    if MERGE_SUBJECT.match(subject):
        return [Finding("commit_format", True, "merge, fixup or squash commit: not checked")]
    m = SUBJECT.match(subject)
    if not m:
        findings.append(Finding("commit_subject", False, "The first line must be 'Issue #<N> : <issue title>' (with spaces around ':')."))
    else:
        if issue is not None and issue_title is not None:
            if m.group(1) != str(issue) or norm(m.group(2)) != norm(issue_title):
                findings.append(Finding("commit_subject", False, f"The first line must be '{expected_title(issue, issue_title)}'."))
        branch_issue = issue_from_branch(branch)
        if branch_issue and m.group(1) != branch_issue:
            findings.append(Finding("commit_subject", False, f"Issue #{m.group(1)} in the first line does not match the branch '{branch}' (issue #{branch_issue})."))
    if len(lines) > 1 and lines[1].strip():
        findings.append(Finding("commit_blank_line", False, "The second line must be empty."))
    if not commit_items("\n".join(lines)):
        findings.append(Finding("commit_items", False, "Describe the changes as a list: lines starting with '- ' after the empty line."))
    if author_name is not None and author_email is not None:
        want = f"signed-off-by: {author_name} <{author_email}>"
        if want.lower() not in message.lower():
            findings.append(Finding("sign_off", False, f"Missing sign-off 'Signed-off-by: {author_name} <{author_email}>' (commit with: git commit -s)."))
    if not findings:
        findings.append(Finding("commit_format", True, "commit message follows the format"))
    return findings


SECTION = re.compile(r"<!--\s*section:(\w+)\s*-->(.*?)<!--\s*/section:\1\s*-->", re.S)
CHECK = re.compile(r"^\s*[-*]\s*\[( |x|X)\].*?<!--\s*check:(\w+)\s*-->", re.M)


def check_pr_body(body):
    """Checks the pull request description against the template (summary filled, all checks ticked).

    The changes section is filled by CI from the commit messages, so it is not checked here.
    """
    body = (body or "").replace("\r\n", "\n")
    sections = dict(SECTION.findall(body))
    checks = CHECK.findall(body)
    problems = []
    if "summary" not in sections:
        problems.append("section 'summary' (description of the solution) is missing")
    elif not re.sub(r"<!--.*?-->", "", sections["summary"], flags=re.S).strip():
        problems.append("section 'summary' (description of the solution) is empty")
    if not checks:
        problems.append("the check list is missing")
    unticked = [name for state, name in checks if state == " "]
    if unticked:
        problems.append("not ticked: " + ", ".join(unticked))
    if problems:
        return [Finding("description", False, "The description must follow the pull request template (" + "; ".join(problems) + ").", {"unticked": unticked})]
    return [Finding("description", True, "description follows the template")]


def errors(findings):
    return [f for f in findings if not f.ok]


# /spent entries of the time tracking (same as .github/scripts/time_tracking.py on main)
SPENT_LINE = re.compile(r"^\s*/spent\b(.*)$", re.IGNORECASE)
DURATION = re.compile(
    r"^\s*(?:(?P<h>\d+(?:[.,]\d+)?)\s*h(?:ours?|rs?)?)?\s*(?:(?P<m>\d+)\s*m(?:in(?:utes?)?)?)?(?=\s|$)(?P<rest>.*)$",
    re.IGNORECASE)
MAX_ENTRY_HOURS = 24


def parse_hours(text):
    """(hours, note) for the text after /spent, or None if the duration is invalid."""
    m = DURATION.match(text)
    if not m or (m["h"] is None and m["m"] is None):
        return None
    hours = float((m["h"] or "0").replace(",", ".")) + int(m["m"] or 0) / 60
    if not 0 < hours <= MAX_ENTRY_HOURS:
        return None
    return round(hours, 2), m["rest"].strip()


def spent_entries(text):
    """Valid and invalid /spent lines of a comment text."""
    valid, invalid = [], []
    for line in (text or "").splitlines():
        m = SPENT_LINE.match(line)
        if not m:
            continue
        parsed = parse_hours(m.group(1))
        if parsed is None:
            invalid.append(line.strip())
        else:
            valid.append({"hours": parsed[0], "note": parsed[1], "line": line.strip()})
    return valid, invalid
