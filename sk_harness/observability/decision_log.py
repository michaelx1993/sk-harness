"""Append-only decision log writer."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path


def _now() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


class DecisionLog:
    def __init__(self, path: Path) -> None:
        self.path = path

    def append(
        self,
        *,
        iteration: str,
        loop: int,
        actor: str,
        decision: str,
        body: str,
        timestamp: str | None = None,
    ) -> None:
        ts = timestamp or _now()
        entry = (
            f"\n---\n\n"
            f"## {ts} · iter={iteration} · loop={loop} · actor={actor} · decision={decision}\n\n"
            f"{body.strip()}\n"
        )
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as f:
            f.write(entry)


def append_decision(
    path: Path,
    *,
    iteration: str,
    loop: int,
    actor: str,
    decision: str,
    body: str,
    timestamp: str | None = None,
) -> None:
    DecisionLog(path).append(
        iteration=iteration,
        loop=loop,
        actor=actor,
        decision=decision,
        body=body,
        timestamp=timestamp,
    )
