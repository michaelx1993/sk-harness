"""CLI tests for iter-002 new subcommands."""
from __future__ import annotations

import json
from pathlib import Path

import pytest
from click.testing import CliRunner

from sk_harness.cli import main


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
            "id": "001", "slug": "mvp", "status": "active",
            "started_at": "2026-04-19T00:00:00Z", "completed_at": None,
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
    (skspec / ".constitution.md").write_text("# Constitution\nPlaceholder.\n")
    (skspec / ".progress/state.json").write_text(json.dumps({
        "version": 1, "active_iteration": "001", "phase": "phase-3-implementation",
        "loop_count": 0, "last_updated": "2026-04-20T00:00:00Z",
        "tasks": [{"id": "T-01", "state": "pending", "retries": 0, "snapshot": None}],
        "current_batch": [], "paused": False, "pause_reason": None,
    }))
    (skspec / ".erd/plan-001.md").write_text(
        "# ERD\n\n## 1. Intro\n\n## 2. Components\n"
    )
    (skspec / ".task/tasks-001.md").write_text("### T-01\n- deps: []\n")
    (skspec / ".task/tasks-001/T-01.json").write_text(json.dumps({
        "id": "T-01", "title": "init", "deps": [],
        "agent": "general-purpose", "validator": "code-reviewer",
        "idempotent": True, "outputs": [], "state": "pending",
        "retries": 0, "acceptance_ids": ["SM-01"], "estimate": "S",
        "erd_refs": ["§1"],
    }))
    (skspec / "tests/test-plan-001.md").write_text(
        "# Test Plan\n| ID | Scenario |\n|---|---|\n| SM-01 | smoke |\n"
    )
    monkeypatch.chdir(root)
    return root


@pytest.fixture
def runner():
    return CliRunner()


def test_config_show(runner, project):
    res = runner.invoke(main, ["config", "show"])
    assert res.exit_code == 0
    assert "max_concurrency" in res.output
    assert "max_retries" in res.output
    assert "max_active_agents" in res.output


def test_config_set_valid_key(runner, project):
    res = runner.invoke(main, ["config", "set", "max_concurrency", "5"])
    assert res.exit_code == 0
    state_file = project / ".skspec/.agents.json"
    data = json.loads(state_file.read_text())
    assert data["max_concurrency"] == 5


def test_config_set_invalid_key(runner, project):
    res = runner.invoke(main, ["config", "set", "bogus_key", "1"])
    assert res.exit_code != 0
    assert "unknown" in res.output.lower()


def test_config_set_invalid_value(runner, project):
    res = runner.invoke(main, ["config", "set", "max_concurrency", "0"])
    assert res.exit_code != 0


def test_step(runner, project):
    res = runner.invoke(main, ["step"])
    assert res.exit_code == 0
    state = json.loads((project / ".skspec/.progress/state.json").read_text())
    assert state["pause_reason"] == "step"


def test_review(runner, project):
    res = runner.invoke(main, ["review"])
    assert res.exit_code == 0
    state = json.loads((project / ".skspec/.progress/state.json").read_text())
    assert state["paused"] is True
    assert state["pause_reason"] == "review_requested"


def test_erd_pending_list_empty(runner, project):
    res = runner.invoke(main, ["erd-pending", "list"])
    assert res.exit_code == 0
    assert "none pending" in res.output.lower()


def test_erd_pending_accept_nonexistent(runner, project):
    res = runner.invoke(main, ["erd-pending", "accept", "bogus"])
    assert res.exit_code != 0


def test_analyze_passes_on_clean_iteration(runner, project):
    res = runner.invoke(main, ["analyze"])
    assert res.exit_code == 0
    assert "all checks passed" in res.output or "passed" in res.output


def test_analyze_fails_on_missing_section(runner, project):
    sidecar = project / ".skspec/.task/tasks-001/T-01.json"
    data = json.loads(sidecar.read_text())
    data["erd_refs"] = ["§99"]
    sidecar.write_text(json.dumps(data))
    res = runner.invoke(main, ["analyze"])
    assert res.exit_code == 1
    assert "§99" in res.output


def test_checklist(runner, project):
    res = runner.invoke(main, ["checklist"])
    assert res.exit_code == 0
    assert "T-01" in res.output
    assert "- [ ]" in res.output


def test_constitution(runner, project):
    res = runner.invoke(main, ["constitution"])
    assert res.exit_code == 0
    assert ".constitution.md" in res.output

    res = runner.invoke(main, ["constitution", "--show"])
    assert res.exit_code == 0
    assert "Constitution" in res.output
