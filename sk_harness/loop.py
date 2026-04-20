"""TPM loop orchestration helpers.

The *actual* loop runs in Claude Code's assistant session driven by
`.claude/skills/sk-go/SKILL.md` instructions. This module provides the
Python primitives the skill calls between tool invocations:

- ready_set: compute next batch
- settle_task: record completion/failure
- roster_reconcile: update .agents.json based on content
- termination: decide whether to loop, pause, or enter Phase 5

All functions are atomic under `StateIO.lock()`.
"""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from sk_harness.dag.graph import TaskGraph
from sk_harness.dag.parser import read_sidecars
from sk_harness.observability.decision_log import DecisionLog
from sk_harness.paths import Paths
from sk_harness.snapshots import write_snapshot
from sk_harness.state.io import StateIO
from sk_harness.state.models import (
    AgentEntry,
    AgentsConfig,
    PauseReason,
    Phase,
    ProgressState,
    TaskState,
    TaskStateBrief,
)


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _task_states(state: ProgressState) -> dict[str, TaskState]:
    return {t.id: t.state for t in state.tasks}


def current_iteration(io: StateIO) -> str:
    reg = io.load_iterations()
    if not reg.active:
        raise RuntimeError("No active iteration. Run /sk-specify first.")
    return reg.active


def load_dag(paths: Paths, iteration: str) -> tuple[TaskGraph, dict[str, Any]]:
    sidecar_dir = paths.task_sidecar_dir(iteration)
    tasks = read_sidecars(sidecar_dir)
    if not tasks:
        raise RuntimeError(f"No tasks found at {sidecar_dir}")
    meta = {t.id: t for t in tasks}
    return TaskGraph(tasks), meta


def compute_ready(state: ProgressState, graph: TaskGraph) -> list[str]:
    return graph.ready_set(_task_states(state))


def begin_batch(io: StateIO, state: ProgressState, tids: list[str], loop: int) -> ProgressState:
    with io.lock():
        current = io.load_state()
        for t in current.tasks:
            if t.id in tids:
                t.state = TaskState.running
        current.current_batch = list(tids)
        current.loop_count = loop
        current.phase = Phase.phase_3_implementation
        io.save_state(current)
        return current


def settle_task(
    io: StateIO,
    paths: Paths,
    iteration: str,
    task_id: str,
    *,
    success: bool,
    agent: str,
    summary: str,
    outputs: list[str],
) -> ProgressState:
    snap = write_snapshot(
        paths, iteration, task_id,
        agent=agent, summary=summary, outputs=outputs,
    )
    with io.lock():
        state = io.load_state()
        t = state.task(task_id)
        if t is None:
            t = TaskStateBrief(id=task_id)
            state.tasks.append(t)
        if success:
            t.state = TaskState.done
            t.snapshot = str(snap.relative_to(paths.skspec))
        else:
            t.retries += 1
            cfg = io.load_agents()
            if t.retries > cfg.max_retries:
                t.state = TaskState.failed
            else:
                t.state = TaskState.pending
        if task_id in state.current_batch:
            state.current_batch.remove(task_id)
        io.save_state(state)
        return state


def check_termination(
    state: ProgressState, graph: TaskGraph, *, consecutive_empty_ready: int,
) -> tuple[str, PauseReason | None]:
    """Return (decision, pause_reason) where decision in {continue, pause, retro}."""
    if state.paused:
        return "pause", state.pause_reason
    states = _task_states(state)
    pending = [t.id for t in state.tasks if t.state == TaskState.pending]
    running = [t.id for t in state.tasks if t.state == TaskState.running]
    failed = [t.id for t in state.tasks if t.state == TaskState.failed]
    if failed:
        return "pause", PauseReason.max_retries_exceeded
    if not pending and not running:
        return "retro", None
    ready = graph.ready_set(states)
    if not ready and not running:
        if consecutive_empty_ready >= 2:
            return "pause", PauseReason.deadlock
    return "continue", None


ROSTER_KEYWORDS: dict[str, list[str]] = {
    "database-reviewer":   ["sql", "postgres", "mysql", "migration", "schema", "index"],
    "security-reviewer":   ["auth", "crypto", "token", "secret", "owasp", "xss", "csrf"],
    "performance-optimizer": ["perf", "profiling", "bundle", "latency", "p95"],
    "tdd-guide":           ["test", "coverage", "tdd", "pytest"],
    "typescript-reviewer": ["typescript", "tsconfig", "node ", "npm", "pnpm"],
    "go-reviewer":         ["golang", ".go", "go mod", "goroutine"],
    "rust-reviewer":       ["rust", "cargo", "borrow"],
    "python-reviewer":     ["python", "pyproject", "pip"],
    "e2e-runner":          ["e2e", "playwright", "end-to-end"],
}


def roster_reconcile(
    io: StateIO, paths: Paths, iteration: str, *, loop: int,
) -> tuple[list[str], list[str]]:
    """Inspect current ERD + tasks; add/deactivate catalog entries as needed.

    Returns (added_roles, deactivated_roles).
    """
    added: list[str] = []
    deactivated: list[str] = []

    catalog_path = paths.agents_catalog
    catalog = json.loads(catalog_path.read_text(encoding="utf-8")).get("catalog", {})

    corpus_parts: list[str] = []
    for p in [paths.plan(iteration), paths.tasks(iteration)]:
        if p.exists():
            corpus_parts.append(p.read_text(encoding="utf-8").lower())
    corpus = "\n".join(corpus_parts)
    if not corpus:
        return added, deactivated

    with io.lock():
        cfg = io.load_agents()
        active_roles = {a.role for a in cfg.active()}

        for subagent_type, entry in catalog.items():
            domains = entry.get("domains", [])
            keywords = ROSTER_KEYWORDS.get(subagent_type, []) + [d.lower() for d in domains]
            hit = any(kw and kw in corpus for kw in keywords)
            role = subagent_type
            existing = next((a for a in cfg.roster if a.role == role), None)

            if hit and existing is None:
                if len(cfg.active()) >= cfg.max_active_agents:
                    continue
                cfg.roster.append(AgentEntry(
                    role=role, subagent_type=subagent_type,
                    status="active", added_loop=loop,
                    rationale=f"Matched keyword in ERD/tasks corpus",
                ))
                added.append(role)
            elif hit and existing is not None and existing.status == "inactive":
                existing.status = "active"
                existing.added_loop = loop
                existing.deactivated_loop = None
                added.append(role)
            elif not hit and existing is not None and existing.status == "active" and role not in {"tpm"}:
                existing.status = "inactive"
                existing.deactivated_loop = loop
                deactivated.append(role)

        io.save_agents(cfg)
    return added, deactivated


def log(
    paths: Paths, *, iteration: str, loop: int, actor: str, decision: str, body: str,
) -> None:
    DecisionLog(paths.decision_log).append(
        iteration=iteration, loop=loop, actor=actor, decision=decision, body=body,
    )
