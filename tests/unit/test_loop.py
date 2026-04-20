"""Unit tests for loop orchestration."""
from __future__ import annotations

import pytest

from sk_harness.dag.parser import write_sidecars
from sk_harness.loop import (
    begin_batch,
    check_termination,
    compute_ready,
    load_dag,
    roster_reconcile,
    settle_task,
)
from sk_harness.paths import Paths
from sk_harness.state.io import StateIO
from sk_harness.state.models import (
    AgentsConfig,
    IterationEntry,
    IterationsRegistry,
    PauseReason,
    Phase,
    ProgressState,
    TaskMeta,
    TaskState,
    TaskStateBrief,
)


@pytest.fixture
def project(tmp_path):
    root = tmp_path / "proj"
    skspec = root / ".skspec"
    for d in [
        "prd", "tests", "docs", "references",
        ".erd/history", ".task/tasks-001", ".progress",
        ".snapshot", ".knowledge/retrospectives", ".prd-pending",
    ]:
        (skspec / d).mkdir(parents=True, exist_ok=True)
    (skspec / ".version").write_text("0.3.0\n")
    paths = Paths(root)
    io = StateIO(paths, lock_timeout=2.0)

    # seed iterations
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
    io.save_iterations(reg)

    # seed agents + catalog
    io.save_agents(AgentsConfig(max_concurrency=3, max_retries=2))
    paths.agents_catalog.write_text(
        '{"version":1,"catalog":{"security-reviewer":{"domains":["auth","crypto"]}}}'
    )

    # seed tasks DAG: T-01 → T-02, T-03 → T-04
    tasks = [
        TaskMeta(id="T-01", title="init", deps=[]),
        TaskMeta(id="T-02", title="build", deps=["T-01"]),
        TaskMeta(id="T-03", title="lint", deps=["T-01"]),
        TaskMeta(id="T-04", title="publish", deps=["T-02", "T-03"]),
    ]
    write_sidecars(paths.task_sidecar_dir("001"), tasks)
    paths.tasks("001").write_text(
        "# Tasks\n\n### T-01: init\n- deps: []\n\n### T-02: build\n- deps: [T-01]\n\n"
        "### T-03: lint\n- deps: [T-01]\n\n### T-04: publish\n- deps: [T-02, T-03]\n"
    )
    paths.plan("001").write_text("# ERD\n\nNo keywords that would trigger roster reconciliation.\n")

    # seed progress
    state = ProgressState(
        active_iteration="001",
        phase=Phase.phase_3_implementation,
        tasks=[TaskStateBrief(id=t.id) for t in tasks],
    )
    io.save_state(state)

    return paths, io


def test_load_dag(project) -> None:
    paths, io = project
    graph, meta = load_dag(paths, "001")
    assert len(meta) == 4
    assert graph.depth() == 2


def test_compute_ready(project) -> None:
    paths, io = project
    state = io.load_state()
    graph, _ = load_dag(paths, "001")
    assert compute_ready(state, graph) == ["T-01"]


def test_begin_batch_and_settle(project) -> None:
    paths, io = project
    state = io.load_state()
    state = begin_batch(io, state, ["T-01"], loop=1)
    assert state.current_batch == ["T-01"]
    assert state.task("T-01").state == TaskState.running

    settle_task(
        io, paths, "001", "T-01",
        success=True, agent="general-purpose",
        summary="done", outputs=[".skspec/.version"],
    )
    state = io.load_state()
    assert state.task("T-01").state == TaskState.done
    assert state.task("T-01").snapshot is not None
    assert "T-01" not in state.current_batch


def test_settle_retry_logic(project) -> None:
    paths, io = project
    state = io.load_state()
    state = begin_batch(io, state, ["T-01"], loop=1)
    # max_retries=2; first failure → pending retry
    settle_task(io, paths, "001", "T-01", success=False, agent="x", summary="f", outputs=[])
    state = io.load_state()
    assert state.task("T-01").state == TaskState.pending
    assert state.task("T-01").retries == 1

    # second failure → pending again
    settle_task(io, paths, "001", "T-01", success=False, agent="x", summary="f", outputs=[])
    state = io.load_state()
    assert state.task("T-01").retries == 2

    # third failure → failed
    settle_task(io, paths, "001", "T-01", success=False, agent="x", summary="f", outputs=[])
    state = io.load_state()
    assert state.task("T-01").state == TaskState.failed


def test_check_termination_retro(project) -> None:
    paths, io = project
    state = io.load_state()
    for t in state.tasks:
        t.state = TaskState.done
    io.save_state(state)
    state = io.load_state()
    graph, _ = load_dag(paths, "001")
    decision, reason = check_termination(state, graph, consecutive_empty_ready=0)
    assert decision == "retro"
    assert reason is None


def test_check_termination_failed(project) -> None:
    paths, io = project
    state = io.load_state()
    state.tasks[0].state = TaskState.failed
    io.save_state(state)
    state = io.load_state()
    graph, _ = load_dag(paths, "001")
    decision, reason = check_termination(state, graph, consecutive_empty_ready=0)
    assert decision == "pause"
    assert reason == PauseReason.max_retries_exceeded


def test_check_termination_deadlock(project) -> None:
    paths, io = project
    state = io.load_state()
    # T-02 depends on T-01; both pending → ready_set = [T-01], but mark T-01 running to simulate
    # a deadlock we need empty ready AND no running — so mark all but one as blocked
    state.tasks[0].state = TaskState.blocked
    state.tasks[1].state = TaskState.pending
    state.tasks[2].state = TaskState.pending
    state.tasks[3].state = TaskState.pending
    io.save_state(state)
    state = io.load_state()
    graph, _ = load_dag(paths, "001")
    decision, reason = check_termination(state, graph, consecutive_empty_ready=2)
    assert decision == "pause"
    assert reason == PauseReason.deadlock


def test_roster_reconcile_adds_from_keyword(project) -> None:
    paths, io = project
    # Inject a keyword into the plan that should trigger security-reviewer
    paths.plan("001").write_text("# ERD\n\nAuth flow with JWT tokens.\n")
    added, deactivated = roster_reconcile(io, paths, "001", loop=1)
    assert "security-reviewer" in added
    cfg = io.load_agents()
    sec = next(a for a in cfg.roster if a.role == "security-reviewer")
    assert sec.status == "active"
