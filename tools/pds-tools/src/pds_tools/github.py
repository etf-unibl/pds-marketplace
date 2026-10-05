"""Read-only access to the course repository on GitHub (issues, pull requests, check results).

Only GET requests are made. The token is taken from GITHUB_TOKEN / GH_TOKEN or from the GitHub
CLI login (gh auth token); without a token public repositories still work, with a lower rate
limit.
"""

import json
import os
import re
import shutil
import subprocess
import urllib.error
import urllib.parse
import urllib.request

from . import repo, rules

API = "https://api.github.com"
_token = None


def token():
    global _token
    if _token is None:
        _token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN") or ""
        if not _token and shutil.which("gh"):
            r = subprocess.run(["gh", "auth", "token"], capture_output=True, text=True)
            _token = r.stdout.strip() if r.returncode == 0 else ""
    return _token


def get(path, params=None):
    url = API + path + ("?" + urllib.parse.urlencode(params) if params else "")
    headers = {"Accept": "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28", "User-Agent": "pds-tools"}
    if token():
        headers["Authorization"] = "Bearer " + token()
    req = urllib.request.Request(url, headers=headers, method="GET")
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            return json.load(r)
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"GitHub API {e.code} for {path}: {e.read().decode(errors='replace')[:200]}")


def _slug(path, repository):
    if repository:
        return repository
    root = repo.find_root(path)
    slug = repo.remote_slug(root) if root else None
    if not slug:
        raise RuntimeError("Cannot determine the GitHub repository (no origin remote on github.com). Pass repository='owner/name'.")
    return slug


def task_context(issue=None, path=".", repository=None):
    """Everything a student needs for an issue: title, kind, deadline, folder, branch and commit format."""
    slug = _slug(path, repository)
    if issue is None:
        state = repo.repo_state(path)
        issue = state.get("issue")
        if not issue:
            return {"ok": False, "message": "Give the issue number (the current branch name does not start with one)."}
    data = get(f"/repos/{slug}/issues/{issue}")
    labels = [l["name"] for l in data.get("labels", [])]
    group = next((l for l in labels if re.fullmatch(r"assignment-\d+", l)), None)
    kind = "test" if "good first issue" in labels else "graded" if group else "other"
    milestone = data.get("milestone") or {}
    title = data["title"]
    return {"ok": True, "repository": slug, "issue": int(issue), "title": title, "state": data["state"], "kind": kind,
            "group": group, "labels": labels, "assignees": [a["login"] for a in data.get("assignees", [])],
            "milestone": milestone.get("title"), "due_on": milestone.get("due_on"), "url": data["html_url"], "body": data.get("body") or "",
            "folder": f"assignments/{issue}/", "branch_prefix": f"{issue}-",
            "commit_subject": rules.expected_title(issue, title), "pr_title": rules.expected_title(issue, title),
            "required_files": ["test.vhd"] if kind == "test" else None}


TRUSTED_ASSOCIATIONS = ("OWNER", "MEMBER", "COLLABORATOR")


def time_summary(issue=None, path=".", repository=None):
    """/spent entries of an issue as the time tracking workflow counts them (per author, invalid lines)."""
    slug = _slug(path, repository)
    if issue is None:
        issue = repo.repo_state(path).get("issue")
        if not issue:
            return {"ok": False, "message": "Give the issue number (the current branch name does not start with one)."}
    data = get(f"/repos/{slug}/issues/{issue}")
    assignees = [a["login"] for a in data.get("assignees", [])]
    per_author, entries, invalid, ignored = {}, [], [], 0
    page = 1
    while True:
        comments = get(f"/repos/{slug}/issues/{issue}/comments", {"per_page": 100, "page": page})
        for c in comments:
            valid, bad = rules.spent_entries(c.get("body"))
            if not (valid or bad):
                continue
            if c["user"]["type"] == "Bot" or not (c["user"]["login"] in assignees or c.get("author_association") in TRUSTED_ASSOCIATIONS):
                ignored += 1
                continue
            for e in valid:
                e.update(author=c["user"]["login"], date=c["created_at"][:10], url=c["html_url"])
                entries.append(e)
                per_author[e["author"]] = round(per_author.get(e["author"], 0) + e["hours"], 2)
            invalid += [{"line": l, "url": c["html_url"]} for l in bad]
        if len(comments) < 100:
            break
        page += 1
    return {"ok": not invalid, "issue": int(issue), "title": data["title"], "logged_hours": round(sum(e["hours"] for e in entries), 2),
            "per_author": per_author, "entries": entries, "invalid_lines": invalid, "ignored_comments": ignored,
            "note": "This is the 'Time logged (h)' part only; 'Time spent (h)' entered on the project board is added by the weekly report."}


def pr_status(pr=None, path=".", repository=None):
    """Pull request of the current branch (or number pr): rule checks and CI results with error annotations."""
    slug = _slug(path, repository)
    if pr is None:
        state = repo.repo_state(path)
        branch = state.get("branch")
        if not branch:
            return {"ok": False, "message": "Not on a branch; give the pull request number."}
        owner = slug.split("/")[0]
        found = get(f"/repos/{slug}/pulls", {"head": f"{owner}:{branch}", "state": "all"})
        if not found:
            # forks or other owners: search by branch name
            found = [p for p in get(f"/repos/{slug}/pulls", {"state": "all", "per_page": 100}) if p["head"]["ref"] == branch]
        if not found:
            return {"ok": False, "message": f"No pull request for branch {branch} yet.", "branch": branch}
        pr = found[0]["number"]
    data = get(f"/repos/{slug}/pulls/{pr}")
    m = re.match(r"^Issue #(\d+)", data["title"] or "")
    issue = m.group(1) if m else rules.issue_from_branch(data["head"]["ref"])
    findings = []
    if issue:
        issue_data = get(f"/repos/{slug}/issues/{issue}")
        findings += rules.check_pr_title(data["title"], issue, issue_data["title"])
        findings += rules.check_branch(data["head"]["ref"], issue)
        findings += rules.check_assignee(data["user"]["login"], [a["login"] for a in issue_data.get("assignees", [])], issue)
        files = get(f"/repos/{slug}/pulls/{pr}/files", {"per_page": 100})
        findings += rules.check_paths([p for f in files for p in (f["filename"], f.get("previous_filename"))], issue)
        for c in get(f"/repos/{slug}/pulls/{pr}/commits", {"per_page": 100}):
            if len(c["parents"]) > 1:
                continue
            a = c["commit"]["author"]
            for f in rules.check_commit_message(c["commit"]["message"], issue, issue_data["title"], a["name"], a["email"]):
                if not f.ok:
                    f.message = f"{c['sha'][:7]}: {f.message}"
                    findings.append(f)
    findings += rules.check_pr_body(data.get("body"))
    checks = []
    runs = get(f"/repos/{slug}/commits/{data['head']['sha']}/check-runs", {"per_page": 100}).get("check_runs", [])
    # Re-runs and new events (edited title, new push of the same commit) add runs; keep the latest per check name
    latest = {}
    for run in runs:
        if run["name"] not in latest or (run.get("started_at") or "") > (latest[run["name"]].get("started_at") or ""):
            latest[run["name"]] = run
    for run in latest.values():
        entry = {"name": run["name"], "status": run["status"], "conclusion": run["conclusion"], "url": run["html_url"]}
        if run["conclusion"] == "failure":
            try:
                entry["annotations"] = [{"message": a["message"], "path": a.get("path"), "line": a.get("start_line")}
                                        for a in get(f"/repos/{slug}/check-runs/{run['id']}/annotations", {"per_page": 50})]
            except RuntimeError:
                pass
        checks.append(entry)
    return {"ok": not rules.errors(findings) and all(c["conclusion"] in ("success", "skipped", "neutral", None) for c in checks),
            "pull_request": int(pr), "title": data["title"], "state": data["state"], "url": data["html_url"], "issue": issue,
            "rule_checks": [f.as_dict() for f in findings], "ci_checks": checks,
            "note": "rule_checks repeat the pr-checks job locally; ci_checks are the results of the last run on GitHub."}
