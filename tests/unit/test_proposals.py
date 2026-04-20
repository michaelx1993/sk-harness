"""Tests for proposals module (.prd-pending and .erd-pending channels)."""
from __future__ import annotations

import pytest

from sk_harness.paths import Paths
from sk_harness.proposals import (
    accept_erd_proposal,
    accept_proposal,
    file_erd_proposal,
    file_proposal,
    list_erd_pending,
    list_pending,
    reject_erd_proposal,
    reject_proposal,
)


@pytest.fixture
def skspec(tmp_path):
    root = tmp_path / "proj"
    for d in [
        ".skspec/prd",
        ".skspec/.erd/history",
        ".skspec/.prd-pending",
        ".skspec/.erd-pending",
    ]:
        (root / d).mkdir(parents=True, exist_ok=True)
    (root / ".skspec/.version").write_text("0.3.0\n")
    return Paths(root)


def test_file_prd_proposal(skspec) -> None:
    p = file_proposal(
        skspec, title="Fix gap", problem="X", evidence="Y",
        suggested_change="Z", impact="W", filed_by_task="T-01",
    )
    assert p.exists()
    assert "channel: prd" in p.read_text()
    assert p in list_pending(skspec)


def test_file_erd_proposal(skspec) -> None:
    p = file_erd_proposal(
        skspec, title="ERD gap", problem="X", evidence="Y",
        suggested_change="Z", impact="W",
    )
    assert p.exists()
    assert "channel: erd" in p.read_text()
    assert p in list_erd_pending(skspec)
    # Not listed in PRD channel
    assert p not in list_pending(skspec)


def test_accept_erd_proposal_snapshots_plan(skspec) -> None:
    plan = skspec.plan("001")
    plan.write_text("# ERD v0.1\n\nOriginal content.\n")
    p = file_erd_proposal(
        skspec, title="Adopt foo", problem="X", evidence="Y",
        suggested_change="Change §4 to baz", impact="T-09..T-12",
    )
    updated = accept_erd_proposal(skspec, p, "001")
    # plan now has addendum
    text = updated.read_text()
    assert "Addendum from ERD proposal" in text
    assert "Change §4 to baz" in text
    # snapshot saved in history
    snaps = list(skspec.erd_history_dir.glob("plan-001-*-before-erd-proposal.md"))
    assert len(snaps) == 1
    assert "Original content." in snaps[0].read_text()
    # proposal archived
    assert not p.exists()
    assert list_erd_pending(skspec) == []


def test_reject_erd_proposal(skspec) -> None:
    p = file_erd_proposal(
        skspec, title="Rejected", problem="X", evidence="Y",
        suggested_change="Z", impact="W",
    )
    archived = reject_erd_proposal(skspec, p)
    assert archived.name.startswith("rejected-")
    assert not p.exists()


def test_accept_erd_proposal_no_prior_plan(skspec) -> None:
    """If plan-NNN.md doesn't exist yet, accept creates it fresh."""
    p = file_erd_proposal(
        skspec, title="Bootstrap plan", problem="X", evidence="Y",
        suggested_change="Initial draft", impact="W",
    )
    out = accept_erd_proposal(skspec, p, "042")
    assert out.exists()
    assert "Addendum from ERD proposal" in out.read_text()
