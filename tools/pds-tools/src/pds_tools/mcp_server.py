"""MCP server of the PDS plugins: one server, one profile per plugin.

    pds-mcp --profile git        # tools of the pds-git plugin
    pds-mcp --profile learning   # tools of the pds-learning plugin
    pds-mcp --list               # profiles and their tools

All tools are read-only (MCP read-only hint). The server runs over stdio in the folder the AI
tool starts it in, normally the student's course repository.
"""

import argparse
import os
import sys

from mcp.server.mcpserver import MCPServer
from mcp.types import ToolAnnotations

from . import __version__, env, explain, github, hdl, pins, quartus, repo, rules, topics

READ_ONLY = ToolAnnotations(readOnlyHint=True, destructiveHint=False, idempotentHint=True, openWorldHint=False)
READ_ONLY_REMOTE = ToolAnnotations(readOnlyHint=True, destructiveHint=False, idempotentHint=True, openWorldHint=True)


def _read(path):
    with open(path, encoding="utf-8", errors="replace") as f:
        return f.read()


# ---- tool functions (thin wrappers with docstrings that the AI tool sees) ----

def env_check() -> dict:
    """Checks the student's environment: git, GHDL, vhdl-style, gh, Quartus and ModelSim/Questa on PATH, git identity (noreply e-mail) and course hooks."""
    return env.env_check(os.getcwd())


def task_context(issue: int | None = None) -> dict:
    """Context of a course issue (default: the issue of the current branch): title, kind (test/graded), group, deadline, folder, expected branch prefix, commit subject and PR title."""
    return github.task_context(issue, os.getcwd())


def pr_status(pr: int | None = None) -> dict:
    """Pull request of the current branch (or number pr): the course rule checks (title, branch, assignee, files, commits, description) and the CI results with error annotations."""
    return github.pr_status(pr, os.getcwd())


def course_doc(name: str | None = None) -> dict:
    """A course guide from docs/ (e.g. assignment-submission, simulation-and-testing, vhdl-code-style); without a name, the list of guides."""
    return topics.course_doc(name, os.getcwd())


def repo_state() -> dict:
    """State of the working copy: branch, issue, staged/unstaged/untracked files, files outside assignments/<N>/, upstream ahead/behind, merge/rebase in progress, hooks and identity."""
    return repo.repo_state(os.getcwd())


def commit_check(message: str, issue: int | None = None, issue_title: str | None = None) -> dict:
    """Checks a commit message draft against the course format (and the exact issue title if given). The sign-off is checked against the git identity of the repository."""
    root = repo.find_root(os.getcwd())
    name = repo.git(["config", "--get", "user.name"], cwd=root, check=False) if root else None
    email = repo.git(["config", "--get", "user.email"], cwd=root, check=False) if root else None
    branch = repo.git(["branch", "--show-current"], cwd=root, check=False) if root else None
    findings = rules.check_commit_message(message, issue, issue_title, name or None, email or None, branch)
    return {"ok": not rules.errors(findings), "findings": [f.as_dict() for f in findings]}


def branch_check(issue_title: str | None = None, base: str = "origin/assignments") -> dict:
    """Checks the commits of the current branch that are not on base, like the CI pr-checks job (format, sign-off, issue number)."""
    return repo.check_branch_commits(os.getcwd(), base, issue_title)


def explain_command(command: str, lang: str = "en") -> dict:
    """Explains a git/gh/course command: what it does, why it is used in the course, how to check the result and how to undo it. lang: 'sr' or 'en'."""
    return explain.explain_command(command, lang)


def vhdl_analyze(paths: list[str]) -> dict:
    """Analyses VHDL files or folders with GHDL (VHDL-2008, the course standard) into a temporary library; returns errors and warnings with file and line."""
    return hdl.analyze(paths)


def list_testbenches(folder: str) -> dict:
    """Testbenches (*_tb.vhd) of an assignment folder and whether each entity is named like its file (CI requirement)."""
    return hdl.list_testbenches(folder)


def run_testbenches(folder: str, testbenches: list[str] | None = None, stop_time: str = "10ms") -> dict:
    """Runs the testbenches of an assignment folder exactly like the course CI (in a temporary copy, nothing is written to the folder); pass/fail, assertion messages and files the testbench writes."""
    return hdl.run_testbenches(folder, testbenches, stop_time)


def style_report(target: str) -> dict:
    """Runs the course style check (vhdl-style, never with --fix) on an issue number, folder or file and returns the violations."""
    return hdl.style_report(target, os.getcwd())


def synth_summary(project_dir: str = ".", revision: str | None = None) -> dict:
    """Reads the Quartus reports of a compiled project: flow summary (ALMs, registers, pins, memory, DSP), warnings that point to design errors (latches, sensitivity lists, ...) and timing (Fmax, slack, unconstrained paths)."""
    return quartus.synth_summary(project_dir, revision)


def board_pins(filter_text: str | None = None) -> dict:
    """DE1-SoC pin table of the course (signal, FPGA pin, direction, notes such as active-low KEY and HEX); filter by group (SW, KEY, LEDR, HEX0..5, CLOCK_50, GPIO_0/1), signal or pin."""
    return pins.board_pins(filter_text)


def pin_check(vhdl_file: str) -> dict:
    """Checks the ports of the top-level entity in a VHDL file against the board pin names: which bits have a pin, which do not, and direction or vector problems."""
    return pins.pin_check(_read(vhdl_file))


def pin_plan(vhdl_file: str) -> dict:
    """Quartus pin assignments (set_location_assignment lines) for the ports of a VHDL file that match board signals; text only, nothing is written."""
    return pins.pin_plan(_read(vhdl_file))


def topics_list() -> dict:
    """Topic pages of the course (one per video lecture): number, title, video link, length and example code folder."""
    return topics.list_topics(os.getcwd())


def topics_search(query: str, limit: int = 8) -> dict:
    """Searches the topic pages (and the timestamped video contents) for a question or term; returns the matching paragraphs and video moments."""
    return topics.search_topics(query, os.getcwd(), limit)


def topic_get(number: int, section: str | None = None) -> dict:
    """A topic page or one of its sections (contents, key_terms, explanation, example, common_mistakes, self_check, further_material)."""
    return topics.get_topic(number, section, os.getcwd())


def glossary(term: str | None = None) -> dict:
    """Key terms of all topic pages with their explanations (Serbian or English, depending on the course repository); filter by term."""
    return topics.glossary(term, os.getcwd())


def quiz(topic: int | None = None, reveal_answers: bool = False) -> dict:
    """Self-check questions of the topic pages (one topic or all). Answers are included only with reveal_answers=True, after the student has answered."""
    return topics.self_check(topic, os.getcwd(), reveal_answers)


def video_notes() -> dict:
    """Notes on errors in the videos and on outdated tools, per topic (the course code and pages contain the corrections)."""
    return topics.video_notes(os.getcwd())


def tutorial_examples(topic: int | None = None) -> dict:
    """Example code of the video lectures (video-tutorials/); verified code, corrections of video errors are marked with NOTE comments."""
    return topics.examples(topic, os.getcwd())


def tutorial_example_read(file: str) -> dict:
    """Reads one file from video-tutorials/ (path as returned by tutorial_examples)."""
    return topics.read_example(file, os.getcwd())


PROFILES = {
    "course": [(env_check, READ_ONLY), (task_context, READ_ONLY_REMOTE), (pr_status, READ_ONLY_REMOTE), (course_doc, READ_ONLY)],
    "git": [(repo_state, READ_ONLY), (commit_check, READ_ONLY), (branch_check, READ_ONLY), (explain_command, READ_ONLY)],
    "design": [(style_report, READ_ONLY), (synth_summary, READ_ONLY), (vhdl_analyze, READ_ONLY), (board_pins, READ_ONLY), (pin_check, READ_ONLY), (pin_plan, READ_ONLY)],
    "testing": [(list_testbenches, READ_ONLY), (vhdl_analyze, READ_ONLY), (run_testbenches, READ_ONLY)],
    "learning": [(topics_list, READ_ONLY), (topics_search, READ_ONLY), (topic_get, READ_ONLY), (glossary, READ_ONLY), (quiz, READ_ONLY),
                 (video_notes, READ_ONLY), (tutorial_examples, READ_ONLY), (tutorial_example_read, READ_ONLY), (course_doc, READ_ONLY)],
}
PROFILES["all"] = list({f.__name__: (f, a) for p in PROFILES.values() for f, a in p}.values())

INSTRUCTIONS = ("Tools of the PDS (Projektovanje digitalnih sistema) course. All tools are read-only. "
                "Never run commands that change the repository or GitHub for the student: show the command, explain it "
                "(explain_command), let the student run it, then check the result with repo_state.")


def build(profile):
    if profile not in PROFILES:
        raise SystemExit(f"Unknown profile '{profile}'. Profiles: {', '.join(PROFILES)}")
    server = MCPServer(name=f"pds-{profile}", version=__version__, instructions=INSTRUCTIONS)
    for func, annotations in PROFILES[profile]:
        server.tool(annotations=annotations)(func)
    return server


def main(argv=None):
    parser = argparse.ArgumentParser(prog="pds-mcp", description="MCP server of the PDS course plugins (read-only tools).")
    parser.add_argument("--profile", default="all", help="tool set: " + ", ".join(PROFILES))
    parser.add_argument("--list", action="store_true", help="list the profiles and their tools")
    parser.add_argument("--version", action="version", version=f"pds-mcp {__version__}")
    args = parser.parse_args(argv)
    if args.list:
        for name, tools in PROFILES.items():
            print(f"{name}: {', '.join(f.__name__ for f, _ in tools)}")
        return 0
    build(args.profile).run("stdio")
    return 0


if __name__ == "__main__":
    sys.exit(main())
