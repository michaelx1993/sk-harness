"""Unit tests for state models + IO."""
from __future__ import annotations

import pytest

from sk_harness.paths import Paths
from sk_harness.state.io import StateIO, atomic_write, write_model
from sk_harness.state.models import (
    AgentsConfig,
    IterationEntry,
    IterationsRegistry,
    PauseReason,
    Phase,
    ProgressState,
    TaskState,
    TaskStateBrief,
)


def test_progress_state_ready_set() -> None:
    s = ProgressState(
        tasks=[
            TaskStateBrief(id="T-01", state=TaskState.done),
            TaskStateBrief(id="T-02", state=TaskState.pending),
            TaskStateBrief(id="T-03", state=TaskState.pending),
        ]
    )
    dag = {"T-01": [], "T-02": ["T-01"], "T-03": ["T-02"]}
    assert s.ready_set(dag) == ["T-02"]


def test_iterations_registry_active() -> None:
    reg = IterationsRegistry(
        active="001",
        iterations=[
            IterationEntry(
                id="001", slug="mvp", status="active",
                spec="prd/spec-001.md", plan=".erd/plan-001.md",
                tasks=".task/tasks-001.md", test_plan="tests/test-plan-001.md",
            ),
        ],
    )
    assert reg.get_active() is not None
    assert reg.get_active().id == "001"


def test_atomic_write_and_roundtrip(tmp_path) -> None:
    p = tmp_path / "subdir" / "file.json"
    atomic_write(p, '{"a":1}\n')
    assert p.read_text() == '{"a":1}\n'

    cfg = AgentsConfig(max_concurrency=5)
    write_model(p, cfg)
    loaded = AgentsConfig.model_validate_json(p.read_text())
    assert loaded.max_concurrency == 5


def test_stateio_lock(tmp_path) -> None:
    skspec = tmp_path / ".skspec"
    (skspec / ".progress").mkdir(parents=True)
    skspec.joinpath(".version").write_text("0.3.0\n")
    paths = Paths(tmp_path)
    io = StateIO(paths, lock_timeout=1.0)
    state = ProgressState(phase=Phase.init)
    with io.lock():
        io.save_state(state)
    loaded = io.load_state()
    assert loaded.phase == Phase.init


def test_pause_reason_enum() -> None:
    assert PauseReason("user") == PauseReason.user
    assert PauseReason("deadlock") == PauseReason.deadlock
    with pytest.raises(ValueError):
        PauseReason("nonsense")
