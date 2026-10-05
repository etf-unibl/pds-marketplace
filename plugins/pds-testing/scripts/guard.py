#!/usr/bin/env python3
"""Guard hook of the PDS student plugins (Claude Code PreToolUse, Copilot CLI preToolUse).

The student plugins teach the course workflow instead of doing it. This hook denies:
  - shell commands that change the repository or GitHub (git commit/push/..., gh pr create/...,
    vhdl-style --fix), and
  - edits of files in assignments/ (graded work),
and tells the assistant to show and explain the command or change instead. Read-only commands
(git status/log/diff, ghdl, vhdl-style without --fix, ...) are allowed.

Reads the hook JSON on stdin, writes the decision JSON on stdout, always exits 0. Standalone (no
dependencies), so it works before pds-tools is installed. The classification must stay equal to
pds_tools.explain.is_state_changing (checked by the pds-tools tests).
"""

import json
import re
import shlex
import sys

READ_ONLY_GIT = {"status", "log", "diff", "show", "fetch", "ls-files", "ls-tree", "rev-parse", "blame", "describe",
                 "shortlog", "reflog", "grep", "help", "version", "cat-file", "rev-list", "for-each-ref", "merge-base",
                 "symbolic-ref", "whatchanged", "count-objects"}
READ_ONLY_GH = ("pr view", "pr list", "pr checks", "pr diff", "pr status", "issue view", "issue list", "run view", "run list",
                "run watch", "repo view", "auth status", "browse")
GIT_GLOBAL_WITH_VALUE = {"-C", "-c", "--git-dir", "--work-tree", "--namespace"}
EDIT_TOOLS = re.compile(r"^(Edit|Write|MultiEdit|NotebookEdit|edit|create|write|str_replace_editor|replace|write_file|apply_patch)$")

MESSAGE_COMMAND = (
    "PDS plugin rule (teach, don't execute): '{cmd}' changes the repository or GitHub, so the assistant does not run it. "
    "Show the student this exact command in a code block, explain what each part does and why it is needed in the course "
    "workflow (the explain_command tool helps), say what output to expect, how to check the result and how to undo it. "
    "Let the student run it, then check the result with read-only tools (repo_state, git status). "
    "Do not try another way to run it (other shell, script, alias)."
)
MESSAGE_EDIT = (
    "PDS plugin rule: files in assignments/ are the student's graded work, so the assistant does not edit them. "
    "Explain the problem and show the change (file, line, corrected code) for the student to apply. "
    "Do not write the solution of a graded assignment; give hints and explanations instead."
)


def is_state_changing(command):
    """True if a single command changes the repository or GitHub."""
    try:
        words = shlex.split(command)
    except ValueError:
        words = command.split()
    while words and re.match(r"^[A-Za-z_][A-Za-z0-9_]*=", words[0]):
        words = words[1:]  # VAR=value prefixes
    if not words:
        return False
    exe = words[0].replace("\\", "/").rsplit("/", 1)[-1].lower()
    exe = exe[:-4] if exe.endswith(".exe") else exe
    if exe == "git":
        rest, i = words[1:], 0
        while i < len(rest) and rest[i].startswith("-"):
            i += 2 if rest[i] in GIT_GLOBAL_WITH_VALUE else 1
        if i >= len(rest):
            return False
        sub, args = rest[i], rest[i + 1:]
        if sub in READ_ONLY_GIT:
            return False
        if sub == "branch" and all(a in ("--show-current", "-a", "-r", "-v", "-vv", "--list", "--all") or a.startswith("--contains") or a.startswith("--merged") for a in args):
            return False
        if sub == "remote" and (not args or args[0] in ("-v", "show", "get-url")):
            return False
        if sub == "config" and any(a in ("--get", "--list", "-l", "--get-all", "--get-regexp") for a in args):
            return False
        if sub == "stash" and args and args[0] in ("list", "show"):
            return False
        return True
    if exe == "gh":
        if len(words) > 1 and words[1] == "api":
            method = next((words[i + 1] for i, w in enumerate(words[:-1]) if w in ("-X", "--method")), "GET")
            writes = any(w in ("-f", "-F", "--field", "--raw-field", "--input") or w.startswith(("-f=", "-F=", "--field=", "--raw-field=", "--input=", "--method=")) for w in words)
            return method.upper() != "GET" or writes
        sub = " ".join(words[1:3])
        return not any(sub.startswith(s) for s in READ_ONLY_GH)
    if exe == "vhdl-style":
        return "--fix" in words
    return False


def segments(command):
    """Simple commands of a command line (split at ;, &&, ||, |, newlines; subshells and quotes opened)."""
    text = re.sub(r"\$\(|`|\(|\)", " ; ", command)
    parts = re.split(r"\s*(?:&&|\|\||;|\||\n)\s*", text)
    out = []
    for part in parts:
        part = part.strip()
        # powershell -Command "...", bash -c '...', cmd /c ...
        m = re.match(r"^(?:\S*(?:pwsh|powershell)(?:\.exe)?\s+(?:-\w+\s+)*-(?:c|command)\s+|\S*(?:bash|sh|zsh)(?:\.exe)?\s+-l?c\s+|cmd(?:\.exe)?\s+/[ck]\s+)(.*)$", part, re.I)
        if m:
            out += segments(m.group(1).strip().strip("\"'"))
        elif part:
            out.append(part)
    return out


def decide(data):
    """(deny, reason) for a hook input of Claude Code or Copilot CLI."""
    tool = data.get("tool_name") or data.get("toolName") or ""
    args = data.get("tool_input", data.get("toolArgs")) or {}
    if isinstance(args, str):
        try:
            args = json.loads(args)
        except ValueError:
            args = {"command": args}
    command = args.get("command") if isinstance(args, dict) else None
    if command and tool.lower() in ("bash", "powershell", "shell", "run_shell_command", "terminal"):
        for seg in segments(command):
            if is_state_changing(seg):
                return True, MESSAGE_COMMAND.format(cmd=seg)
        return False, ""
    if EDIT_TOOLS.match(tool) and isinstance(args, dict):
        paths = [str(args.get(k, "")) for k in ("file_path", "path", "notebook_path", "filePath", "absolute_path")]
        if any(re.search(r"(^|[\\/])assignments[\\/]", p) for p in paths):
            return True, MESSAGE_EDIT
    return False, ""


def main():
    client = sys.argv[1] if len(sys.argv) > 1 else "claude"
    try:
        data = json.load(sys.stdin)
    except ValueError:
        return 0
    deny, reason = decide(data)
    if not deny:
        return 0
    if client == "copilot":
        out = {"permissionDecision": "deny", "permissionDecisionReason": reason}
    else:
        out = {"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "deny", "permissionDecisionReason": reason}}
    sys.stdout.write(json.dumps(out))
    return 0


if __name__ == "__main__":
    sys.exit(main())
