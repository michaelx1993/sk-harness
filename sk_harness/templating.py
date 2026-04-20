"""Minimal Jinja-style {{var}} template rendering for harness templates."""

from __future__ import annotations

import re
from pathlib import Path

_VAR = re.compile(r"\{\{\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*\}\}")


def render(template: str, context: dict[str, str]) -> str:
    def sub(m: re.Match[str]) -> str:
        key = m.group(1)
        return str(context.get(key, m.group(0)))
    return _VAR.sub(sub, template)


def render_file(template_path: Path, context: dict[str, str]) -> str:
    return render(template_path.read_text(encoding="utf-8"), context)


def render_to(template_path: Path, target_path: Path, context: dict[str, str]) -> None:
    target_path.parent.mkdir(parents=True, exist_ok=True)
    target_path.write_text(render_file(template_path, context), encoding="utf-8")
