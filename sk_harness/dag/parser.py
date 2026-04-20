"""Markdown ↔ JSON sidecar parser for `.task/tasks-NNN.md`.

Grammar (mirrors what engineer-subagent produces):

    ## Wave N: <name>

    ### T-NN: <title>
    - deps: [T-XX, T-YY]
    - agent: <subagent_type>
    - validator: <subagent_type|manual>
    - idempotent: true|false
    - outputs: [path1, path2]
    - acceptance: SM-XX, OBS-YY
    - estimate: S|M|L

    Description paragraph(s).
"""

from __future__ import annotations

import re
from pathlib import Path

from sk_harness.state.models import TaskMeta, TaskState

_TASK_HDR = re.compile(r"^###\s+(T-\d+):\s*(.+?)\s*$")
_FIELD = re.compile(r"^\s*-\s+([a-z_]+)\s*:\s*(.+?)\s*$", re.IGNORECASE)
_LIST_VAL = re.compile(r"^\[(.*)\]$")


def _parse_list(raw: str) -> list[str]:
    raw = raw.strip()
    m = _LIST_VAL.match(raw)
    inner = m.group(1) if m else raw
    if not inner.strip():
        return []
    parts = [p.strip().strip('"').strip("'") for p in inner.split(",")]
    return [p for p in parts if p]


def _parse_field(name: str, value: str) -> object:
    name = name.lower()
    v = value.strip()
    if name in {"deps", "outputs", "acceptance", "acceptance_ids", "erd_refs"}:
        return _parse_list(v)
    if name == "idempotent":
        return v.lower() in {"true", "yes", "1"}
    if name == "estimate":
        return v.upper() if v.upper() in {"S", "M", "L"} else "M"
    return v.strip().strip('"').strip("'")


_FIELD_ALIASES = {"acceptance": "acceptance_ids"}


def parse_tasks_markdown(text: str) -> list[TaskMeta]:
    """Parse a tasks-NNN.md file into a list of TaskMeta."""
    tasks: list[TaskMeta] = []
    cur: dict[str, object] | None = None
    desc_lines: list[str] = []

    def flush() -> None:
        nonlocal cur, desc_lines
        if cur is None:
            return
        if desc_lines:
            cur["title"] = cur.get("title", "")
        cur.setdefault("state", TaskState.pending)
        cur.setdefault("retries", 0)
        tasks.append(TaskMeta(**cur))
        cur = None
        desc_lines = []

    for line in text.splitlines():
        m = _TASK_HDR.match(line)
        if m:
            flush()
            cur = {"id": m.group(1), "title": m.group(2), "deps": [], "outputs": []}
            desc_lines = []
            continue
        if cur is None:
            continue
        fm = _FIELD.match(line)
        if fm:
            name = fm.group(1).lower()
            name = _FIELD_ALIASES.get(name, name)
            cur[name] = _parse_field(name, fm.group(2))
            continue
        if line.strip():
            desc_lines.append(line)
    flush()
    return tasks


def render_tasks_markdown(tasks: list[TaskMeta], header: str = "") -> str:
    lines = [header.rstrip(), ""] if header else []
    for t in tasks:
        lines.append(f"### {t.id}: {t.title}")
        lines.append(f"- deps: [{', '.join(t.deps)}]")
        lines.append(f"- agent: {t.agent}")
        lines.append(f"- validator: {t.validator}")
        lines.append(f"- idempotent: {'true' if t.idempotent else 'false'}")
        lines.append(f"- outputs: [{', '.join(t.outputs)}]")
        lines.append(f"- acceptance: {', '.join(t.acceptance_ids)}")
        lines.append(f"- estimate: {t.estimate}")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def write_sidecars(sidecar_dir: Path, tasks: list[TaskMeta]) -> int:
    sidecar_dir.mkdir(parents=True, exist_ok=True)
    n = 0
    for t in tasks:
        path = sidecar_dir / f"{t.id}.json"
        path.write_text(t.model_dump_json(indent=2) + "\n", encoding="utf-8")
        n += 1
    return n


def read_sidecars(sidecar_dir: Path) -> list[TaskMeta]:
    out: list[TaskMeta] = []
    for p in sorted(sidecar_dir.glob("T-*.json")):
        out.append(TaskMeta.model_validate_json(p.read_text(encoding="utf-8")))
    return out
