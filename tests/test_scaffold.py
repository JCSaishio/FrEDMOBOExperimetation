"""Acceptance test for milestone M0 — scaffold.

§9.4 M0 accepts when "pytest passes on an empty suite; PLAN.md lists M1-M9 with checkboxes".

"Empty suite" means no *milestone* tests yet, not no tests at all: a suite that collects nothing
exits 5, which would fail CI and tell us nothing. So M0 is verified by checking the layout it is
supposed to have produced — that every module §9.3 names exists and imports, that CLAUDE.md is
within its stated cap, and that PLAN.md really does list the milestones.
"""
from __future__ import annotations

import importlib
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]

# The twelve backend modules named in §9.3.
BACKEND_MODULES = [
    "config", "space", "extraction", "power", "models", "constraints",
    "acquisition", "pareto", "storage", "campaign", "simulate", "export",
]

# The nine UI windows of §7.3.
UI_TABS = [
    "settings", "intake", "pareto", "design_space", "gp",
    "kernel", "next", "convergence", "simulation",
]


@pytest.mark.parametrize("name", BACKEND_MODULES)
def test_backend_module_exists_and_imports(name: str) -> None:
    """Every module in the §9.3 layout is present and importable."""
    assert (ROOT / "fred_mobo" / f"{name}.py").is_file(), f"fred_mobo/{name}.py missing"
    mod = importlib.import_module(f"fred_mobo.{name}")
    assert mod.__doc__, f"fred_mobo/{name}.py has no module docstring"


@pytest.mark.parametrize("name", BACKEND_MODULES)
def test_backend_module_cites_the_spec(name: str) -> None:
    """§9.7: every module docstring cites the section of the record it implements."""
    mod = importlib.import_module(f"fred_mobo.{name}")
    assert "Implements:" in (mod.__doc__ or ""), (
        f"fred_mobo/{name}.py docstring does not say what it implements"
    )


@pytest.mark.parametrize("name", UI_TABS)
def test_ui_tab_exists(name: str) -> None:
    """The nine §7.3 windows have placeholders. Not imported — PySide6 is not installed until M8."""
    assert (ROOT / "fred_mobo" / "ui" / "tabs" / f"{name}.py").is_file()


def test_package_imports() -> None:
    import fred_mobo

    assert fred_mobo.__doc__


def test_claude_md_within_line_cap() -> None:
    """§9.3 specifies "CLAUDE.md # 40 lines max"."""
    lines = (ROOT / "CLAUDE.md").read_text(encoding="utf-8").splitlines()
    non_blank = [ln for ln in lines if ln.strip()]
    assert len(non_blank) <= 40, f"CLAUDE.md has {len(non_blank)} non-blank lines, cap is 40"


def test_plan_lists_every_milestone_with_a_checkbox() -> None:
    """The stated M0 acceptance criterion."""
    plan = (ROOT / "docs" / "PLAN.md").read_text(encoding="utf-8")
    for milestone in ["M1", "M2", "M3", "M4", "M5", "M6", "M6b", "M7", "M8", "M9"]:
        pattern = rf"- \[[ x]\] \*\*{re.escape(milestone)} "
        assert re.search(pattern, plan), f"PLAN.md has no checkbox entry for {milestone}"


def test_required_docs_exist() -> None:
    """§9.3: the three docs/ files plus the architecture record itself."""
    for name in ["PLAN.md", "PROGRESS.md", "DECISIONS.md", "ARCHITECTURE.pdf"]:
        assert (ROOT / "docs" / name).is_file(), f"docs/{name} missing"


def test_reference_csv_is_present_and_has_the_device_schema() -> None:
    """The example CSV is committed so a clone is self-contained (§9.3 data/examples/).

    It is a *schema* fixture, not an acceptance fixture — see DECISIONS D2. All this asserts is
    that the device column names and the separator/decimal convention are what extraction.py will
    be written against.
    """
    device = ROOT / "data" / "examples" / "fred_experiment_withgraphing.csv"
    assert device.is_file(), "device example CSV missing from data/examples/"

    header = device.read_text(encoding="utf-8-sig").splitlines()[0]
    assert ";" in header, "device CSV is semicolon-separated (§2.3 step 1)"
    for column in ["Time (s)", "Temperature (C)", "Diameter raw (mm)", "Spooler setpoint (RPM)"]:
        assert column in header, f"expected device column {column!r} missing"


def test_power_log_example_matches_the_requirements_file() -> None:
    """data/examples/power_log_example.csv is the shape docs/POWER_LOG_REQUIREMENTS.docx specifies
    (F1 dialect, F2 header names, F6 markers) and the shape PowerConfig defaults to. A glob-order
    bug once made CI read this file as the device CSV — hence both files are named explicitly.
    """
    from fred_mobo.config import POWER_LOG_COLUMNS, default_2d_campaign

    path = ROOT / "data" / "examples" / "power_log_example.csv"
    assert path.is_file(), "power-log example CSV missing from data/examples/"
    lines = path.read_text(encoding="utf-8").splitlines()
    power = default_2d_campaign().power
    header = lines[0].split(power.separator)
    assert header == list(POWER_LOG_COLUMNS.values()), "header must match the F2 names, in order"
    events = [line.split(power.separator)[-1] for line in lines[1:]]
    assert events.count(power.run_start_marker) == 1 and events.count(power.run_stop_marker) == 1
    assert any(cell == "" for line in lines[1:] for cell in line.split(power.separator)[1:7]), (
        "the example must show a missing sample as an empty cell (F7)"
    )
