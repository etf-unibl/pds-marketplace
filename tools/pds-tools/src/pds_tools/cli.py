"""Command line access to the same read-only tools as the MCP server (JSON output).

    pds-tools repo_state
    pds-tools topics_search "latch"
    pds-tools run_testbenches assignments/12
    pds-tools --list
"""

import argparse
import inspect
import json
import sys

from . import mcp_server


def main(argv=None):
    # Course texts are Serbian; the Windows console encoding (cp1252) cannot print them
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    tools = {f.__name__: f for f, _ in mcp_server.PROFILES["all"]}
    parser = argparse.ArgumentParser(prog="pds-tools", description="Read-only tools of the PDS course plugins (JSON output).")
    parser.add_argument("tool", nargs="?", help="tool name (see --list)")
    parser.add_argument("args", nargs="*", help="positional arguments, or name=value")
    parser.add_argument("--list", action="store_true", help="list the tools")
    a = parser.parse_args(argv)
    if a.list or not a.tool:
        for name, f in tools.items():
            print(f"{name}{inspect.signature(f)}\n    {inspect.getdoc(f).splitlines()[0]}")
        return 0
    if a.tool not in tools:
        print(f"Unknown tool {a.tool}; see pds-tools --list", file=sys.stderr)
        return 2
    func = mcp_server.safe(tools[a.tool])
    params = list(inspect.signature(func).parameters.values())
    positional, named = [], {}
    for arg in a.args:
        if "=" in arg and arg.split("=", 1)[0] in {p.name for p in params}:
            k, v = arg.split("=", 1)
            named[k] = v
        else:
            positional.append(arg)
    bound = {}
    for p, v in zip(params, positional):
        bound[p.name] = v
    bound.update(named)
    for p in params:
        if p.name in bound:
            v = bound[p.name]
            ann = str(p.annotation)
            if "list" in ann:
                bound[p.name] = v.split(",") if isinstance(v, str) else v
            elif "int" in ann and v not in (None, "None"):
                bound[p.name] = int(v)
            elif "bool" in ann:
                bound[p.name] = str(v).lower() in ("1", "true", "yes")
    print(json.dumps(func(**bound), indent=2, ensure_ascii=False, default=str))
    return 0


if __name__ == "__main__":
    sys.exit(main())
