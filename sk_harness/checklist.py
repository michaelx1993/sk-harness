"""Generate markdown acceptance checklists from task sidecars."""

from __future__ import annotations

from sk_harness.dag.parser import read_sidecars
from sk_harness.paths import Paths


def generate_checklist(paths: Paths, iteration: str) -> str:
    sidecar_dir = paths.task_sidecar_dir(iteration)
    if not sidecar_dir.exists():
        return f"No sidecars for iteration {iteration}."
    sidecars = read_sidecars(sidecar_dir)
    if not sidecars:
        return f"Sidecar dir for iteration {iteration} empty."
    lines = [f"# Acceptance checklist — iteration {iteration}", ""]
    for t in sidecars:
        accepts = ", ".join(t.acceptance_ids) if t.acceptance_ids else "—"
        lines.append(f"- [ ] **{t.id}** {t.title}  ({accepts})")
    return "\n".join(lines) + "\n"
