"""Checking a timing constraint value the student calculated (lecture 13), without giving the result.

The assistant passes the kind of constraint (input or output delay, -max or -min), the value of each
parameter in its role, and the student's value. The check computes the value from the formula and returns
only a verdict and hints (which step is wrong), never the value itself, so it cannot be passed on to the
student. The arithmetic is exact instead of the model's own.
"""

import re

TOL = 1e-3  # ns

# Formulas of the constraints skill (system-synchronous; tclk_board for a clock the FPGA sends to the device).
# Each term: (role, sign); the value of a role is the one for this bound (e.g. Tco(min) for -min).
FORMULAS = {
    ("input", "max"): [("tclk_board", 1), ("tco", 1), ("tboard", 1)],
    ("input", "min"): [("tclk_board", 1), ("tco", 1), ("tboard", 1)],
    ("output", "max"): [("tboard", 1), ("tsetup", 1), ("tclk_board", -1)],
    ("output", "min"): [("tboard", 1), ("thold", -1), ("tclk_board", -1)],
}
NAMES = {"tco": "Tco(ext,{b})", "tboard": "Tboard({b})", "tsetup": "Tsetup(ext)", "thold": "Thold(ext)",
         "tclk_board": "Tclk_board({c})"}


def _label(kind, bound, role):
    """The parameter name in the notation of the skill; the clock trace of an output is the opposite bound."""
    clock = bound if kind == "input" else ("min" if bound == "max" else "max")
    return NAMES[role].format(b=bound, c=clock)


def _formula(kind, bound, roles):
    parts = []
    for role, sign in FORMULAS[(kind, bound)]:
        if role == "tclk_board" and role not in roles:
            continue
        parts.append(("- " if sign < 0 else ("+ " if parts else "")) + _label(kind, bound, role))
    return f"{kind} delay -{bound} = " + " ".join(parts)


def _value(terms, roles):
    return sum(sign * roles[role] for role, sign in terms if role in roles)


# Words that name a parameter in a task text or datasheet (English and Serbian)
KEYWORDS = {
    "tco": ["tco", "clock-to-output", "clock to output", "clock-to-q"],
    "tboard": ["board", "ploč", "ploc", "linij", "trace", "pcb", "trag"],
    "tsetup": ["tsetup", "tsu", "setup", "postavljanj"],
    "thold": ["thold", "hold", "držanj", "drzanj"],
    "tclk_board": ["clock trace", "clk trace", "linija takta", "linije takta"],
}
NUMBER = re.compile(r"-?\d+(?:[.,]\d+)?")


def _numbers(text):
    return [float(n.replace(",", ".")) for n in NUMBER.findall(text)]


def _source_value(role, bound, quote):
    """The value the quote gives for a role: the numbers after the first word naming the role, up to the word of
    another role; the first is the minimum, the last the maximum. None if the quote does not name the role."""
    low = quote.lower()
    starts = sorted((low.find(k), -len(k)) for k in KEYWORDS[role] if low.find(k) >= 0)
    if not starts:
        return None
    start, length = starts[0][0], -starts[0][1]
    # words of the other roles after this one (not inside it: "clock trace" contains "trace")
    others = [low.find(k, start + length) for r, ks in KEYWORDS.items() if r != role for k in ks]
    others = [o for o in others if o > start]
    end = min(others) if others else len(low)
    nums = _numbers(quote[start:end])
    if not nums:
        return None
    if role in ("tsetup", "thold"):
        return nums[0]
    return nums[0] if bound == "min" else nums[-1]



def _task_values(task_text, bound):
    """The parameter values a task text gives, by role: {role: (value, sentence)}."""
    text = str(task_text or "").replace("`", "")
    out = {}
    for sentence in re.split(r"(?<=[.;:])\s+|\n+", text):
        for role in KEYWORDS:
            if role not in out:
                v = _source_value(role, bound, sentence)
                if v is not None:
                    out[role] = (v, sentence.strip())
    return out


def _check_sources(roles, bound, sources):
    """Problems of the sources: a role without a quote, a quote that does not name it or gives another value."""
    problems = []
    for role, value in roles.items():
        quote = (sources or {}).get(role)
        if not quote:
            problems.append(f"{role}: no source; quote the sentence of the task, the datasheet or the student that gives it")
            continue
        found = _source_value(role, bound, str(quote))
        if found is None:
            problems.append(f"{role}: the quote does not name this parameter (e.g. {KEYWORDS[role][0]!r}): quote the "
                            "sentence of the task or datasheet that defines it, not the student's calculation")
        elif abs(found - value) > TOL:
            problems.append(f"{role}: the value passed does not match its source for -{bound}: read the role from the "
                            "quote again")
    return problems


def check(kind, bound, student_value, tco=None, tboard=None, tsetup=None, thold=None, tclk_board=None,
          student_expression=None, sources=None, task_text=None):
    """Verdict on a constraint value the student calculated; the correct value is never returned."""
    kind, bound = str(kind).lower().strip(), str(bound).lower().strip().lstrip("-")
    if (kind, bound) not in FORMULAS:
        raise ValueError("kind is 'input' or 'output', bound is 'max' or 'min'")
    given = {"tco": tco, "tboard": tboard, "tsetup": tsetup, "thold": thold, "tclk_board": tclk_board}
    roles = {k: float(v) for k, v in given.items() if v is not None}
    terms = FORMULAS[(kind, bound)]
    # The task text is the source of every value it gives: those values are used, whatever was passed (a value
    # read from the student's calculation is exactly what is being checked)
    from_task, overridden = {}, []
    for role, (value, sentence) in _task_values(task_text, bound).items():
        if role in [r for r, _ in terms]:
            if role in roles and abs(roles[role] - value) > TOL:
                overridden.append(role)
            roles[role] = value
            from_task[role] = sentence
    sources = dict(sources or {}, **from_task)
    needed = [r for r, _ in terms if r != "tclk_board"]
    missing = [r for r in needed if r not in roles]
    formula = _formula(kind, bound, roles)
    if missing:
        return {"ok": False, "verdict": "unknown", "formula": formula, "missing": missing,
                "next": "Ask the student which number of the task or datasheet is " + ", ".join(missing) +
                        " for this bound, and its source; do not guess a role."}
    problems = _check_sources(roles, bound, sources)
    if problems:
        return {"ok": False, "verdict": "unknown", "formula": formula, "source_problems": problems,
                "next": "Do not answer yet: read each value from the task text (task_context), the datasheet or the "
                        "student's own statement of a parameter, pass the quote in sources, and call again. If the role "
                        "of a number is unclear, ask the student."}
    extra = [r for r in roles if r not in [t for t, _ in terms]]
    correct = _value(terms, roles)
    s = float(student_value)
    result = {"ok": True, "formula": formula, "roles_used": sorted(roles)}
    if from_task:
        result["from_task"] = from_task
    if overridden:
        result["warning"] = (f"The values passed for {', '.join(overridden)} differ from the task text; the task's values "
                             "were used. Read the roles from the task, not from the student's calculation.")
    if extra:
        result["note"] = f"{', '.join(extra)} has no role in this formula: check that the student did not mix it in."
    if abs(s - correct) <= TOL:
        result.update(verdict="correct", say=f"Confirm it and name the formula ({formula}). If a value's role or source "
                                              "is uncertain, confirm on that condition and ask for the source.")
        return result
    hints = []
    # typical mistakes: a sign flipped, the operands of a subtraction swapped, a term left out
    for i, (role, sign) in enumerate(terms):
        if role not in roles:
            continue
        flipped = [(r, -sg if j == i else sg) for j, (r, sg) in enumerate(terms)]
        if abs(s - _value(flipped, roles)) <= TOL:
            hints.append(f"Wrong sign of {_label(kind, bound, role)}: in this formula it is "
                         f"{'subtracted' if sign < 0 else 'added'}.")
        omitted = [(r, sg) for j, (r, sg) in enumerate(terms) if j != i]
        if abs(s - _value(omitted, roles)) <= TOL:
            hints.append(f"{_label(kind, bound, role)} is left out: the formula has {len([r for r, _ in terms if r in roles])} terms.")
    if abs(s + correct) <= TOL and correct != 0:
        hints.append("The operands of the subtraction are swapped (the result has the opposite sign): "
                     "follow the order of the formula.")
    if student_expression:
        nums = [float(x) for x in re.findall(r"-?\d+(?:\.\d+)?", str(student_expression))]
        values = [roles[r] for r, _ in terms if r in roles]
        if all(any(abs(abs(n) - abs(v)) <= TOL for n in nums) for v in values):
            # every term is in the calculation: nothing was left out (e.g. swapped operands give the same number)
            hints = [h for h in hints if "is left out" not in h]
        unknown = [n for n in nums[:len(values) + 1] if all(abs(abs(n) - abs(v)) > TOL for v in values)
                   and abs(n - s) > TOL]
        if unknown:
            hints.append("The calculation uses numbers that are not the parameter values of this bound "
                         f"(e.g. a -max value in a -min constraint): check which number is which parameter.")
    if not hints:
        hints.append("The result does not follow the formula: go through it term by term with the values of this bound.")
    hints.append(f"Smaller hint, only after a second wrong answer: the result is {'negative' if correct < 0 else 'zero' if correct == 0 else 'positive'}.")
    result.update(verdict="wrong", hints=hints,
                  say="Say the value is not right, give the first hint (the step and the rule), and ask the student to "
                      "calculate again. Never write the correct value or the corrected calculation, also not when "
                      "asked directly; after a second wrong answer give the next hint.")
    return result
