"""Read-only view of the course repository (git state of the student's working copy).

All git calls go through git(), which accepts only read-only subcommands. Anything that changes
the repository (add, commit, push, checkout, switch, reset, merge, rebase, config writes, ...)
is refused, so the tools can only describe the state and explain what to run.
"""

import os
import re
import subprocess

from . import rules

# Read-only git subcommands; options are checked separately for the few that could write
READ_ONLY = {"status", "rev-parse", "log", "diff", "show", "ls-files", "ls-tree", "branch", "remote",
             "config", "symbolic-ref", "rev-list", "for-each-ref", "merge-base", "cat-file", "describe"}
WRITE_OPTIONS = {
    "branch": {"-d", "-D", "-m", "-M", "-c", "-C", "--delete", "--move", "--copy", "--set-upstream-to", "-u", "--unset-upstream", "--edit-description", "-f", "--force"},
    "remote": {"add", "remove", "rm", "rename", "set-url", "set-head", "prune", "update", "set-branches"},
    "config": {"--add", "--unset", "--unset-all", "--replace-all", "--rename-section", "--remove-section", "--edit", "-e", "set", "unset"},
}


class GitError(RuntimeError):
    pass


def git(args, cwd=None, check=True):
    """Runs a read-only git command and returns its standard output (stripped)."""
    if not args or args[0] not in READ_ONLY:
        raise GitError(f"git {args[0] if args else ''} is not a read-only command; pds-tools never runs it")
    if set(args[1:]) & WRITE_OPTIONS.get(args[0], set()):
        raise GitError(f"git {' '.join(args)} could change the repository; pds-tools never runs it")
    if args[0] == "config" and not any(a in ("--get", "--get-all", "--list", "-l", "--get-regexp", "get") for a in args[1:]):
        raise GitError("only 'git config --get ...' is allowed")
    if args[0] == "branch" and len([a for a in args[1:] if not a.startswith("-")]) > 0 and "--list" not in args and "--contains" not in args and "--merged" not in args and "--no-merged" not in args:
        raise GitError("git branch <name> creates a branch; pds-tools never runs it")
    result = subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if check and result.returncode != 0:
        raise GitError(result.stderr.strip() or f"git {' '.join(args)} failed")
    return result.stdout.strip()


def find_root(path="."):
    """Root of the git working copy that contains path, or None."""
    try:
        return git(["rev-parse", "--show-toplevel"], cwd=path)
    except (GitError, FileNotFoundError, NotADirectoryError):
        return None


def remote_slug(root):
    """owner/repo of the origin remote on GitHub, or None."""
    url = git(["remote", "get-url", "origin"], cwd=root, check=False)
    m = re.match(r"^(?:git@github\.com:|https://github\.com/)([^/]+/[^/]+?)(?:\.git)?/?$", url or "")
    return m.group(1) if m else None


def repo_state(path="."):
    """Summary of the working copy: branch, issue, staged/unstaged files, upstream, hooks, identity."""
    root = find_root(path)
    if not root:
        return {"ok": False, "message": "Not inside a git repository. Run the tools from your course repository folder."}
    branch = git(["branch", "--show-current"], cwd=root, check=False)
    issue = rules.issue_from_branch(branch)
    porcelain = git(["status", "--porcelain=v1", "--branch"], cwd=root)
    lines = porcelain.splitlines()
    head = lines[0] if lines else ""
    staged, unstaged, untracked = [], [], []
    for line in lines[1:]:
        code, path_ = line[:2], line[3:]
        if code == "??":
            untracked.append(path_)
            continue
        if code[0] not in (" ", "?"):
            staged.append(path_)
        if code[1] not in (" ", "?"):
            unstaged.append(path_)
    upstream = re.search(r"\.\.\.(\S+)", head)
    ahead = re.search(r"ahead (\d+)", head)
    behind = re.search(r"behind (\d+)", head)
    git_dir = git(["rev-parse", "--git-dir"], cwd=root)
    if not os.path.isabs(git_dir):
        git_dir = os.path.join(root, git_dir)
    state = {
        "ok": True,
        "root": root,
        "repository": remote_slug(root),
        "branch": branch or None,
        "detached": not branch,
        "issue": issue,
        "upstream": upstream.group(1) if upstream else None,
        "ahead": int(ahead.group(1)) if ahead else 0,
        "behind": int(behind.group(1)) if behind else 0,
        "staged": staged,
        "unstaged": unstaged,
        "untracked": untracked,
        "merge_in_progress": os.path.exists(os.path.join(git_dir, "MERGE_HEAD")),
        "rebase_in_progress": any(os.path.isdir(os.path.join(git_dir, d)) for d in ("rebase-merge", "rebase-apply")),
        "hooks_path": git(["config", "--get", "core.hooksPath"], cwd=root, check=False) or None,
        "user_name": git(["config", "--get", "user.name"], cwd=root, check=False) or None,
        "user_email": git(["config", "--get", "user.email"], cwd=root, check=False) or None,
    }
    if issue:
        state["outside_folder"] = sorted(p for p in staged if not p.startswith(f"assignments/{issue}/"))
    return state


def commits_on_branch(root, base="origin/assignments", limit=50):
    """Commits on the current branch that are not on base (newest first)."""
    sep = "\x1e"
    out = git(["log", f"--max-count={limit}", f"--format=%H%x1f%an%x1f%ae%x1f%P%x1f%B{sep}", f"{base}..HEAD"], cwd=root, check=False)
    commits = []
    for chunk in out.split(sep):
        chunk = chunk.strip("\n")
        if not chunk:
            continue
        sha, name, email, parents, body = (chunk.split("\x1f") + [""] * 5)[:5]
        commits.append({"sha": sha, "author_name": name, "author_email": email, "merge": len(parents.split()) > 1, "message": body.strip("\n")})
    return commits


def check_branch_commits(path=".", base="origin/assignments", issue_title=None):
    """Checks the commits of the current branch like the CI check (format, sign-off, issue number)."""
    state = repo_state(path)
    if not state["ok"]:
        return state
    results = []
    for c in commits_on_branch(state["root"], base):
        if c["merge"]:
            continue
        findings = rules.check_commit_message(c["message"], state["issue"] if issue_title else None, issue_title,
                                              c["author_name"], c["author_email"], state["branch"])
        results.append({"sha": c["sha"][:7], "subject": c["message"].split("\n")[0], "findings": [f.as_dict() for f in findings]})
    return {"ok": all(f["ok"] for r in results for f in r["findings"]), "branch": state["branch"], "base": base, "commits": results}


def show_file(root, ref, path):
    """Content of path at ref (e.g. origin/main:docs/...), or None if it does not exist."""
    try:
        return git(["show", f"{ref}:{path}"], cwd=root)
    except GitError:
        return None
