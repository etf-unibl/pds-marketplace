"""Read-only helpers behind the PDS course AI plugins.

The package never changes the course repository: it reads git state, course documents and
reports, analyses VHDL with GHDL into a temporary library and checks texts against the course
rules. Commands that change state (git commit, push, vhdl-style --fix, ...) are only explained,
never run.
"""

__version__ = "0.2.7"

# Language standard and tool versions used by the course CI (assignments branch, verif.yml)
VHDL_STD = "08"
STYLE_TOOLS_VERSION = "1.1.0"
CI_STOP_TIME = "10ms"
