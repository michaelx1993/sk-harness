"""Unit tests for speckit_adapter."""
from __future__ import annotations

from sk_harness.speckit_adapter import (
    CommandRename,
    emit_frontmatter,
    harness_frontmatter,
    parse_frontmatter,
    rename_artifact,
    resolve_upstream_command,
)


def test_command_rename() -> None:
    r = CommandRename.of("sk.specify")
    assert r.skill_dir == "sk-specify"
    assert r.invocation == "/sk-specify"
    assert r.internal == "sk.specify"


def test_command_rename_nested() -> None:
    r = CommandRename.of("sk.tasks.retry")
    assert r.skill_dir == "sk-tasks-retry"
    assert r.invocation == "/sk-tasks-retry"


def test_rename_artifact() -> None:
    assert rename_artifact("spec.md", "001") == "spec-001.md"
    assert rename_artifact("plan.md", "042") == "plan-042.md"
    assert rename_artifact("random.md", "001") == "random.md"


def test_resolve_upstream_command_inherited() -> None:
    p = resolve_upstream_command("sk.plan")
    assert p is not None
    assert p.name == "plan-template.md"


def test_resolve_upstream_command_native() -> None:
    assert resolve_upstream_command("sk.go") is None
    assert resolve_upstream_command("not.well.formed") is None


def test_parse_emit_frontmatter_roundtrip() -> None:
    original = "---\nname: sk-specify\ndescription: draft PRD\n---\nbody here\n"
    fm, body = parse_frontmatter(original)
    assert fm == {"name": "sk-specify", "description": "draft PRD"}
    assert body == "body here\n"
    out = emit_frontmatter(fm, body)
    assert "name: sk-specify" in out
    assert "body here" in out


def test_harness_frontmatter_drops_allowed_tools() -> None:
    fm = harness_frontmatter("sk.init", "Init skspec")
    assert "allowed-tools" not in fm
    assert fm["name"] == "sk-init"
    assert fm["description"] == "Init skspec"
