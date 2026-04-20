"""Proposal channels: `.prd-pending/` (user-confirm) and `.erd-pending/` (agent-autonomous).

Per Constitution §VII:
- PRD changes require user acceptance via `/sk-specify --accept|--reject`
- ERD changes are agent-autonomous; proposals in `.erd-pending/` are auto-accepted
  by TPM with snapshot-first reversibility (Constitution §III)
"""

from __future__ import annotations

import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal

from sk_harness.paths import Paths

_FRONTMATTER = re.compile(r"^---\s*\n(?P<fm>.*?)\n---\s*\n(?P<body>.*)$", re.DOTALL)

Channel = Literal["prd", "erd"]


def _now_id() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _channel_dir(paths: Paths, channel: Channel) -> Path:
    return paths.prd_pending_dir if channel == "prd" else paths.erd_pending_dir


def _write_proposal(
    paths: Paths, channel: Channel, *, title: str, problem: str, evidence: str,
    suggested_change: str, impact: str, filed_by_task: str | None,
) -> Path:
    pid = _now_id()
    content = (
        f"---\n"
        f"proposal_id: {pid}\n"
        f"channel: {channel}\n"
        f"filed_by_task: {filed_by_task or ''}\n"
        f"filed_at: {_now_iso()}\n"
        f"status: pending\n"
        f"---\n\n"
        f"# {title}\n\n"
        f"## Problem\n{problem}\n\n"
        f"## Evidence\n{evidence}\n\n"
        f"## Suggested Change\n{suggested_change}\n\n"
        f"## Impact\n{impact}\n"
    )
    out_dir = _channel_dir(paths, channel)
    out_dir.mkdir(parents=True, exist_ok=True)
    out = out_dir / f"proposal-{pid}.md"
    out.write_text(content, encoding="utf-8")
    return out


def file_proposal(
    paths: Paths, *, title: str, problem: str, evidence: str,
    suggested_change: str, impact: str, filed_by_task: str | None = None,
) -> Path:
    """File a PRD-channel proposal (requires user accept/reject)."""
    return _write_proposal(
        paths, "prd", title=title, problem=problem, evidence=evidence,
        suggested_change=suggested_change, impact=impact, filed_by_task=filed_by_task,
    )


def file_erd_proposal(
    paths: Paths, *, title: str, problem: str, evidence: str,
    suggested_change: str, impact: str, filed_by_task: str | None = None,
) -> Path:
    """File an ERD-channel proposal (TPM may auto-accept with snapshot)."""
    return _write_proposal(
        paths, "erd", title=title, problem=problem, evidence=evidence,
        suggested_change=suggested_change, impact=impact, filed_by_task=filed_by_task,
    )


def _list_channel(paths: Paths, channel: Channel) -> list[Path]:
    d = _channel_dir(paths, channel)
    if not d.exists():
        return []
    return sorted(d.glob("proposal-*.md"))


def list_pending(paths: Paths) -> list[Path]:
    return _list_channel(paths, "prd")


def list_erd_pending(paths: Paths) -> list[Path]:
    return _list_channel(paths, "erd")


def _extract_change(proposal_path: Path) -> str:
    raw = proposal_path.read_text(encoding="utf-8")
    m = re.search(r"## Suggested Change\s*\n(.*?)(?=\n## |\Z)", raw, re.DOTALL)
    return m.group(1).strip() if m else raw


def accept_proposal(paths: Paths, proposal_path: Path, iteration: str) -> Path:
    """Append proposal's Suggested Change to spec-NNN.md as an addendum."""
    change = _extract_change(proposal_path)
    spec = paths.spec(iteration)
    existing = spec.read_text(encoding="utf-8") if spec.exists() else ""
    addendum = (
        f"\n\n---\n\n"
        f"## Addendum from proposal {proposal_path.stem} "
        f"({datetime.now(timezone.utc).strftime('%Y-%m-%d')})\n\n"
        f"{change}\n"
    )
    spec.write_text(existing + addendum, encoding="utf-8")
    archived = proposal_path.with_name(f"accepted-{proposal_path.name}")
    proposal_path.rename(archived)
    return spec


def reject_proposal(paths: Paths, proposal_path: Path) -> Path:
    archived = proposal_path.with_name(f"rejected-{proposal_path.name}")
    proposal_path.rename(archived)
    return archived


def accept_erd_proposal(paths: Paths, proposal_path: Path, iteration: str) -> Path:
    """Snapshot current plan, append proposal's Suggested Change, archive proposal.

    Constitution §III: reversibility. The snapshot happens FIRST.
    """
    plan = paths.plan(iteration)
    if plan.exists():
        paths.erd_history_dir.mkdir(parents=True, exist_ok=True)
        ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        snap = paths.erd_history_dir / f"plan-{iteration}-{ts}-before-erd-proposal.md"
        snap.write_text(plan.read_text(encoding="utf-8"), encoding="utf-8")

    change = _extract_change(proposal_path)
    existing = plan.read_text(encoding="utf-8") if plan.exists() else f"# ERD — Iteration {iteration}\n"
    addendum = (
        f"\n\n---\n\n"
        f"## Addendum from ERD proposal {proposal_path.stem} "
        f"({datetime.now(timezone.utc).strftime('%Y-%m-%d')})\n\n"
        f"{change}\n"
    )
    plan.write_text(existing + addendum, encoding="utf-8")
    archived = proposal_path.with_name(f"accepted-{proposal_path.name}")
    proposal_path.rename(archived)
    return plan


def reject_erd_proposal(paths: Paths, proposal_path: Path) -> Path:
    archived = proposal_path.with_name(f"rejected-{proposal_path.name}")
    proposal_path.rename(archived)
    return archived
