"""Pydantic models for `.skspec/` state files."""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


def _utcnow() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


class TaskState(str, Enum):
    pending = "pending"
    running = "running"
    done = "done"
    failed = "failed"
    blocked = "blocked"


class Phase(str, Enum):
    init = "init"
    spec_drafted = "spec-drafted"
    phase_1_erd = "phase-1-erd"
    phase_2_tasks = "phase-2-tasks"
    phase_2_complete = "phase-2-complete-ready-for-go"
    phase_3_implementation = "phase-3-implementation"
    phase_5_retro = "phase-5-retro"
    completed = "completed"


class PauseReason(str, Enum):
    user = "user"
    step = "step"
    prd_proposal = "prd_proposal"
    erd_proposal = "erd_proposal"
    review_requested = "review_requested"
    max_retries_exceeded = "max_retries_exceeded"
    deadlock = "deadlock"


class IterationEntry(BaseModel):
    model_config = ConfigDict(extra="allow")
    id: str
    slug: str
    status: Literal["planned", "active", "completed", "archived"]
    started_at: str | None = None
    completed_at: str | None = None
    spec: str
    plan: str
    tasks: str
    test_plan: str


class IterationsRegistry(BaseModel):
    version: int = 1
    active: str | None
    iterations: list[IterationEntry] = Field(default_factory=list)

    def get_active(self) -> IterationEntry | None:
        if not self.active:
            return None
        return next((it for it in self.iterations if it.id == self.active), None)


class TaskMeta(BaseModel):
    model_config = ConfigDict(extra="allow")
    id: str
    title: str = ""
    deps: list[str] = Field(default_factory=list)
    agent: str = "general-purpose"
    validator: str = "code-reviewer"
    idempotent: bool = True
    outputs: list[str] = Field(default_factory=list)
    state: TaskState = TaskState.pending
    retries: int = 0
    acceptance_ids: list[str] = Field(default_factory=list)
    estimate: Literal["S", "M", "L"] = "M"
    erd_refs: list[str] = Field(default_factory=list)


class TaskStateBrief(BaseModel):
    model_config = ConfigDict(extra="allow")
    id: str
    state: TaskState = TaskState.pending
    retries: int = 0
    snapshot: str | None = None


class ProgressState(BaseModel):
    version: int = 1
    active_iteration: str | None = None
    phase: Phase = Phase.init
    loop_count: int = 0
    last_updated: str = Field(default_factory=_utcnow)
    tasks: list[TaskStateBrief] = Field(default_factory=list)
    current_batch: list[str] = Field(default_factory=list)
    paused: bool = False
    pause_reason: PauseReason | None = None

    def task(self, tid: str) -> TaskStateBrief | None:
        return next((t for t in self.tasks if t.id == tid), None)

    def ready_set(self, dag: dict[str, list[str]]) -> list[str]:
        done = {t.id for t in self.tasks if t.state == TaskState.done}
        return [
            t.id for t in self.tasks
            if t.state == TaskState.pending and all(d in done for d in dag.get(t.id, []))
        ]


class AgentEntry(BaseModel):
    model_config = ConfigDict(extra="allow")
    role: str
    subagent_type: str
    status: Literal["active", "inactive", "locked"] = "active"
    added_loop: int = 0
    deactivated_loop: int | None = None
    rationale: str = ""


class AgentsConfig(BaseModel):
    version: int = 1
    max_concurrency: int = 3
    max_retries: int = 2
    max_active_agents: int = 8
    roster: list[AgentEntry] = Field(default_factory=list)

    def active(self) -> list[AgentEntry]:
        return [a for a in self.roster if a.status == "active"]
