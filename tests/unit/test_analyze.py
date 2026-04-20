"""Tests for analyze and checklist."""
from __future__ import annotations

import pytest

from sk_harness.analyze import analyze_iteration, format_report
from sk_harness.checklist import generate_checklist
from sk_harness.dag.parser import write_sidecars
from sk_harness.paths import Paths
from sk_harness.state.models import TaskMeta


@pytest.fixture
def iteration(tmp_path):
    root = tmp_path / "proj"
    for d in [
        ".skspec/prd", ".skspec/tests",
        ".skspec/.erd", ".skspec/.task/tasks-001", ".skspec/.progress",
    ]:
        (root / d).mkdir(parents=True, exist_ok=True)
    (root / ".skspec/.version").write_text("0.3.0\n")
    paths = Paths(root)
    paths.plan("001").write_text(
        "# ERD\n\n## 1. Intro\n\n## 2. Components\n\n## 3. State\n"
    )
    paths.tasks("001").write_text("# Tasks\n\n### T-01\n- deps: []\n")
    paths.test_plan("001").write_text(
        "# Test Plan\n\n| ID | Scenario |\n|---|---|\n"
        "| SM-01 | smoke |\n| SM-02 | second |\n| OBS-01 | obs |\n"
    )
    return paths


def _make_task(**kwargs) -> TaskMeta:
    base = dict(
        id="T-01", title="init", deps=[], agent="general-purpose",
        validator="code-reviewer", idempotent=True, outputs=[],
        acceptance_ids=["SM-01"], estimate="S", erd_refs=["§1"],
    )
    base.update(kwargs)
    return TaskMeta(**base)


def test_analyze_pass(iteration) -> None:
    tasks = [
        _make_task(id="T-01", acceptance_ids=["SM-01"], erd_refs=["§1"]),
        _make_task(id="T-02", deps=["T-01"], acceptance_ids=["SM-02", "OBS-01"], erd_refs=["§2", "§3"]),
    ]
    write_sidecars(iteration.task_sidecar_dir("001"), tasks)
    r = analyze_iteration(iteration, "001")
    assert r.ok, f"failures: {r.failures}"
    assert r.checks_passed == 4


def test_analyze_missing_section(iteration) -> None:
    tasks = [_make_task(id="T-01", erd_refs=["§99"])]
    write_sidecars(iteration.task_sidecar_dir("001"), tasks)
    r = analyze_iteration(iteration, "001")
    assert not r.ok
    assert any("§99" in f for f in r.failures)


def test_analyze_missing_acceptance_id(iteration) -> None:
    tasks = [_make_task(id="T-01", acceptance_ids=["SM-999"])]
    write_sidecars(iteration.task_sidecar_dir("001"), tasks)
    r = analyze_iteration(iteration, "001")
    assert not r.ok
    assert any("SM-999" in f for f in r.failures)


def test_analyze_no_sidecars(iteration) -> None:
    r = analyze_iteration(iteration, "001")
    assert not r.ok


def test_format_report() -> None:
    from sk_harness.analyze import AnalyzeResult
    ok = AnalyzeResult(iteration="001", checks_passed=4)
    assert "all checks passed" in format_report(ok)
    bad = AnalyzeResult(iteration="002", checks_passed=2, failures=["T-05 broken"])
    report = format_report(bad)
    assert "FAIL" in report
    assert "T-05" in report


def test_checklist(iteration) -> None:
    tasks = [
        _make_task(id="T-01", title="Foo", acceptance_ids=["SM-01"]),
        _make_task(id="T-02", title="Bar", acceptance_ids=["SM-02", "OBS-01"]),
    ]
    write_sidecars(iteration.task_sidecar_dir("001"), tasks)
    out = generate_checklist(iteration, "001")
    assert "T-01" in out
    assert "T-02" in out
    assert "- [ ]" in out


def test_checklist_empty(iteration) -> None:
    out = generate_checklist(iteration, "999")
    assert "No sidecars" in out
