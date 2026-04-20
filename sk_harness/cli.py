"""Click-based CLI for `sk` — backs every `/sk-*` skill invocation."""

from __future__ import annotations

import shutil
import sys
from datetime import UTC
from pathlib import Path

import click
from rich.console import Console
from rich.table import Table

from sk_harness.analyze import analyze_iteration, format_report
from sk_harness.checklist import generate_checklist
from sk_harness.dag.graph import TaskGraph
from sk_harness.dag.parser import read_sidecars
from sk_harness.observability.decision_log import DecisionLog
from sk_harness.paths import Paths
from sk_harness.proposals import (
    accept_erd_proposal,
    accept_proposal,
    list_erd_pending,
    list_pending,
    reject_erd_proposal,
    reject_proposal,
)
from sk_harness.state.io import StateIO
from sk_harness.state.models import (
    AgentEntry,
    PauseReason,
    Phase,
    TaskState,
)

console = Console()
SCHEMA_VERSION = "0.3.0"


def _paths_or_exit() -> Paths:
    try:
        return Paths.find()
    except FileNotFoundError as e:
        console.print(f"[red]error:[/red] {e}")
        console.print("Hint: run `sk init` first or cd into a project with `.skspec/`.")
        sys.exit(2)


@click.group()
@click.version_option("0.3.0", prog_name="sk")
def main() -> None:
    """sk Harness — SDD + autonomous TPM loop on top of spec-kit."""


@main.command("init")
@click.argument("name", required=False)
def init_cmd(name: str | None) -> None:
    """Bootstrap .skspec/ skeleton in the current directory."""
    cwd = Path.cwd()
    target = cwd / ".skspec"
    if target.exists():
        console.print(f"[yellow].skspec/ already exists at[/yellow] {target}")
        console.print("Repair-only mode: checking for missing files.")
    repo_root = Path(__file__).resolve().parent.parent
    skeleton = repo_root / "templates" / "harness" / "skspec-skeleton"
    if not skeleton.exists():
        console.print(f"[red]skeleton not found at {skeleton}[/red]")
        sys.exit(3)
    for src in skeleton.rglob("*"):
        if src.is_dir():
            (target / src.relative_to(skeleton)).mkdir(parents=True, exist_ok=True)
        elif src.name == ".gitkeep":
            dest = target / src.relative_to(skeleton)
            dest.parent.mkdir(parents=True, exist_ok=True)
            if not dest.exists():
                dest.write_text("")
        else:
            dest = target / src.relative_to(skeleton)
            dest.parent.mkdir(parents=True, exist_ok=True)
            if not dest.exists():
                shutil.copy2(src, dest)
    console.print(f"[green]✓[/green] .skspec/ ready at {target}")
    if name:
        console.print(f"Project name: {name} (used in next /sk-specify)")


@main.command("status")
def status_cmd() -> None:
    paths = _paths_or_exit()
    io = StateIO(paths)
    try:
        state = io.load_state()
        reg = io.load_iterations()
        cfg = io.load_agents()
    except FileNotFoundError as e:
        console.print(f"[red]state missing:[/red] {e}")
        sys.exit(2)

    active = reg.get_active()
    header = f"Iteration: [cyan]{reg.active or '(none)'}[/cyan]"
    if active:
        header += f" · slug={active.slug} · status={active.status}"
    header += f" · phase=[magenta]{state.phase.value}[/magenta] · loop={state.loop_count}"
    console.print(header)

    tab = Table(title="Task states")
    tab.add_column("State")
    tab.add_column("Count", justify="right")
    counts = {s: 0 for s in TaskState}
    for t in state.tasks:
        counts[t.state] += 1
    for s, c in counts.items():
        tab.add_row(s.value, str(c))
    console.print(tab)

    console.print(f"paused=[yellow]{state.paused}[/yellow] reason={state.pause_reason or '—'}")
    console.print(f"current_batch={state.current_batch or '[]'}")
    console.print(f"roster: {len(cfg.active())} active / {len(cfg.roster)} total")

    pending = list_pending(paths)
    if pending:
        console.print(f"[yellow].prd-pending/ proposals[/yellow]: {len(pending)}")
        for p in pending:
            console.print(f"  - {p.name}")


@main.command("pause")
@click.option("--reason", default="user")
def pause_cmd(reason: str) -> None:
    paths = _paths_or_exit()
    io = StateIO(paths)
    with io.lock():
        state = io.load_state()
        if state.paused:
            console.print("[yellow]already paused[/yellow]")
            return
        state.paused = True
        try:
            state.pause_reason = PauseReason(reason)
        except ValueError:
            state.pause_reason = PauseReason.user
        io.save_state(state)
    DecisionLog(paths.decision_log).append(
        iteration=state.active_iteration or "?", loop=state.loop_count,
        actor="sk.pause(user)", decision="pause",
        body=f"User requested pause. Reason={reason}.",
    )
    console.print("[green]✓[/green] paused")


@main.command("resume")
def resume_cmd() -> None:
    paths = _paths_or_exit()
    io = StateIO(paths)
    with io.lock():
        state = io.load_state()
        if not state.paused:
            console.print("[yellow]not paused[/yellow]")
            return
        state.paused = False
        state.pause_reason = None
        io.save_state(state)
    DecisionLog(paths.decision_log).append(
        iteration=state.active_iteration or "?", loop=state.loop_count,
        actor="sk.resume(user)", decision="resume",
        body="User resumed loop.",
    )
    console.print("[green]✓[/green] resumed — invoke /sk-go to continue loop")


@main.command("log")
@click.option("--tail", "-n", default=50, show_default=True)
def log_cmd(tail: int) -> None:
    paths = _paths_or_exit()
    if not paths.decision_log.exists():
        console.print("[yellow]no decision log yet[/yellow]")
        return
    lines = paths.decision_log.read_text(encoding="utf-8").splitlines()
    for line in lines[-tail:]:
        console.print(line)


@main.group("tasks")
def tasks_group() -> None:
    """Task DAG operations."""


@tasks_group.command("list")
def tasks_list_cmd() -> None:
    paths = _paths_or_exit()
    io = StateIO(paths)
    state = io.load_state()
    reg = io.load_iterations()
    if not reg.active:
        console.print("[yellow]no active iteration[/yellow]")
        return
    sidecars = read_sidecars(paths.task_sidecar_dir(reg.active))
    by_id = {t.id: t for t in sidecars}
    tab = Table(title=f"Tasks for iteration {reg.active}")
    tab.add_column("id"); tab.add_column("state"); tab.add_column("title")
    tab.add_column("deps"); tab.add_column("agent")
    for brief in state.tasks:
        meta = by_id.get(brief.id)
        tab.add_row(
            brief.id, brief.state.value,
            (meta.title if meta else "")[:60],
            ",".join(meta.deps) if meta else "",
            meta.agent if meta else "",
        )
    console.print(tab)


@tasks_group.command("show")
@click.argument("task_id")
def tasks_show_cmd(task_id: str) -> None:
    paths = _paths_or_exit()
    io = StateIO(paths)
    reg = io.load_iterations()
    if not reg.active:
        console.print("[red]no active iteration[/red]"); sys.exit(2)
    sidecar = paths.task_sidecar_dir(reg.active) / f"{task_id}.json"
    if not sidecar.exists():
        console.print(f"[red]{task_id} not found[/red]"); sys.exit(2)
    console.print_json(sidecar.read_text(encoding="utf-8"))


@tasks_group.command("graph")
def tasks_graph_cmd() -> None:
    paths = _paths_or_exit()
    io = StateIO(paths)
    reg = io.load_iterations()
    if not reg.active:
        console.print("[red]no active iteration[/red]"); sys.exit(2)
    sidecars = read_sidecars(paths.task_sidecar_dir(reg.active))
    g = TaskGraph(sidecars)
    console.print(f"DAG depth: {g.depth()}  critical path: {' → '.join(g.critical_path())}")


@tasks_group.command("retry")
@click.argument("task_id")
def tasks_retry_cmd(task_id: str) -> None:
    paths = _paths_or_exit()
    io = StateIO(paths)
    with io.lock():
        state = io.load_state()
        t = state.task(task_id)
        if t is None:
            console.print(f"[red]{task_id} not in state[/red]"); sys.exit(2)
        if t.state != TaskState.failed:
            console.print(f"[yellow]{task_id} is {t.state.value}, not failed — nothing to reset[/yellow]")
            return
        t.state = TaskState.pending
        t.retries = 0
        io.save_state(state)
    DecisionLog(paths.decision_log).append(
        iteration=state.active_iteration or "?", loop=state.loop_count,
        actor="sk.tasks.retry(user)", decision=f"reset {task_id}",
        body=f"User reset failed task {task_id} to pending.",
    )
    console.print(f"[green]✓[/green] {task_id} reset to pending")


@main.group("iteration")
def iteration_group() -> None:
    """Iteration lifecycle commands."""


@iteration_group.command("list")
def iteration_list_cmd() -> None:
    paths = _paths_or_exit()
    io = StateIO(paths)
    reg = io.load_iterations()
    tab = Table(title="Iterations")
    tab.add_column("id"); tab.add_column("slug"); tab.add_column("status")
    tab.add_column("started"); tab.add_column("completed")
    for it in reg.iterations:
        tab.add_row(it.id, it.slug, it.status, it.started_at or "", it.completed_at or "")
    console.print(tab)


@iteration_group.command("complete")
def iteration_complete_cmd() -> None:
    paths = _paths_or_exit()
    io = StateIO(paths)
    with io.lock():
        state = io.load_state()
        reg = io.load_iterations()
        active = reg.get_active()
        if active is None:
            console.print("[red]no active iteration[/red]"); sys.exit(2)
        pending = [t.id for t in state.tasks if t.state in {TaskState.pending, TaskState.running}]
        if pending:
            console.print(f"[red]cannot complete — {len(pending)} task(s) pending/running[/red]")
            console.print(f"  {pending}")
            sys.exit(2)
        from datetime import datetime
        active.status = "completed"
        active.completed_at = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
        state.phase = Phase.completed
        reg.active = None
        io.save_iterations(reg)
        io.save_state(state)
    console.print(f"[green]✓[/green] iteration {active.id} ({active.slug}) marked completed")
    console.print("Next: /sk-specify to draft next iteration's PRD.")


@main.group("agent")
def agent_group() -> None:
    """Agent roster management."""


@agent_group.command("list")
def agent_list_cmd() -> None:
    paths = _paths_or_exit()
    io = StateIO(paths)
    cfg = io.load_agents()
    tab = Table(title="Agent roster")
    tab.add_column("role"); tab.add_column("type"); tab.add_column("status")
    tab.add_column("added"); tab.add_column("rationale")
    for a in cfg.roster:
        tab.add_row(a.role, a.subagent_type, a.status, str(a.added_loop), a.rationale[:60])
    console.print(tab)


@agent_group.command("add")
@click.argument("role")
@click.option("--type", "subagent_type", default="general-purpose")
@click.option("--rationale", default="manual")
def agent_add_cmd(role: str, subagent_type: str, rationale: str) -> None:
    paths = _paths_or_exit()
    io = StateIO(paths)
    with io.lock():
        cfg = io.load_agents()
        if any(a.role == role for a in cfg.roster):
            console.print(f"[yellow]role {role} already present[/yellow]"); return
        cfg.roster.append(AgentEntry(role=role, subagent_type=subagent_type, rationale=rationale))
        io.save_agents(cfg)
    console.print(f"[green]✓[/green] added {role} ({subagent_type})")


@agent_group.command("remove")
@click.argument("role")
def agent_remove_cmd(role: str) -> None:
    paths = _paths_or_exit()
    io = StateIO(paths)
    with io.lock():
        cfg = io.load_agents()
        before = len(cfg.roster)
        cfg.roster = [a for a in cfg.roster if a.role != role]
        if len(cfg.roster) == before:
            console.print(f"[yellow]{role} not in roster[/yellow]"); return
        io.save_agents(cfg)
    console.print(f"[green]✓[/green] removed {role}")


@main.command("specify")
@click.option("--accept", "accept_id", default=None, help="Accept a proposal by ID")
@click.option("--reject", "reject_id", default=None, help="Reject a proposal by ID")
def specify_cmd(accept_id: str | None, reject_id: str | None) -> None:
    paths = _paths_or_exit()
    io = StateIO(paths)
    if accept_id:
        matches = [p for p in list_pending(paths) if accept_id in p.name]
        if not matches:
            console.print(f"[red]no pending proposal matches '{accept_id}'[/red]"); sys.exit(2)
        reg = io.load_iterations()
        target = accept_proposal(paths, matches[0], reg.active or "001")
        console.print(f"[green]✓[/green] accepted; spec updated: {target}")
        return
    if reject_id:
        matches = [p for p in list_pending(paths) if reject_id in p.name]
        if not matches:
            console.print(f"[red]no pending proposal matches '{reject_id}'[/red]"); sys.exit(2)
        archived = reject_proposal(paths, matches[0])
        console.print(f"[green]✓[/green] rejected → {archived.name}")
        return
    console.print("`/sk-specify` drafting runs inside Claude Code (see SKILL.md). ")
    console.print("Use `sk specify --accept <id>` or `--reject <id>` for pending proposals.")


@main.command("step")
def step_cmd() -> None:
    """Request exactly one more batch from /sk-go, then pause."""
    paths = _paths_or_exit()
    io = StateIO(paths)
    with io.lock():
        state = io.load_state()
        state.paused = False
        state.pause_reason = PauseReason.step
        io.save_state(state)
    DecisionLog(paths.decision_log).append(
        iteration=state.active_iteration or "?", loop=state.loop_count,
        actor="sk.step(user)", decision="step-requested",
        body="User requested single-batch step via /sk-step. /sk-go will stop after next batch.",
    )
    console.print("[green]✓[/green] step armed — invoke /sk-go for one batch")


@main.command("review")
def review_cmd() -> None:
    """Request a review cycle. /sk-go picks up the review_requested pause reason."""
    paths = _paths_or_exit()
    io = StateIO(paths)
    with io.lock():
        state = io.load_state()
        state.paused = True
        state.pause_reason = PauseReason.review_requested
        io.save_state(state)
    DecisionLog(paths.decision_log).append(
        iteration=state.active_iteration or "?", loop=state.loop_count,
        actor="sk.review(user)", decision="review-requested",
        body="User requested review cycle. Next /sk-go will dispatch review subagents before Step 5.",
    )
    console.print("[green]✓[/green] review requested — resume with /sk-resume + /sk-go")


@main.group("config")
def config_group() -> None:
    """View/edit concurrency + retry settings."""


_ALLOWED_CONFIG_KEYS = {"max_concurrency", "max_retries", "max_active_agents"}


@config_group.command("show")
def config_show_cmd() -> None:
    paths = _paths_or_exit()
    cfg = StateIO(paths).load_agents()
    console.print(f"max_concurrency   = {cfg.max_concurrency}")
    console.print(f"max_retries       = {cfg.max_retries}")
    console.print(f"max_active_agents = {cfg.max_active_agents}")
    console.print(f"roster size       = {len(cfg.roster)} ({len(cfg.active())} active)")


@config_group.command("set")
@click.argument("key")
@click.argument("value", type=int)
def config_set_cmd(key: str, value: int) -> None:
    if key not in _ALLOWED_CONFIG_KEYS:
        console.print(f"[red]unknown config key:[/red] {key}")
        console.print(f"allowed: {sorted(_ALLOWED_CONFIG_KEYS)}")
        sys.exit(2)
    if value < 1:
        console.print("[red]value must be ≥ 1[/red]")
        sys.exit(2)
    paths = _paths_or_exit()
    io = StateIO(paths)
    with io.lock():
        cfg = io.load_agents()
        setattr(cfg, key, value)
        io.save_agents(cfg)
    console.print(f"[green]✓[/green] {key} = {value}")


@main.group("erd-pending")
def erd_pending_group() -> None:
    """Manage `.erd-pending/` proposals (agent-autonomous ERD revisions)."""


@erd_pending_group.command("list")
def erd_pending_list_cmd() -> None:
    paths = _paths_or_exit()
    pending = list_erd_pending(paths)
    if not pending:
        console.print("none pending")
        return
    for p in pending:
        console.print(p.name)


@erd_pending_group.command("accept")
@click.argument("proposal_id")
def erd_pending_accept_cmd(proposal_id: str) -> None:
    paths = _paths_or_exit()
    io = StateIO(paths)
    matches = [p for p in list_erd_pending(paths) if proposal_id in p.name]
    if not matches:
        console.print(f"[red]no ERD proposal matches '{proposal_id}'[/red]")
        sys.exit(2)
    reg = io.load_iterations()
    target = accept_erd_proposal(paths, matches[0], reg.active or "001")
    DecisionLog(paths.decision_log).append(
        iteration=reg.active or "?", loop=io.load_state().loop_count,
        actor="sk.erd-pending.accept(user)", decision=f"accept {matches[0].name}",
        body="Accepted ERD proposal; snapshot written; plan appended.",
    )
    console.print(f"[green]✓[/green] ERD updated: {target}")


@erd_pending_group.command("reject")
@click.argument("proposal_id")
def erd_pending_reject_cmd(proposal_id: str) -> None:
    paths = _paths_or_exit()
    matches = [p for p in list_erd_pending(paths) if proposal_id in p.name]
    if not matches:
        console.print(f"[red]no ERD proposal matches '{proposal_id}'[/red]")
        sys.exit(2)
    archived = reject_erd_proposal(paths, matches[0])
    console.print(f"[green]✓[/green] ERD proposal rejected → {archived.name}")


@main.command("analyze")
def analyze_cmd() -> None:
    """Cross-reference consistency check across spec/plan/tasks/test-plan."""
    paths = _paths_or_exit()
    io = StateIO(paths)
    reg = io.load_iterations()
    if not reg.active:
        console.print("[red]no active iteration[/red]")
        sys.exit(2)
    result = analyze_iteration(paths, reg.active)
    report = format_report(result)
    console.print(report)
    sys.exit(0 if result.ok else 1)


@main.command("checklist")
def checklist_cmd() -> None:
    """Emit markdown acceptance checklist for current iteration."""
    paths = _paths_or_exit()
    io = StateIO(paths)
    reg = io.load_iterations()
    if not reg.active:
        console.print("[red]no active iteration[/red]")
        sys.exit(2)
    console.print(generate_checklist(paths, reg.active))


@main.command("constitution")
@click.option("--show", is_flag=True, help="Print contents instead of path")
def constitution_cmd(show: bool) -> None:
    """Open or show `.constitution.md`."""
    paths = _paths_or_exit()
    cpath = paths.constitution
    if not cpath.exists():
        console.print(f"[yellow]constitution not found at {cpath}[/yellow]")
        sys.exit(2)
    if show:
        console.print(cpath.read_text(encoding="utf-8"))
    else:
        console.print(f"Edit: {cpath}")


if __name__ == "__main__":
    main()
