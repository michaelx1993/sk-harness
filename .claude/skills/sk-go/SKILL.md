---
name: sk-go
description: Start or resume the TPM master loop (Phases 1-5)
argument-hint: "[--until-pause] [--no-confirm]"
---

You (Claude) ARE the TPM agent. Drive the loop in PRD §5.3 until a natural stop. All state-mutating operations go through the `sk` CLI (no raw Python in this skill — the CLI handles atomicity, locking, and logging).

## Read on entry

```bash
sk status           # current phase, task counts, pause state
sk log --tail 20    # recent decisions
```

Also read:
- `.skspec/.iterations.json` — active iteration id
- `.skspec/.progress/state.json` — phase, tasks, batch, paused
- `.skspec/.agents.json` — roster
- `.skspec/.erd/plan-<N>.md` — current ERD
- `.skspec/.task/tasks-<N>.md` — task DAG

## Loop algorithm (per assistant turn)

**Step 0 — Check pause + pending channels**
```bash
# State file shows paused + reason; react accordingly
sk erd-pending list   # auto-accept any agent-authored ERD proposals
```
If `state.paused=True`:
- `review_requested` → dispatch review subagents, log findings, `sk resume`, continue
- any other reason → report and stop
If any `.skspec/.prd-pending/proposal-*.md` exists (not yet accepted/rejected): `sk pause --reason prd_proposal`, stop.

**Step 1 — Phase routing** (from `sk status`)
- `spec-drafted` → run `/sk-plan` flow inline (architect writes ERD)
- `phase-1-erd` → run `/sk-tasks` flow (engineer decomposes, rolling-wave)
- `phase-2-complete-ready-for-go` → enter micro loop
- `phase-3-implementation` → continue micro loop
- `completed` → exit; prompt user for `/sk-specify`

**Step 2 — Agent roster reconciliation**
```bash
sk loop reconcile
```
Prints `added: [...]` and `deactivated: [...]`. Already persisted to `.agents.json`.

**Step 3 — Multi-role review** (skip on first entry after Phase 2)
Spawn Task subagents (parallel, one assistant message) for each active reviewer role using `templates/harness/agents/<role>.md` as system prompt. Ask: "Does the plan still hold? Any blockers?"

**Step 4 — Decision branch** (first-match)
- (a) failed tasks present → `sk pause --reason max_retries_exceeded`, stop
- (b) ERD-reality mismatch OR technical ambiguity → write ERD revision proposal, `sk erd-pending accept <id>`, continue (per Constitution §VIII, tech items never pause)
- (c) **genuine USER-INTENT gap** → write `.prd-pending/proposal-<ts>.md`, `sk pause --reason prd_proposal`, stop
- (d) deadlock (≥2 consecutive empty ready-sets) → `sk pause --reason deadlock`, stop
- (e) task granularity issue → run engineer to adjust tasks-<N>.md, continue
- (f) all clear → continue

**Step 5 — Compute ready set + batch dispatch**
```bash
ready=$(sk loop ready)                 # one task id per line
# read max_concurrency from `sk config show`; take first N
sk loop begin-batch T-01 T-02 T-03     # marks running + updates current_batch
```
Then dispatch each task in **parallel** via Task tool (one assistant message, N tool uses):
- Subagent type: `agent` field from T-XX sidecar (view via `sk tasks show T-XX`)
- Prompt: derived from `templates/harness/agents/engineer.md` + task metadata
- Constraint: subagent must NOT touch state.json or decision-log — TPM does that via `sk loop settle`

**Step 6 — Settle batch**
For each returned task:
```bash
sk loop settle T-01 --success --agent general-purpose \
  --summary "implemented X" --output path/a --output path/b
# or on failure:
sk loop settle T-02 --failure --agent general-purpose --summary "timed out"
```
`sk loop settle` writes the snapshot, updates task state, bumps retry counter on failure, and handles max_retries → `failed` transition.

**Step 7 — Knowledge extraction** (for notable completions)
Dispatch `knowledge-extractor` subagent per `templates/harness/agents/knowledge-extractor.md`. It writes to `.knowledge/{patterns,gotchas,decisions}.md`.

**Step 8 — Termination check**
```bash
decision=$(sk loop terminate)
```
Output: `continue` | `pause:<reason>` | `retro`.
- `continue` → next assistant turn (goto Step 0)
- `pause:*` → `sk pause --reason <that-reason>`, stop
- `retro` → enter Phase 5

**Step 8.5 — Step flag honored**
If `state.pause_reason == step` (armed by `/sk-step`): after settle, `sk pause --reason step`, stop.

**Phase 5 — Iteration retro**
Dispatch `retro` subagent per `templates/harness/agents/retro.md` → writes `.knowledge/retrospectives/<NNN>-retro.md`. Then `sk iteration complete`. Exit.

## Headless mode (`--until-pause`)
Continue across assistant turns without stopping until (a), (c), (d), or retro. Report final state.

With `--no-confirm`: treat any PRD proposals as auto-rejected (log + `sk specify --reject <id>`) rather than pausing.

## Per-turn output
End each turn with:
```
loop=N phase=X batch=[T-XX,T-YY] next=(continue|pause:reason|retro)
```

## Logging
Every decision-worthy event:
```bash
sk loop log "decision-slug" "one-paragraph rationale"
```

## Constitution reminders
- §III: snapshots auto-written by `sk loop settle` before state transitions
- §IV: `sk loop log` + all other `sk` state commands write decision-log entries
- §VII: PRD changes → `.prd-pending/` (human confirm); ERD/tasks → autonomous
- §VIII: technical ambiguity → decide, log `[MAJOR]` or `[routine]`, proceed
