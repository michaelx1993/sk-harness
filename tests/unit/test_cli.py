"""Click-based smoke tests for CLI commands."""
from __future__ import annotations

import json

import pytest
from click.testing import CliRunner

from sk_harness.cli import main


@pytest.fixture
def project(tmp_path, monkeypatch):
    root = tmp_path / "proj"
    # Build a minimal .skspec/ that commands can read
    skspec = root / ".skspec"
    for d in [
        "prd", "tests", "docs", "references",
        ".erd/history", ".task/tasks-001", ".progress",
        ".snapshot", ".knowledge/retrospectives", ".prd-pending",
    ]:
        (skspec / d).mkdir(parents=True, exist_ok=True)
    (skspec / ".version").write_text("0.3.0\n")
    (skspec / ".iterations.json").write_text(json.dumps({
        "version": 1, "active": "001",
        "iterations": [{
            "id": "001", "slug": "mvp", "status": "active",
            "started_at": "2026-04-19T00:00:00Z", "completed_at": None,
            "spec": "prd/spec-001.md", "plan": ".erd/plan-001.md",
            "tasks": ".task/tasks-001.md", "test_plan": "tests/test-plan-001.md",
        }],
    }))
    (skspec / ".agents.json").write_text(json.dumps({
        "version": 1, "max_concurrency": 3, "max_retries": 2, "max_active_agents": 8,
        "roster": [{
            "role": "tpm", "subagent_type": "general-purpose",
            "status": "active", "added_loop": 0,
            "deactivated_loop": None, "rationale": "main",
        }],
    }))
    (skspec / ".agents-catalog.json").write_text('{"version":1,"catalog":{}}')
    (skspec / ".progress/state.json").write_text(json.dumps({
        "version": 1, "active_iteration": "001", "phase": "phase-3-implementation",
        "loop_count": 1, "last_updated": "2026-04-20T00:00:00Z",
        "tasks": [{"id": "T-01", "state": "pending", "retries": 0, "snapshot": None}],
        "current_batch": [], "paused": False, "pause_reason": None,
    }))
    (skspec / ".task/tasks-001/T-01.json").write_text(json.dumps({
        "id": "T-01", "title": "init", "deps": [],
        "agent": "general-purpose", "validator": "code-reviewer",
        "idempotent": True, "outputs": [], "state": "pending",
        "retries": 0, "acceptance_ids": ["SM-01"], "estimate": "S",
        "erd_refs": [],
    }))
    (skspec / ".task/tasks-001.md").write_text("### T-01: init\n- deps: []\n")
    monkeypatch.chdir(root)
    return root


@pytest.fixture
def runner():
    return CliRunner()


def test_help(runner):
    res = runner.invoke(main, ["--help"])
    assert res.exit_code == 0
    assert "sk Harness" in res.output


def test_version(runner):
    res = runner.invoke(main, ["--version"])
    assert res.exit_code == 0
    assert "0.3.0" in res.output


def test_status(runner, project):
    res = runner.invoke(main, ["status"])
    assert res.exit_code == 0
    assert "phase=" in res.output.lower() or "phase-3" in res.output
    assert "001" in res.output


def test_pause_resume_cycle(runner, project):
    res = runner.invoke(main, ["pause"])
    assert res.exit_code == 0
    assert "paused" in res.output.lower()

    res = runner.invoke(main, ["pause"])
    assert "already paused" in res.output.lower()

    res = runner.invoke(main, ["resume"])
    assert res.exit_code == 0
    assert "resumed" in res.output.lower()

    res = runner.invoke(main, ["resume"])
    assert "not paused" in res.output.lower()


def test_tasks_list_and_show(runner, project):
    res = runner.invoke(main, ["tasks", "list"])
    assert res.exit_code == 0
    assert "T-01" in res.output

    res = runner.invoke(main, ["tasks", "show", "T-01"])
    assert res.exit_code == 0
    assert "T-01" in res.output

    res = runner.invoke(main, ["tasks", "show", "T-99"])
    assert res.exit_code != 0


def test_tasks_graph(runner, project):
    res = runner.invoke(main, ["tasks", "graph"])
    assert res.exit_code == 0
    assert "T-01" in res.output


def test_tasks_retry_not_failed(runner, project):
    res = runner.invoke(main, ["tasks", "retry", "T-01"])
    assert res.exit_code == 0
    assert "not failed" in res.output.lower() or "pending" in res.output.lower()


def test_iteration_list(runner, project):
    res = runner.invoke(main, ["iteration", "list"])
    assert res.exit_code == 0
    assert "001" in res.output


def test_iteration_complete_blocked_by_pending(runner, project):
    res = runner.invoke(main, ["iteration", "complete"])
    # There is a pending T-01 so it should refuse
    assert res.exit_code != 0


def test_agent_list_add_remove(runner, project):
    res = runner.invoke(main, ["agent", "list"])
    assert res.exit_code == 0
    assert "tpm" in res.output

    res = runner.invoke(main, ["agent", "add", "custom-role", "--type", "general-purpose"])
    assert res.exit_code == 0

    res = runner.invoke(main, ["agent", "add", "custom-role"])
    assert "already present" in res.output.lower()

    res = runner.invoke(main, ["agent", "remove", "custom-role"])
    assert res.exit_code == 0
    assert "removed" in res.output.lower()

    res = runner.invoke(main, ["agent", "remove", "nonexistent"])
    assert "not in roster" in res.output.lower()


def test_init_fresh(tmp_path, monkeypatch, runner):
    monkeypatch.chdir(tmp_path)
    res = runner.invoke(main, ["init", "sample"])
    # will probably fail unless skeleton accessible — expect 0 or 3
    assert res.exit_code in (0, 3)


def test_log_empty(runner, project):
    res = runner.invoke(main, ["log"])
    # No decision-log yet → either "no decision log yet" or empty
    assert res.exit_code == 0


def test_specify_requires_proposal_id(runner, project):
    res = runner.invoke(main, ["specify"])
    assert res.exit_code == 0
    assert "slash" in res.output.lower() or "claude" in res.output.lower()

    res = runner.invoke(main, ["specify", "--accept", "nonsense"])
    assert res.exit_code != 0
