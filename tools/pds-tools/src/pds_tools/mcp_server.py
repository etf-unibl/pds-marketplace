"""MCP server of the PDS plugins: one server, one profile per plugin.

    pds-mcp --profile git        # tools of the pds-git plugin
    pds-mcp --profile learning   # tools of the pds-learning plugin
    pds-mcp --list               # profiles and their tools

All tools are read-only (MCP read-only hint). The server runs over stdio in the folder the AI
tool starts it in, normally the student's course repository.
"""

import argparse
import functools
import inspect
import os
import re
import sys
import urllib.parse

from mcp.server.mcpserver import Context, MCPServer
from mcp.types import ToolAnnotations

from . import __version__, env, explain, github, hdl, pins, quartus, quartus_run, repo, rules, topics

READ_ONLY = ToolAnnotations(readOnlyHint=True, destructiveHint=False, idempotentHint=True, openWorldHint=False)
READ_ONLY_REMOTE = ToolAnnotations(readOnlyHint=True, destructiveHint=False, idempotentHint=True, openWorldHint=True)
# Quartus tools write into the Quartus project folder outside the repository; Tcl and programming the board act on the user's machine
PROJECT_FILES = ToolAnnotations(readOnlyHint=False, destructiveHint=False, idempotentHint=False, openWorldHint=False)
ACTS = ToolAnnotations(readOnlyHint=False, destructiveHint=True, idempotentHint=False, openWorldHint=False)


def _read(path):
    with open(path, encoding="utf-8", errors="replace") as f:
        return f.read()


# ---- tool functions (thin wrappers with docstrings that the AI tool sees) ----

def env_check() -> dict:
    """Checks the student's environment: git, GHDL, vhdl-style, gh, Quartus and ModelSim/Questa on PATH, git identity (noreply e-mail) and course hooks."""
    return env.env_check(base())


def task_context(issue: int | None = None) -> dict:
    """Context of a course issue (default: the issue of the current branch): title, kind (test/graded), group, deadline, folder, expected branch prefix, commit subject and PR title."""
    return github.task_context(issue, base())


def pr_status(pr: int | None = None) -> dict:
    """Pull request of the current branch (or number pr): the course rule checks (title, branch, assignee, files, commits, description) and the CI results with error annotations."""
    return github.pr_status(pr, base())


def time_summary(issue: int | None = None) -> dict:
    """Time logged with /spent comments on an issue (default: the issue of the current branch), per author, with invalid lines, as the time tracking workflow counts it."""
    return github.time_summary(issue, base())


def spent_check(text: str) -> dict:
    """Checks a /spent comment draft: which lines are valid entries (hours, note) and which would be rejected."""
    valid, invalid = rules.spent_entries(text)
    return {"ok": bool(valid) and not invalid, "entries": valid, "invalid": invalid,
            "format": "/spent <duration> <description>, duration like 2h, 1.5h, 1,5h, 1h30m, 90m, 45min (at most 24h per line)"}


def course_doc(name: str | None = None) -> dict:
    """A course guide from docs/ (e.g. assignment-submission, simulation-and-testing, vhdl-code-style); without a name, the list of guides."""
    return topics.course_doc(name, base())


def repo_state() -> dict:
    """State of the working copy: branch, issue, staged/unstaged/untracked files, files outside assignments/<N>/, upstream ahead/behind, merge/rebase in progress, hooks and identity."""
    return repo.repo_state(base())


def commit_check(message: str, issue: int | None = None, issue_title: str | None = None) -> dict:
    """Checks a commit message draft against the course format (and the exact issue title if given). The sign-off is checked against the git identity of the repository."""
    root = repo.find_root(base())
    name = repo.git(["config", "--get", "user.name"], cwd=root, check=False) if root else None
    email = repo.git(["config", "--get", "user.email"], cwd=root, check=False) if root else None
    branch = repo.git(["branch", "--show-current"], cwd=root, check=False) if root else None
    findings = rules.check_commit_message(message, issue, issue_title, name or None, email or None, branch)
    return {"ok": not rules.errors(findings), "findings": [f.as_dict() for f in findings]}


def branch_check(issue_title: str | None = None, base: str = "origin/assignments") -> dict:
    """Checks the commits of the current branch that are not on base, like the CI pr-checks job (format, sign-off, issue number)."""
    return repo.check_branch_commits(_repo_base(), base, issue_title)


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
    return hdl.style_report(target, base())


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
    return topics.list_topics(base())


def topics_search(query: str, limit: int = 8) -> dict:
    """Searches the topic pages (and the timestamped video contents) for a question or term; returns the matching paragraphs and video moments."""
    return topics.search_topics(query, base(), limit)


def topic_get(number: int, section: str | None = None) -> dict:
    """A topic page or one of its sections (contents, key_terms, explanation, example, common_mistakes, self_check, further_material)."""
    return topics.get_topic(number, section, base())


def glossary(term: str | None = None) -> dict:
    """Key terms of all topic pages with their explanations (Serbian or English, depending on the course repository); filter by term."""
    return topics.glossary(term, base())


def quiz(topic: int | None = None, reveal_answers: bool = False) -> dict:
    """Self-check questions of the topic pages (one topic or all). Answers are included only with reveal_answers=True, after the student has answered."""
    return topics.self_check(topic, base(), reveal_answers)


def video_notes() -> dict:
    """Notes on errors in the videos and on outdated tools, per topic (the course code and pages contain the corrections)."""
    return topics.video_notes(base())


def tutorial_examples(topic: int | None = None) -> dict:
    """Example code of the video lectures (video-tutorials/); verified code, corrections of video errors are marked with NOTE comments."""
    return topics.examples(topic, base())


def tutorial_example_read(file: str) -> dict:
    """Reads one file from video-tutorials/ (path as returned by tutorial_examples)."""
    return topics.read_example(file, base())


def tutorial_example_run(folder: str) -> dict:
    """Analyses and simulates (with GHDL, like CI) an example folder of video-tutorials/ from the course repository, without changing the working copy; examples with *_tb.vhd are simulated, others analysed."""
    return topics.run_example(folder, base())


def quartus_env() -> dict:
    """Quartus Prime installation: bin folder, version, Cyclone V (DE1-SoC) support, available command-line tools."""
    return quartus_run.quartus_env()


def quartus_project_create(sources: list[str], top: str | None = None, project_dir: str | None = None,
                           assign_pins: bool = True, clock_mhz: float = 50.0, overwrite: bool = False) -> dict:
    """Creates a Quartus project for a task folder or VHDL files (testbenches left out): DE1-SoC device 5CSEMA5F31C6, VHDL-2008, top-level entity (detected if not given), pins for ports named like board signals (SW, KEY, LEDR, HEX0..5, CLOCK_50, GPIO) with 3.3-V LVTTL, clock constraint for a clock port. The project folder is outside the repository (default: <repository>-quartus/<task>-<top> next to it). Writes and runs create_project.tcl and returns it."""
    return quartus_run.project_create([base_path(s) for s in sources], top, base_path(project_dir) if project_dir else None,
                                      assign_pins=assign_pins, clock_mhz=clock_mhz, overwrite=overwrite)


def quartus_compile(project_dir: str, flow: str = "synthesis", revision: str | None = None) -> dict:
    """Runs Quartus on a project: flow 'synthesis' (Analysis & Synthesis), 'fit', 'timing', 'assemble' or 'full' (complete compilation, produces the .sof). Returns errors, critical warnings, the synthesis review (latches, removed registers) and the commands it ran."""
    return quartus_run.compile(base_path(project_dir), flow, revision)


def quartus_timing(project_dir: str, paths: int = 10, revision: str | None = None) -> dict:
    """Timing analysis of a compiled project (quartus_sta): setup and hold slack and TNS per clock over all corners, Fmax, the worst setup and hold paths (from, to, data delay, skew), unconstrained paths, check_timing warnings. Writes pds_timing.tcl in the project folder."""
    return quartus_run.timing_analysis(base_path(project_dir), revision, paths)


def quartus_tcl(script: str, tool: str = "quartus_sh", project_dir: str | None = None) -> dict:
    """Runs a Tcl script (file path or script text) with quartus_sh -t or quartus_sta -t in the Quartus project folder and returns its output."""
    return quartus_run.tcl_run(base_path(script) if os.path.isfile(base_path(script)) else script, tool,
                               base_path(project_dir) if project_dir else None)


def board_cables() -> dict:
    """Programming cables (USB-Blaster) that quartus_pgm sees."""
    return quartus_run.program_cables()


def board_program(sof: str, cable: str | None = None) -> dict:
    """Programs the DE1-SoC FPGA with a .sof file over JTAG (volatile: lost when the board is switched off)."""
    return quartus_run.program_board(base_path(sof), cable)


def base_path(path):
    """A path relative to the workspace (the course repository) or absolute."""
    return path if os.path.isabs(path) else os.path.join(base(), path)


PROFILES = {
    "course": [(env_check, READ_ONLY), (task_context, READ_ONLY_REMOTE), (pr_status, READ_ONLY_REMOTE), (time_summary, READ_ONLY_REMOTE),
               (spent_check, READ_ONLY), (course_doc, READ_ONLY)],
    "git": [(repo_state, READ_ONLY), (commit_check, READ_ONLY), (branch_check, READ_ONLY), (explain_command, READ_ONLY)],
    "design": [(style_report, READ_ONLY), (synth_summary, READ_ONLY), (vhdl_analyze, READ_ONLY), (board_pins, READ_ONLY), (pin_check, READ_ONLY), (pin_plan, READ_ONLY)],
    "testing": [(list_testbenches, READ_ONLY), (vhdl_analyze, READ_ONLY), (run_testbenches, READ_ONLY)],
    "learning": [(topics_list, READ_ONLY), (topics_search, READ_ONLY), (topic_get, READ_ONLY), (glossary, READ_ONLY), (quiz, READ_ONLY),
                 (video_notes, READ_ONLY), (tutorial_examples, READ_ONLY), (tutorial_example_read, READ_ONLY), (tutorial_example_run, READ_ONLY),
                 (course_doc, READ_ONLY)],
    "quartus": [(quartus_env, READ_ONLY), (quartus_project_create, PROJECT_FILES), (quartus_compile, PROJECT_FILES),
                (quartus_timing, PROJECT_FILES), (synth_summary, READ_ONLY), (board_pins, READ_ONLY), (pin_check, READ_ONLY),
                (pin_plan, READ_ONLY), (board_cables, READ_ONLY), (quartus_tcl, ACTS), (board_program, ACTS)],
}
PROFILES["all"] = list({f.__name__: (f, a) for p in PROFILES.values() for f, a in p}.values())

INSTRUCTIONS = ("Tools of the PDS (Projektovanje digitalnih sistema) course. All tools are read-only. "
                "Never run commands that change the repository or GitHub for the student: show the command, explain it "
                "(explain_command), let the student run it, then check the result with repo_state.")


_workdir = None


def base():
    """The student's course repository: PDS_REPO, the server's working directory if it is a git
    repository, or the workspace root reported by the AI tool (resolved by the first tool call)."""
    return _workdir or os.environ.get("PDS_REPO") or os.getcwd()


_repo_base = base  # branch_check has a parameter named base


async def resolve_workdir(ctx):
    global _workdir
    if _workdir:
        return
    if os.environ.get("PDS_REPO"):
        _workdir = os.environ["PDS_REPO"]
        return
    # The client's workspace roots come first: e.g. Copilot CLI starts plugin servers in the plugin
    # folder, not in the project
    debug = os.environ.get("PDS_DEBUG_LOG")
    try:
        caps = ctx.client_capabilities
        if debug:
            with open(debug, "a", encoding="utf-8") as f:
                f.write(f"cwd={os.getcwd()} roots_capability={getattr(caps, 'roots', None) if caps else None}\n")
                f.write("env names=" + ", ".join(k for k in sorted(os.environ) if any(x in k.upper() for x in ("COPILOT", "PWD", "CLAUDE", "PLUGIN", "WORKSPACE", "PROJECT", "GEMINI"))) + "\n")
        if caps is not None and getattr(caps, "roots", None) is not None:
            result = await ctx.session.list_roots()
            if debug:
                with open(debug, "a", encoding="utf-8") as f:
                    f.write(f"roots={[str(r.uri) for r in result.roots]}\n")
            for root in result.roots:
                uri = str(root.uri)
                if uri.startswith("file://"):
                    path = urllib.parse.unquote(urllib.parse.urlparse(uri).path)
                    if re.match(r"^/[A-Za-z]:", path):
                        path = path[1:]  # file:///C:/x on Windows
                    if repo.find_root(path):
                        _workdir = path
                        return
    except Exception:  # noqa: BLE001 - fall back to the other sources
        pass
    _workdir = fallback_workdir()
    if debug:
        with open(debug, "a", encoding="utf-8") as f:
            f.write(f"workdir={_workdir}\n")


def _inside(path, folder):
    try:
        return bool(folder) and os.path.commonpath([os.path.abspath(path), os.path.abspath(folder)]) == os.path.abspath(folder)
    except ValueError:
        return False


def fallback_workdir():
    """Working directory when the client gives no roots: the server's own directory unless it is the
    plugin folder (Copilot CLI starts plugin servers there), the working directory of the nearest
    parent process (the AI tool session) that is inside a git repository, or PWD."""
    plugin_root = os.environ.get("CLAUDE_PLUGIN_ROOT") or os.environ.get("COPILOT_PLUGIN_ROOT") or os.environ.get("PLUGIN_ROOT")
    candidates = [os.getcwd()]
    try:
        import psutil
        proc = psutil.Process().parent()
        for _ in range(6):
            if proc is None:
                break
            try:
                candidates.append(proc.cwd())
            except (psutil.AccessDenied, psutil.NoSuchProcess, psutil.ZombieProcess):
                pass
            proc = proc.parent()
    except ImportError:
        pass
    # PWD last: it is inherited from whichever shell started the AI tool and may be stale
    candidates.append(os.environ.get("PWD"))
    for c in candidates:
        if c and os.path.isdir(c) and not _inside(c, plugin_root) and repo.find_root(c):
            return c
    return os.getcwd()


def with_workspace(func):
    """Async tool wrapper that resolves the workspace (MCP roots) before calling the tool."""
    params = list(inspect.signature(func).parameters.values())

    async def wrapper(ctx: Context, **kwargs):
        await resolve_workdir(ctx)
        return func(**kwargs)

    wrapper.__name__ = func.__name__
    wrapper.__doc__ = func.__doc__
    wrapper.__signature__ = inspect.Signature(params + [inspect.Parameter("ctx", inspect.Parameter.KEYWORD_ONLY, annotation=Context)],
                                              return_annotation=dict)
    wrapper.__annotations__ = {**getattr(func, "__annotations__", {}), "ctx": Context}
    return wrapper


def safe(func):
    """Returns errors as {ok: false, error, message} instead of raising, so the assistant can explain them."""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:  # noqa: BLE001 - every failure is reported to the assistant
            return {"ok": False, "error": type(e).__name__, "message": str(e)}
    return wrapper


def build(profile):
    if profile not in PROFILES:
        raise SystemExit(f"Unknown profile '{profile}'. Profiles: {', '.join(PROFILES)}")
    server = MCPServer(name=f"pds-{profile}", version=__version__, instructions=INSTRUCTIONS)
    for func, annotations in PROFILES[profile]:
        server.tool(annotations=annotations)(with_workspace(safe(func)))
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
