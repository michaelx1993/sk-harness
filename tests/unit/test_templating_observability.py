"""Unit tests for templating, observability.decision_log, paths, prd_merge, snapshots, headless."""
from __future__ import annotations

import pytest

from sk_harness.headless import (
    EXIT_DEADLOCK,
    EXIT_MAX_RETRIES,
    EXIT_PRD_PROPOSAL,
    pause_reason_to_exit,
)
from sk_harness.observability.decision_log import DecisionLog, append_decision
from sk_harness.paths import Paths
from sk_harness.prd_merge import accept_proposal, file_proposal, list_pending, reject_proposal
from sk_harness.snapshots import list_snapshots, load_snapshot, write_snapshot
from sk_harness.state.models import PauseReason
from sk_harness.templating import render, render_file, render_to


@pytest.fixture
def skspec(tmp_path):
    root = tmp_path / "proj"
    for d in [
        ".skspec/prd",
        ".skspec/.erd/history",
        ".skspec/.progress",
        ".skspec/.snapshot",
        ".skspec/.prd-pending",
        ".skspec/.task",
    ]:
        (root / d).mkdir(parents=True, exist_ok=True)
    (root / ".skspec/.version").write_text("0.3.0\n")
    return Paths(root)


def test_render_variable_substitution() -> None:
    assert render("hello {{name}}", {"name": "sk"}) == "hello sk"
    # missing variable stays literal
    assert render("hello {{missing}}", {}) == "hello {{missing}}"
    # multiple vars
    assert render("{{a}} + {{b}} = {{c}}", {"a": "1", "b": "2", "c": "3"}) == "1 + 2 = 3"


def test_render_file_and_to(tmp_path) -> None:
    src = tmp_path / "template.md"
    src.write_text("Iteration {{iter_id}} for {{name}}.")
    assert render_file(src, {"iter_id": "001", "name": "alpha"}) == "Iteration 001 for alpha."
    dest = tmp_path / "out" / "rendered.md"
    render_to(src, dest, {"iter_id": "002", "name": "beta"})
    assert dest.read_text() == "Iteration 002 for beta."


def test_decision_log_append(tmp_path) -> None:
    log = DecisionLog(tmp_path / "log.md")
    log.append(iteration="001", loop=1, actor="tpm", decision="test", body="Body here.")
    content = (tmp_path / "log.md").read_text()
    assert "iter=001" in content
    assert "loop=1" in content
    assert "actor=tpm" in content
    assert "decision=test" in content
    assert "Body here." in content


def test_append_decision_free_function(tmp_path) -> None:
    path = tmp_path / "d.md"
    append_decision(path, iteration="002", loop=5, actor="user", decision="pause", body="Stopped.")
    assert "iter=002" in path.read_text()


def test_paths_find_walks_up(tmp_path) -> None:
    root = tmp_path / "a" / "b"
    (root / ".skspec" / ".progress").mkdir(parents=True)
    (root / ".skspec" / ".version").write_text("0.3.0\n")
    deep = root / "sub" / "deeper"
    deep.mkdir(parents=True)
    p = Paths.find(deep)
    assert p.root == root.resolve()
    assert p.spec("001").name == "spec-001.md"


def test_paths_find_raises(tmp_path) -> None:
    with pytest.raises(FileNotFoundError):
        Paths.find(tmp_path)


def test_prd_proposal_flow(skspec) -> None:
    spec = skspec.prd_dir / "spec-001.md"
    spec.write_text("# PRD\n\nOriginal content.\n")
    p = file_proposal(
        skspec,
        title="Gap",
        problem="Something missing",
        evidence="file.py:42",
        suggested_change="Add section X",
        impact="T-07, T-08",
        filed_by_task="T-05",
    )
    assert p.exists()
    assert p in list_pending(skspec)
    assert "proposal_id:" in p.read_text()

    updated = accept_proposal(skspec, p, "001")
    assert "Addendum" in updated.read_text()
    assert "Add section X" in updated.read_text()
    assert not p.exists()
    assert not list_pending(skspec)

    # Test reject
    p2 = file_proposal(
        skspec, title="Reject me", problem="X", evidence="Y",
        suggested_change="Z", impact="W",
    )
    archived = reject_proposal(skspec, p2)
    assert archived.name.startswith("rejected-")
    assert not list_pending(skspec)


def test_snapshot_write_and_load(skspec) -> None:
    (skspec.root / "output.txt").write_text("hello")
    snap = write_snapshot(
        skspec, "001", "T-42",
        agent="general-purpose",
        summary="smoke",
        outputs=["output.txt"],
    )
    assert snap.exists()
    data = load_snapshot(snap)
    assert data["task_id"] == "T-42"
    assert data["outputs"][0]["sha256"]
    snaps = list_snapshots(skspec, "001")
    assert snap in snaps
    task_snaps = list_snapshots(skspec, "001", "T-42")
    assert snap in task_snaps
    assert list_snapshots(skspec, "999") == []


def test_headless_exit_mapping() -> None:
    assert pause_reason_to_exit(None) == 0
    assert pause_reason_to_exit(PauseReason.user) == 0
    assert pause_reason_to_exit(PauseReason.max_retries_exceeded) == EXIT_MAX_RETRIES
    assert pause_reason_to_exit(PauseReason.deadlock) == EXIT_DEADLOCK
    assert pause_reason_to_exit(PauseReason.prd_proposal) == EXIT_PRD_PROPOSAL
