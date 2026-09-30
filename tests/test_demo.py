"""Smoke test: the README quickstart demo runs and prints what the README shows."""

import runpy
from pathlib import Path

DEMO = Path(__file__).resolve().parent.parent / "examples" / "demo.py"


def test_demo_output(capsys):
    runpy.run_path(str(DEMO), run_name="__main__")
    out = capsys.readouterr().out
    assert "Cohort: 600; eligible: 487" in out
    assert "e3/e3: 20 selected; F=10, M=10; ages 18-80" in out
    assert "e4/e4: 12 selected; F=8, M=4; ages 21-76  (short by 8)" in out
