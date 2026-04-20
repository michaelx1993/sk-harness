"""Filesystem layout constants and resolvers for `.skspec/` workspace."""

from __future__ import annotations

from pathlib import Path

SKSPEC_DIRNAME = ".skspec"


class Paths:
    def __init__(self, root: Path) -> None:
        self.root = Path(root).resolve()
        self.skspec = self.root / SKSPEC_DIRNAME

    @classmethod
    def find(cls, start: Path | None = None) -> Paths:
        cur = Path(start or Path.cwd()).resolve()
        for cand in [cur, *cur.parents]:
            if (cand / SKSPEC_DIRNAME).is_dir():
                return cls(cand)
        raise FileNotFoundError(f"No {SKSPEC_DIRNAME}/ found from {cur} upward")

    @property
    def version_file(self) -> Path:        return self.skspec / ".version"
    @property
    def constitution(self) -> Path:        return self.skspec / ".constitution.md"
    @property
    def iterations(self) -> Path:          return self.skspec / ".iterations.json"
    @property
    def agents(self) -> Path:              return self.skspec / ".agents.json"
    @property
    def agents_catalog(self) -> Path:      return self.skspec / ".agents-catalog.json"

    @property
    def prd_dir(self) -> Path:             return self.skspec / "prd"
    @property
    def tests_dir(self) -> Path:           return self.skspec / "tests"
    @property
    def docs_dir(self) -> Path:            return self.skspec / "docs"
    @property
    def references_dir(self) -> Path:      return self.skspec / "references"

    @property
    def erd_dir(self) -> Path:             return self.skspec / ".erd"
    @property
    def erd_history_dir(self) -> Path:     return self.erd_dir / "history"
    @property
    def task_dir(self) -> Path:            return self.skspec / ".task"
    @property
    def task_archive_dir(self) -> Path:    return self.task_dir / "archive"
    @property
    def progress_dir(self) -> Path:        return self.skspec / ".progress"
    @property
    def state_file(self) -> Path:          return self.progress_dir / "state.json"
    @property
    def decision_log(self) -> Path:        return self.progress_dir / "decision-log.md"
    @property
    def milestones(self) -> Path:          return self.progress_dir / "milestones.md"
    @property
    def snapshot_dir(self) -> Path:        return self.skspec / ".snapshot"
    @property
    def knowledge_dir(self) -> Path:       return self.skspec / ".knowledge"
    @property
    def retro_dir(self) -> Path:           return self.knowledge_dir / "retrospectives"
    @property
    def prd_pending_dir(self) -> Path:     return self.skspec / ".prd-pending"
    @property
    def erd_pending_dir(self) -> Path:     return self.skspec / ".erd-pending"
    @property
    def lock_file(self) -> Path:           return self.skspec / ".lock"

    def spec(self, n: str) -> Path:        return self.prd_dir / f"spec-{n}.md"
    def plan(self, n: str) -> Path:        return self.erd_dir / f"plan-{n}.md"
    def tasks(self, n: str) -> Path:       return self.task_dir / f"tasks-{n}.md"
    def task_sidecar_dir(self, n: str) -> Path: return self.task_dir / f"tasks-{n}"
    def test_plan(self, n: str) -> Path:   return self.tests_dir / f"test-plan-{n}.md"
    def iter_snapshot_dir(self, n: str) -> Path: return self.snapshot_dir / f"iter-{n}"
    def retro(self, n: str) -> Path:       return self.retro_dir / f"{n}-retro.md"
