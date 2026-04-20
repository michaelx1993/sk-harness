"""Single concentration point for upstream-spec-kit ↔ sk Harness translation.

Per Constitution §VI and ERD §1.3 (v0.2): the only place upstream paths,
command names, or skill frontmatter shapes are referenced.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

UPSTREAM_PKG = "speckit/specify_cli"
UPSTREAM_TEMPLATES = "templates/upstream"
HARNESS_TEMPLATES = "templates/harness"
HARNESS_SKILL_DIR = ".claude/skills"

_FRONTMATTER = re.compile(r"^---\s*\n(?P<body>.*?)\n---\s*\n(?P<rest>.*)$", re.DOTALL)


@dataclass(frozen=True)
class CommandRename:
    """Logical name (dotted, internal) ↔ skill dir + invocation (hyphenated, user-facing)."""

    internal: str          # e.g. "sk.specify"
    skill_dir: str         # e.g. "sk-specify"
    invocation: str        # e.g. "/sk-specify"

    @classmethod
    def of(cls, internal: str) -> CommandRename:
        stem = internal.replace(".", "-")
        return cls(internal=internal, skill_dir=stem, invocation=f"/{stem}")


def resolve_upstream_command(internal: str) -> Path | None:
    """Return path to upstream Claude skill body if `internal` is an inherited speckit command.

    Examples
    --------
    sk.specify         → templates/upstream/specify.md  (or rendered skill, see ERD §4.4)
    sk.harness.go      → None (Harness-only, no upstream basis)
    """
    parts = internal.split(".")
    if len(parts) != 2 or parts[0] != "sk":
        return None
    upstream_set = {
        "specify", "constitution", "clarify", "plan", "tasks", "analyze", "checklist",
    }
    name = parts[1]
    if name not in upstream_set:
        return None
    return Path(UPSTREAM_TEMPLATES) / f"{name}-template.md"


def rename_artifact(artifact: str, iteration: str) -> str:
    """Map upstream artifact filename to sk iteration-aware name.

    spec.md → spec-001.md
    plan.md → plan-001.md
    tasks.md → tasks-001.md
    test-plan.md → test-plan-001.md
    """
    base = artifact.rsplit(".", 1)[0]
    ext = "md"
    if base in {"spec", "plan", "tasks", "test-plan"}:
        return f"{base}-{iteration}.{ext}"
    return artifact


def parse_frontmatter(text: str) -> tuple[dict[str, str], str]:
    """Parse a markdown file with optional --- yaml frontmatter."""
    m = _FRONTMATTER.match(text)
    if not m:
        return {}, text
    fm: dict[str, str] = {}
    for line in m.group("body").splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            fm[k.strip()] = v.strip()
    return fm, m.group("rest")


def emit_frontmatter(fm: dict[str, str], body: str) -> str:
    if not fm:
        return body
    lines = ["---"] + [f"{k}: {v}" for k, v in fm.items()] + ["---", ""]
    return "\n".join(lines) + body.lstrip("\n")


def harness_frontmatter(internal: str, description: str, source: str | None = None) -> dict[str, str]:
    """Build agentskills.io-compatible frontmatter for a Harness skill.

    Drops `allowed-tools` (per ERD OQ-3 resolution v0.2: not honored by Claude Code).
    """
    rn = CommandRename.of(internal)
    fm = {
        "name": rn.skill_dir,
        "description": description,
        "argument-hint": "",
    }
    if source:
        fm["source"] = source
    return fm


def inherit_body(upstream_md: Path, internal: str, description: str) -> str:
    """Read an upstream skill/template body and emit a Harness skill body.

    1. Read upstream
    2. Strip incompatible frontmatter keys (handoffs, scripts, allowed-tools)
    3. Translate `/speckit-<x>` references to `/sk-<x>` where applicable
    4. Emit Harness frontmatter + adapted body
    """
    raw = upstream_md.read_text(encoding="utf-8")
    _, body = parse_frontmatter(raw)
    body = re.sub(r"/speckit[-.]([a-z_-]+)", r"/sk-\1", body)
    fm = harness_frontmatter(internal, description, source=str(upstream_md))
    return emit_frontmatter(fm, body)


def skill_path(repo_root: Path, internal: str) -> Path:
    rn = CommandRename.of(internal)
    return repo_root / HARNESS_SKILL_DIR / rn.skill_dir / "SKILL.md"
