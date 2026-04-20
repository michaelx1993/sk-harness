"""CLI tests for `sk loop` subcommands used by /sk-go SKILL.md."""
from __future__ import annotations

import json

import pytest
from click.testing import CliRunner

from sk_harness.cli import main


@pytest.fixture
def runner():
    return CliRunner()


@pytest.fixture
def project(tmp_path, monkeypatch):
    root = tmp_path / "proj"
    skspec = root / ".skspec"
    for d in [
        "prd", "tests", "docs", "references",
        ".erd/history", ".task/tasks-001", ".progress",
        ".snapshot", ".knowledge/retrospectives", ".prd-pending", ".erd-pending",
    ]:
        (skspec / d).mkdir(parents=True, exist_ok=True)
    (skspec / ".version").write_text("0.3.0\n")
    (skspec / ".iterations.json").write_text(json.dumps({
        "version": 1, "active": "001",
        "iterations": [{
            "id": "001", "slug": "t", "status": "active",
            "started_at": "2026-04-20T00:00:00Z", "completed_at": None,
            "spec": "prd/spec-001.md", "plan": ".erd/plan-001.md",
            "tasks": ".task/tasks-001.md", "test_plan": "tests/test-plan-001.md",
        }],
    }))
    (skspec / ".agents.json").write_text(json.dumps({
        "version": 1, "max_concurrency": 3, "max_retries": 2, "max_active_agents": 8,
        "roster": [{"role": "tpm", "subagent_type": "general-purpose",
                    "status": "active", "added_loop": 0,
                    "deactivated_loop": None, "rationale": "main"}],
    }))
    (skspec / ".agents-catalog.json").write_text('{"version":1,"catalog":{}}')
    (skspec / ".erd/plan-001.md").write_text("# ERD\n")
    (skspec / ".task/tasks-001.md").write_text("### T-01\n### T-02\n")
    for tid, deps in [("T-01", []), ("T-02", ["T-01"]), ("T-03", ["T-01"])]:
        (skspec / f".task/tasks-001/{tid}.json").write_text(json.dumps({
            "id": tid, "title": tid, "deps": deps,
            "agent": "general-purpose", "validator": "code-reviewer",
            "idempotent": True, "outputs": [], "state": "pending",
            "retries": 0, "acceptance_ids": [], "estimate": "S", "erd_refs": [],
        }))
    (skspec / ".progress/state.json").write_text(json.dumps({
        "version": 1, "active_iteration": "001", "phase": "phase-3-implementation",
        "loop_count": 0, "last_updated": "2026-04-20T00:00:00Z",
        "tasks": [
            {"id": "T-01", "state": "pending", "retries": 0, "snapshot": None},
            {"id": "T-02", "state": "pending", "retries": 0, "snapshot": None},
            {"id": "T-03", "state": "pending", "retries": 0, "snapshot": None},
        ],
        "current_batch": [], "paused": False, "pause_reason": None,
    }))
    monkeypatch.chdir(root)
    return root


def test_loop_ready(runner, project):
    res = runner.invoke(main, ["loop", "ready"])
    assert res.exit_code == 0
    assert res.output.strip() == "T-01"  # T-02/T-03 blocked on T-01


def test_loop_begin_batch(runner, project):
    res = runner.invoke(main, ["loop", "begin-batch", "T-01"])
    assert res.exit_code == 0
    state = json.loads((project / ".skspec/.progress/state.json").read_text())
    assert state["current_batch"] == ["T-01"]
    assert any(t["id"] == "T-01" and t["state"] == "running" for t in state["tasks"])


def test_loop_settle_success(runner, project):
    runner.invoke(main, ["loop", "begin-batch", "T-01"])
    res = runner.invoke(main, [
        "loop", "settle", "T-01",
        "--success", "--agent", "general-purpose",
        "--summary", "implemented", "--output", "a.py",
    ])
    assert res.exit_code == 0
    state = json.loads((project / ".skspec/.progress/state.json").read_text())
    t = next(t for t in state["tasks"] if t["id"] == "T-01")
    assert t["state"] == "done"
    assert t["snapshot"]  # snapshot path set


def test_loop_settle_failure_and_retry(runner, project):
    runner.invoke(main, ["loop", "begin-batch", "T-01"])
    # First failure → pending retry
    runner.invoke(main, ["loop", "settle", "T-01", "--failure", "--summary", "f1"])
    state = json.loads((project / ".skspec/.progress/state.json").read_text())
    t = next(t for t in state["tasks"] if t["id"] == "T-01")
    assert t["state"] == "pending"
    assert t["retries"] == 1


def test_loop_reconcile(runner, project):
    # Seed catalog with a keyword-matching entry
    (project / ".skspec/.agents-catalog.json").write_text(
        '{"version":1,"catalog":{"security-reviewer":{"domains":["auth"]}}}'
    )
    # Seed plan with matching keyword
    (project / ".skspec/.erd/plan-001.md").write_text("# ERD\nUse auth tokens.\n")
    res = runner.invoke(main, ["loop", "reconcile"])
    assert res.exit_code == 0
    assert "security-reviewer" in res.output


def test_loop_terminate_continue(runner, project):
    res = runner.invoke(main, ["loop", "terminate"])
    assert res.exit_code == 0
    assert res.output.strip() == "continue"


def test_loop_terminate_retro_when_all_done(runner, project):
    state_path = project / ".skspec/.progress/state.json"
    state = json.loads(state_path.read_text())
    for t in state["tasks"]:
        t["state"] = "done"
    state_path.write_text(json.dumps(state))
    res = runner.invoke(main, ["loop", "terminate"])
    assert res.exit_code == 0
    assert res.output.strip() == "retro"


def test_loop_log(runner, project):
    res = runner.invoke(main, [
        "loop", "log", "test-decision", "one-line body", "--actor", "tpm",
    ])
    assert res.exit_code == 0
    content = (project / ".skspec/.progress/decision-log.md").read_text()
    assert "test-decision" in content
    assert "one-line body" in content
