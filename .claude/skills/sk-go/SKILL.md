---
name: sk-go
description: Start or resume the TPM master loop (Phases 1-5)
argument-hint: "[--until-pause] [--no-confirm]"
---

You (Claude) ARE the TPM agent for this session. Drive the loop in PRD §5.3 until a natural stopping point.

## Read on entry

```bash
sk status          # get current phase, task counts, pause state
sk log --tail 20   # recent decisions
```

Also read (without printing full content):
- `.skspec/.iterations.json` — active iteration id
- `.skspec/.progress/state.json` — phase, tasks, batch, paused
- `.skspec/.agents.json` — roster
- `.skspec/.agents-catalog.json` — candidate pool
- `.skspec/.erd/plan-<N>.md` — current ERD
- `.skspec/.task/tasks-<N>.md` — task DAG
- Recent `.skspec/.progress/decision-log.md` entries

## Loop algorithm (per assistant turn)

**Step 0 — Check pause + pending-channels**
If `state.paused=True`:
- `pause_reason=review_requested` → dispatch multi-role review subagents (see Step 3b below); write findings to decision-log; then auto-resume (clear pause) and continue
- any other reason → report and stop; user resumes via `/sk-resume`

Before looping further, scan `.skspec/.erd-pending/`:
- If any proposal exists: read it, snapshot plan-NNN.md, `sk erd-pending accept <id>` (agent-autonomous per Decision #4), then continue
- If `.skspec/.prd-pending/` has proposals: set `paused=True`, `pause_reason=prd_proposal`, and stop (requires user)

**Step 1 — Phase routing**
- phase=`spec-drafted` → trigger architect (`/sk-plan` logic inline) to write ERD, then continue
- phase=`phase-1-erd` (ERD just written) → trigger engineer (`/sk-tasks` logic inline) to decompose, then continue
- phase=`phase-2-complete-ready-for-go` → enter micro loop (Step 2)
- phase=`phase-3-implementation` → continue micro loop (Step 2)
- phase=`completed` → nothing to do; prompt user for `/sk-specify` on next iteration

**Step 2 — Agent roster reconciliation** (within micro loop)
Use `sk_harness.loop.roster_reconcile(io, paths, iteration, loop=N)`. Writes `.agents.json` and returns (added, deactivated). Log the diff.

**Step 3 — Multi-role review** (lightweight; skip on first entry since Phase 1/2 already reviewed)
For each active role that is a reviewer (architect, qa, security, engineer), spawn a Task subagent with the role's template `templates/harness/agents/<role>.md`. Ask: "Does the plan still hold? Any blockers before next batch?". Concurrent dispatch via parallel tool calls.

**Step 4 — Decision branch** (first-match)
Inspect review results + state:
- (a) Task hit `max_retries` (state.tasks has `failed` entries): `sk pause --reason max_retries_exceeded`, report, stop
- (b) Any review found ERD-vs-reality mismatch OR technical ambiguity: trigger `/sk-plan` revision flow (snapshot + architect rewrites, logs `[MAJOR]` or `[routine]` per Constitution §VIII), **continue** — technical items never pause the loop
- (c) Any review found a genuine USER-INTENT gap (what feature, which requirement wins, is scope X in or out, acceptance threshold): write `.prd-pending/proposal-<ts>.md`, `sk pause --reason prd_proposal`, stop. Tech items do NOT go here.
- (d) Deadlock (`ready_set=[]` but pending tasks exist, and this has happened ≥2 consecutive loops): `sk pause --reason deadlock`, stop
- (e) Task granularity issue surfaced: invoke engineer to adjust tasks-<N>.md, then continue
- (f) All clear: continue

**Step 5 — Compute ready set + batch dispatch**
```python
from sk_harness.paths import Paths
from sk_harness.state.io import StateIO
from sk_harness.loop import load_dag, compute_ready, begin_batch

paths = Paths.find()
io = StateIO(paths)
state = io.load_state()
graph, meta = load_dag(paths, state.active_iteration)
ready = compute_ready(state, graph)
batch = ready[:io.load_agents().max_concurrency]
state = begin_batch(io, state, batch, loop=state.loop_count + 1)
```

Now dispatch all `batch` tasks in **parallel** via Task tool calls (one assistant message, N tool uses). For each task T-XX:
- Subagent type: the `agent` field from T-XX sidecar (e.g., general-purpose, python-reviewer, etc.)
- Prompt: derived from `templates/harness/agents/engineer.md` with task metadata, ERD refs, outputs list
- Constraint: subagent must NOT touch `.progress/state.json` or `decision-log.md` — TPM serializes writes

**Step 6 — Settle batch**
For each task that returned, call `sk_harness.loop.settle_task(io, paths, iteration, task_id, success=..., agent=..., summary=..., outputs=[...])`. This writes snapshot + updates state atomically.

**Step 7 — Knowledge extraction**
For any task that (a) failed then succeeded, (b) triggered ERD revision, (c) introduced a reusable pattern: dispatch knowledge-extractor subagent per `templates/harness/agents/knowledge-extractor.md`. Append to `.knowledge/`.

**Step 8 — Termination check**
```python
from sk_harness.loop import check_termination
decision, reason = check_termination(state, graph, consecutive_empty_ready=N)
```
- decision=`continue` → next loop iteration (goto Step 0 on next assistant turn)
- decision=`pause` → `sk pause --reason <reason>`, report, stop
- decision=`retro` → enter Phase 5 (see below)

**Step 8.5 — Step flag check**
If `state.pause_reason == step` (armed by `/sk-step`): after this batch settles, set `paused=True` and stop. Do not continue to another loop even if decision was `continue`.

**Phase 5 — Iteration retro**
Dispatch retro-subagent per `templates/harness/agents/retro.md`. It writes `.knowledge/retrospectives/<NNN>-retro.md`. Then run `sk iteration complete`. Loop exits.

## Headless mode (`--until-pause`)
If `--until-pause` in $ARGUMENTS: continue the loop without pausing between assistant turns until you hit (a), (c), (d), or (retro). Report final state.

If `--no-confirm` in $ARGUMENTS: treat PRD proposals as auto-rejected (log the rejection) rather than pausing. This trades safety for unattended progress.

## Output per turn
End each turn with a concise status:
```
loop=N phase=X batch=[T-XX,T-YY] next=(continue|pause:reason|retro)
```

## Constitution reminders
- §III: snapshot before ERD rewrites
- §IV: log every decision
- §VII: PRD changes go through `.prd-pending/`
