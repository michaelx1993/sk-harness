"""Unit tests for DAG parser and graph."""
from __future__ import annotations

import pytest

from sk_harness.dag.graph import TaskGraph
from sk_harness.dag.parser import parse_tasks_markdown, render_tasks_markdown
from sk_harness.state.models import TaskMeta, TaskState


def test_parse_basic_task_list() -> None:
    md = """
## Wave 1: bootstrap

### T-01: Fork speckit
- deps: []
- agent: general-purpose
- validator: code-reviewer
- idempotent: true
- outputs: [LICENSE, docs/UPSTREAM.md]
- acceptance: SM-01, OBS-01
- estimate: M

Description here.

### T-02: Scaffold package
- deps: [T-01]
- agent: general-purpose
- validator: python-reviewer
- idempotent: true
- outputs: [pyproject.toml]
- acceptance: SM-01
- estimate: S
"""
    tasks = parse_tasks_markdown(md)
    assert len(tasks) == 2
    assert tasks[0].id == "T-01"
    assert tasks[0].outputs == ["LICENSE", "docs/UPSTREAM.md"]
    assert tasks[1].deps == ["T-01"]
    assert tasks[0].idempotent is True
    assert tasks[1].estimate == "S"


def test_graph_cycle_detection() -> None:
    a = TaskMeta(id="T-01", deps=["T-02"])
    b = TaskMeta(id="T-02", deps=["T-01"])
    with pytest.raises(ValueError, match="Cycle"):
        TaskGraph([a, b])


def test_ready_set() -> None:
    a = TaskMeta(id="T-01")
    b = TaskMeta(id="T-02", deps=["T-01"])
    c = TaskMeta(id="T-03", deps=["T-01"])
    d = TaskMeta(id="T-04", deps=["T-02", "T-03"])
    g = TaskGraph([a, b, c, d])
    assert g.ready_set({"T-01": TaskState.pending, "T-02": TaskState.pending,
                         "T-03": TaskState.pending, "T-04": TaskState.pending}) == ["T-01"]
    assert sorted(g.ready_set({"T-01": TaskState.done, "T-02": TaskState.pending,
                                "T-03": TaskState.pending, "T-04": TaskState.pending})) == ["T-02", "T-03"]
    assert g.ready_set({"T-01": TaskState.done, "T-02": TaskState.done,
                         "T-03": TaskState.done, "T-04": TaskState.pending}) == ["T-04"]
    assert g.ready_set({"T-01": TaskState.done, "T-02": TaskState.done,
                         "T-03": TaskState.done, "T-04": TaskState.done}) == []


def test_render_roundtrip() -> None:
    original = TaskMeta(
        id="T-99", title="Test task",
        deps=["T-01"], agent="general-purpose",
        validator="tdd-guide", idempotent=True,
        outputs=["a.py", "b.py"],
        acceptance_ids=["SM-42"], estimate="L",
    )
    md = render_tasks_markdown([original])
    parsed = parse_tasks_markdown(md)
    assert len(parsed) == 1
    assert parsed[0].id == "T-99"
    assert parsed[0].deps == ["T-01"]
    assert parsed[0].estimate == "L"
