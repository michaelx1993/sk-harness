"""Task execution snapshots for `.snapshot/iter-NNN/`."""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from sk_harness.paths import Paths

SOFT_CAP_BYTES = 256 * 1024


def _now() -> str:
    return datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")


def write_snapshot(
    paths: Paths,
    iteration: str,
    task_id: str,
    *,
    agent: str,
    summary: str,
    outputs: list[str],
    extras: dict[str, Any] | None = None,
) -> Path:
    ts = _now()
    target_dir = paths.iter_snapshot_dir(iteration)
    target_dir.mkdir(parents=True, exist_ok=True)
    target = target_dir / f"{task_id}-{ts}.json"

    output_digests: list[dict[str, Any]] = []
    total_bytes = 0
    for rel in outputs:
        fp = paths.root / rel
        digest = {"path": rel, "exists": fp.exists()}
        if fp.is_file():
            data = fp.read_bytes()
            total_bytes += len(data)
            digest["size"] = len(data)
            digest["sha256"] = hashlib.sha256(data).hexdigest()
            if total_bytes <= SOFT_CAP_BYTES:
                try:
                    digest["preview"] = data[:2048].decode("utf-8", errors="replace")
                except Exception:
                    digest["preview"] = None
        output_digests.append(digest)

    payload = {
        "task_id": task_id,
        "iteration": iteration,
        "agent": agent,
        "timestamp": ts,
        "summary": summary,
        "outputs": output_digests,
        "truncated": total_bytes > SOFT_CAP_BYTES,
    }
    if extras:
        payload["extras"] = extras

    target.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return target


def load_snapshot(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def list_snapshots(paths: Paths, iteration: str, task_id: str | None = None) -> list[Path]:
    d = paths.iter_snapshot_dir(iteration)
    if not d.exists():
        return []
    pat = f"{task_id}-*.json" if task_id else "*.json"
    return sorted(d.glob(pat))
