"""Checking a constraint value the student calculated: verdicts and hints, never the correct value."""

import json

import pytest

from pds_tools import constraints


SOURCES = {"tco": "Device A: Tco = 2 ns (min) to 6 ns (max).", "tboard": "The board adds 0.5 ns (min) to 1 ns (max).",
           "tsetup": "Device B: Tsetup = 3 ns, Thold = 1 ns.", "thold": "Device B: Tsetup = 3 ns, Thold = 1 ns.",
           "tclk_board": "The clock trace adds 1 ns."}


def verdict(**kw):
    kw.setdefault("sources", SOURCES)
    return constraints.check(**kw)


def test_correct_values():
    assert verdict(kind="output", bound="min", student_value=-0.5, tboard=0.5, thold=1)["verdict"] == "correct"
    assert verdict(kind="output", bound="max", student_value=4, tboard=1, tsetup=3)["verdict"] == "correct"
    assert verdict(kind="input", bound="max", student_value=7, tco=6, tboard=1)["verdict"] == "correct"
    assert verdict(kind="input", bound="min", student_value=2.5, tco=2, tboard=0.5)["verdict"] == "correct"
    # Serbian task text with a decimal comma
    sr = {"tboard": "Linije na ploči dodaju 0,5 ns (min) do 1 ns (max).", "thold": "Uređaj B: `Tsetup` = 3 ns, `Thold` = 1 ns."}
    assert verdict(kind="output", bound="min", student_value=-0.5, tboard=0.5, thold=1, sources=sr)["verdict"] == "correct"
    # a clock sent by the FPGA: the clock trace is added for an input, subtracted for an output
    assert verdict(kind="input", bound="max", student_value=8, tco=6, tboard=1, tclk_board=1)["verdict"] == "correct"
    assert verdict(kind="output", bound="min", student_value=-1.5, tboard=0.5, thold=1, tclk_board=1)["verdict"] == "correct"


@pytest.mark.parametrize("kw,hint", [
    (dict(kind="output", bound="min", student_value=1.5, tboard=0.5, thold=1, student_expression="0.5 + 1"),
     "Wrong sign of Thold(ext)"),
    (dict(kind="output", bound="min", student_value=0.5, tboard=0.5, thold=1, student_expression="1 - 0.5"),
     "operands of the subtraction are swapped"),
    (dict(kind="input", bound="max", student_value=5, tco=6, tboard=1, student_expression="6 - 1"),
     "Wrong sign of Tboard(max)"),
    (dict(kind="input", bound="min", student_value=2, tco=2, tboard=0.5), "Tboard(min) is left out"),
])
def test_wrong_values_get_the_step_not_the_result(kw, hint):
    r = verdict(**kw)
    assert r["verdict"] == "wrong" and hint in r["hints"][0]
    assert "is left out" not in " ".join(r["hints"]) or "student_expression" not in kw
    text = json.dumps(r)
    correct = {"output": {"min": "-0.5"}, "input": {"max": "7", "min": "2.5"}}[kw["kind"]][kw["bound"]]
    assert correct not in text.replace(str(kw["student_value"]), "")  # the result is never in the answer
    assert "Smaller hint" in r["hints"][-1]


def test_missing_role_is_asked_not_guessed():
    r = verdict(kind="output", bound="min", student_value=-0.5, tboard=0.5)
    assert r["verdict"] == "unknown" and r["missing"] == ["thold"] and "do not guess" in r["next"]


def test_bad_kind():
    with pytest.raises(ValueError):
        verdict(kind="clock", bound="max", student_value=1, tboard=1)


def test_roles_must_match_their_source():
    # the live failure: the roles taken from the student's calculation "1 - 0.5" (tboard 1, thold 0.5)
    r = verdict(kind="output", bound="min", student_value=0.5, tboard=1, thold=0.5)
    assert r["verdict"] == "unknown" and len(r["source_problems"]) == 2 and "Do not answer yet" in r["next"]
    r = verdict(kind="output", bound="min", student_value=0.5, tboard=1, thold=0.5, sources={"tboard": "1 - 0.5", "thold": "1 - 0.5"})
    assert r["verdict"] == "unknown" and all("does not name" in p for p in r["source_problems"])
    # a -max value in a -min constraint
    r = verdict(kind="input", bound="min", student_value=7, tco=6, tboard=1)
    assert r["verdict"] == "unknown"
    assert verdict(kind="output", bound="min", student_value=-0.5, tboard=0.5, thold=1, sources={})["verdict"] == "unknown"


TASK = ("Uređaj A: `Tco` = 2 ns (min) do 6 ns (max). Uređaj B: `Tsetup` = 3 ns, `Thold` = 1 ns. "
        "Linije na ploči dodaju 0,5 ns (min) do 1 ns (max).")


def test_values_come_from_the_task_text():
    # the live failure: invented roles and quotes ("its Thold is 0.5 ns") are replaced by the task's values
    r = constraints.check("output", "min", 0.5, tboard=1, thold=0.5, student_expression="1 - 0.5", task_text=TASK,
                          sources={"tboard": "board delay is 1 ns", "thold": "its Thold is 0.5 ns"})
    assert r["verdict"] == "wrong" and "swapped" in r["hints"][0] and "differ from the task text" in r["warning"]
    assert constraints.check("output", "min", -0.5, task_text=TASK)["verdict"] == "correct"
    assert constraints.check("input", "max", 7, task_text=TASK)["verdict"] == "correct"
    assert constraints.check("input", "min", 2.5, task_text=TASK)["verdict"] == "correct"
    assert constraints.check("output", "max", 4, task_text=TASK)["verdict"] == "correct"
    assert set(constraints.check("output", "max", 4, task_text=TASK)["from_task"]) == {"tboard", "tsetup"}
