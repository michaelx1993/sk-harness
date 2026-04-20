"""Atomic file IO with cooperative lock for `.skspec/` state."""

from __future__ import annotations

import json
import os
import tempfile
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator, Type, TypeVar

from filelock import FileLock, Timeout
from pydantic import BaseModel

from sk_harness.paths import Paths
from sk_harness.state.models import (
    AgentsConfig,
    IterationsRegistry,
    ProgressState,
    TaskMeta,
)

T = TypeVar("T", bound=BaseModel)


def atomic_write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=f".{path.name}.", dir=str(path.parent), text=True)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(content)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, path)
    except Exception:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


def write_json(path: Path, data: Any) -> None:
    atomic_write(path, json.dumps(data, indent=2, ensure_ascii=False) + "\n")


def write_model(path: Path, model: BaseModel) -> None:
    atomic_write(path, model.model_dump_json(indent=2) + "\n")


def read_model(path: Path, cls: Type[T]) -> T:
    return cls.model_validate_json(path.read_text(encoding="utf-8"))


class StateIO:
    """Coordinated read/write for state files. Always grab `lock()` for writes."""

    def __init__(self, paths: Paths, lock_timeout: float = 10.0) -> None:
        self.paths = paths
        self._lock = FileLock(str(paths.lock_file), timeout=lock_timeout)

    @contextmanager
    def lock(self) -> Iterator[None]:
        try:
            with self._lock:
                yield
        except Timeout as e:
            raise RuntimeError(
                f"Timed out acquiring {self.paths.lock_file}. Another sk process running?"
            ) from e

    def load_state(self) -> ProgressState:
        return read_model(self.paths.state_file, ProgressState)

    def save_state(self, state: ProgressState) -> None:
        from sk_harness.state.models import _utcnow
        state.last_updated = _utcnow()
        write_model(self.paths.state_file, state)

    def load_iterations(self) -> IterationsRegistry:
        return read_model(self.paths.iterations, IterationsRegistry)

    def save_iterations(self, reg: IterationsRegistry) -> None:
        write_model(self.paths.iterations, reg)

    def load_agents(self) -> AgentsConfig:
        return read_model(self.paths.agents, AgentsConfig)

    def save_agents(self, cfg: AgentsConfig) -> None:
        write_model(self.paths.agents, cfg)

    def load_task_sidecar(self, iteration: str, task_id: str) -> TaskMeta:
        path = self.paths.task_sidecar_dir(iteration) / f"{task_id}.json"
        return read_model(path, TaskMeta)

    def save_task_sidecar(self, iteration: str, task: TaskMeta) -> None:
        path = self.paths.task_sidecar_dir(iteration) / f"{task.id}.json"
        write_model(path, task)
