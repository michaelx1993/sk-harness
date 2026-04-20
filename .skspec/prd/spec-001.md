# PRD — sk Harness MVP (Iteration 001)

**Version**: 0.3
**Status**: Draft, awaiting user signoff
**Date**: 2026-04-19
**Iteration slug**: `sk-harness-mvp`
**Authoring mode**: Discussion-driven, captured by Claude Code session on 2026-04-19

---

## 1. Background & Motivation

### 1.1 The gap in spec-kit
GitHub's [spec-kit](https://github.com/github/spec-kit) (a.k.a. speckit) provides an excellent SDD scaffolding: `/speckit.constitution`, `/speckit.specify`, `/speckit.clarify`, `/speckit.plan`, `/speckit.tasks`, `/speckit.implement`, `/speckit.analyze`, `/speckit.checklist`. But each command is a one-shot invocation — it lacks:

- **Cross-session state persistence**: pause work, resume tomorrow on a different machine
- **Active TPM scheduling**: a main agent that owns the project, not just a chain of one-off commands
- **Multi-role multi-agent collaboration**: dynamic specialist agents per phase
- **Dynamic plan/task adjustment**: re-evaluate ERD and tasks mid-execution as new information surfaces
- **Knowledge accumulation**: lessons learned in iteration N inform iteration N+1
- **Concurrent task execution**: DAG-aware batch dispatch instead of strictly serial implementation

### 1.2 What sk adds
sk is a fork of spec-kit that layers a **Harness** on top of the SDD substrate. The Harness owns project state, schedules subagents, persists snapshots, accumulates knowledge, and runs an outer TPM loop until a feature iteration is complete or paused.

---

## 2. Goals & Non-Goals

### 2.1 Goals (v1)
1. Preserve speckit's SDD discipline; only add behavior, never weaken it
2. Allow a solo developer to launch a multi-task feature implementation, walk away, come back, and resume cleanly
3. Make the TPM agent's reasoning fully observable through `decision-log.md`
4. Support iteration: the same project can absorb new requirements over time, with knowledge accumulating
5. Enable dynamic agent specialization based on the technical content of the work
6. Run safely overnight in headless mode (`claude -p`)

### 2.2 Non-Goals (v1)
- Team collaboration (locks, claim/release, conflict merge UI)
- Real multi-process concurrency (Task tool single-process is enough for v1)
- Web UI / dashboard
- CI/CD integration beyond headless invocation
- Cloud-hosted state (everything is filesystem-local + git-friendly)
- Cross-project shared state beyond manual `~/.claude/sk-knowledge/` promotion

---

## 3. Target Users & Scenarios

### 3.1 Primary user
A solo developer using Claude Code on a feature of moderate complexity (2–20 sub-tasks, 1–5 files of design surface, may span multiple sessions).

### 3.2 Top scenarios
1. **Bootstrap**: `/sk.init` a new project, write first PRD, let TPM design and implement
2. **Pause-resume**: Pause mid-iteration, restart Claude Code later, resume from snapshot
3. **Iteration 2+**: After shipping v1 of a feature, add a new requirement; TPM uses prior knowledge
4. **PRD-doubt mid-flight**: Agent discovers spec inconsistency, files a `.prd-pending/` proposal, user accepts/rejects
5. **Overnight run**: `claude -p '/sk.go --until-pause'` to make progress while user is asleep
6. **Debug a stuck task**: Use `/sk.step` and `/sk.tasks show` to inspect what an agent did

---

## 4. Core Concepts

| Concept | Definition | Persistence |
|---------|------------|-------------|
| **Project** | A workspace with a single `.skspec/` root. Long-lived. | `.skspec/` |
| **Iteration** | One full SDD cycle: spec → plan → tasks → implement → retro. Numbered `001`, `002`, … | `prd/spec-00N.md` + corresponding plan/tasks/test-plan |
| **PRD** | The product requirements doc for an iteration (user-owned, signed) | `prd/spec-00N.md` |
| **ERD** | Engineering / architecture / data design for an iteration (agent-owned, evolves) | `.erd/plan-00N.md` (+ `history/`) |
| **Task** | The smallest schedulable unit. Has deps, agent, validator. | `.task/tasks-00N.md` + per-task JSON |
| **Snapshot** | State captured at task completion (or manual checkpoint) | `.snapshot/iter-00N/<task>-<ts>.json` |
| **Progress** | Live state machine: active iteration, task states, batch info, pause flag | `.progress/state.json` |
| **Decision log** | Append-only narrative of every TPM decision and roster change | `.progress/decision-log.md` |
| **Knowledge** | Accumulated patterns, gotchas, decisions, retros (cross-iteration) | `.knowledge/` |
| **Agent roster** | Currently-active subagent specializations for this project | `.agents.json` |
| **Agent catalog** | Available subagent_types and their domains. Three-layer fallback. | `.agents-catalog.json` (project) > `~/.claude/sk-agent-catalog.json` (user) > `templates/agents-catalog.json` (built-in) |
| **TPM** | The general-purpose orchestrator subagent that drives the loop | Spawned per `/sk.go` invocation |

---

## 5. Functional Requirements

### 5.1 Project Initialization
- `/sk.init [name]` creates the `.skspec/` skeleton (all directories, stub state files, `.constitution.md` template, empty `.iterations.json`)
- Idempotent: rerunning detects existing `.skspec/` and offers to repair missing pieces only
- `.constitution.md` is interactive: prompts for project principles, tech stack hints, quality bar

### 5.2 Iteration Model
- **Serial only**: at most one iteration with `status: active` in `.iterations.json`
- Each iteration owns four documents (independent, no cross-iter merging):
  - `prd/spec-00N.md` (user-owned, requires user signoff to amend)
  - `.erd/plan-00N.md` (agent-owned, can rewrite freely with history snapshots)
  - `.task/tasks-00N.md` (agent-owned)
  - `tests/test-plan-00N.md` (user-owned baseline; QA agent can append-only via `.task/` artifacts but cannot mutate)
- `/sk.specify` rules:
  - No active iteration → starts iteration `00(N+1)` and drafts `spec-00(N+1).md`
  - Active iteration exists → defaults to `--amend` (writes proposal to `.prd-pending/`)
- `/sk.iteration.complete` finalizes: triggers retro subagents, writes `.knowledge/retrospectives/00N-retro.md`, sets status to `completed`, archives `.task/` to `.task/archive/00N/`

### 5.3 The TPM Master Loop (`/sk.go`)

Phase order per iteration:

**Phase 1 — ERD Design**
- Reads `prd/spec-00N.md` + `docs/` + `references/` + `.knowledge/` + historical `plan-*.md` (advisory)
- Dispatches `architect` subagent → drafts `.erd/plan-00N.md`
- Multi-role review (architect + engineer + security)
- Writes `evolution.md` entry explaining design choices

**Phase 2 — Task Decomposition**
- Reads `plan-00N.md` + `spec-00N.md` + `tests/test-plan-00N.md`
- Dispatches `engineer` + `qa` subagents → produces `.task/tasks-00N.md` with DAG (tasks have explicit `deps`)
- Generates per-task JSON sidecar: `id`, `title`, `deps`, `agent`, `validator`, `idempotent`, `outputs`

**Phase 3-4 — Micro Loop (the workhorse)**
Repeats until iteration complete or pause:

- **Step 0**: Reload `state.json`, reread `prd/`, `tests/`, `docs/`, `references/`
- **Step 1 — Agent Roster Reconciliation**: Scan `.erd/` and `.task/` content vs `.agents-catalog.json`, propose roster additions/deactivations, update `.agents.json`, log to `decision-log.md`. Bounded by `max_active_agents` (default 8)
- **Step 2 — Multi-Role Review**: Concurrent dispatch of `architect`, `qa`, `security`, `engineer` subagents. Each evaluates whether ERD/tasks/PRD still hold. (Disabled in initial loop iteration to avoid redundant work after Phase 1.)
- **Step 3 — Decision Branch** (first match wins):
  - (a) Failed task exceeded `max_retries` → escalate to user, pause
  - (b) ERD contradicted by code reality → rewrite `plan-00N.md` (snapshot to `history/`), regenerate affected tasks, continue
  - (c) Spec gap discovered → write `.prd-pending/proposal-<ts>.md`, pause until `/sk.specify --accept|reject`
  - (d) Deadlock (≥ 2 loops with empty `ready_set` but `pending` non-empty) → escalate, pause
  - (e) Tasks granularity wrong → adjust `tasks-00N.md`
  - (f) All clear → continue
- **Step 4 — Compute Ready Set**: `{t | t.state=pending ∧ all(d.state=done for d in t.deps)}`
- **Step 5 — Batch Dispatch**: Take `min(|ready_set|, max_concurrency)` tasks, fire concurrent Task tool calls in a single assistant turn
- **Step 6 — Settle**: Wait for all to complete. Per task: success → `state=done` + write snapshot; failure → `state=failed` + log + record retry counter
- **Step 7 — Knowledge Extraction**: For each task that surfaced something interesting (failed-then-succeeded, introduced new dep, changed ERD), dispatch `knowledge-extractor` subagent to append to `.knowledge/{patterns,gotchas,decisions}.md`
- **Step 8 — Termination Check**: All done → Phase 5; user paused → exit; deadlock → escalate; else → loop to Step 0

**Phase 5 — Retro & Iteration Close**
- Multi-role retro subagents (architect / qa / engineer / pm perspectives) concurrently
- Synthesize to `.knowledge/retrospectives/00N-retro.md`
- Update `.iterations.json` → `status: completed`, fill `completed_at`
- Archive `.task/tasks-00N.md` to `.task/archive/00N/`
- `/sk.go` exits

### 5.4 DAG Batch Concurrency
- `max_concurrency` configurable in `.agents.json` (default 3)
- Failure of one task in a batch does not abort sibling tasks
- Idempotency: each task declares `idempotent: true|false`. Non-idempotent retries require a `/sk.snapshot.restore` first (TPM auto-handles when possible, escalates if not)

### 5.5 Dynamic Agent Roster
- `.agents.json` is the live roster (status `active|inactive`, with `added_loop`, `rationale`, `subagent_type`)
- `.agents-catalog.json` is the candidate pool (three-layer fallback merge)
- Agent roster reconciliation runs every loop iteration (Step 1 above)
- Manual overrides:
  - `/sk.agent.add <role> [--type <subagent_type>]`
  - `/sk.agent.remove <role>`
  - `/sk.agent.lock <role>` (TPM cannot auto-modify locked entries) — v2

### 5.6 Knowledge Accumulation (three tiers)
- **Task tier (auto)**: `knowledge-extractor` runs after each notable task completion
- **Iteration tier (semi-auto)**: Phase 5 retro synthesizes per-iteration insights
- **Project tier (manual)**: `/sk.knowledge.promote` lifts an entry to `~/.claude/sk-knowledge/` for cross-project reuse — v2

### 5.7 PRD Reverse-Proposal Protocol
- Any subagent finding a spec gap MUST NOT silently work around it
- Instead: write `.prd-pending/proposal-<ts>.md` with `{problem, evidence, suggested_change, impact}`
- TPM enters `paused` with `pause_reason: prd_proposal`
- User reviews; runs `/sk.specify --accept` (merges into `spec-00N.md` + logs) or `--reject` (archives proposal)
- TPM resumes; if accepted, automatically re-runs Phase 1 review of ERD against new spec

### 5.8 Pause / Resume
- `/sk.pause`: sets `paused: true` in `state.json`. TPM finishes the current batch, then stops cleanly (does NOT interrupt in-flight subagents)
- `/sk.resume`: clears `paused`, resumes from Step 0 of next loop
- Granularity: **task-level**. A subagent that's currently executing will not be killed; the pause takes effect after its task settles
- `state.json.paused` is also set automatically when TPM hits `prd_proposal`, `deadlock`, or `max_retries_exceeded`

### 5.9 Failure Handling
- Per-task `retry_count`, bounded by `max_retries` (default 2)
- After max retries: state=`failed`, escalate (pause, decision-log entry)
- Deadlock detection: 2 consecutive loops with empty ready-set but non-empty pending → escalate
- All escalations land in `decision-log.md` with explicit user-action prompt

### 5.10 Headless Mode
- `claude -p '/sk.go --until-pause'` → runs to first natural pause (iteration done / `/sk.pause` was invoked / failure escalation / PRD proposal)
- `--no-confirm`: any PRD proposals are auto-rejected (logged) so the loop never blocks waiting for user
- Non-zero exit code if loop terminated due to escalation; zero if iteration completed cleanly

---

## 6. Command Surface (v1, 21 commands)

### 6.1 Setup
| Command | Effect |
|---------|--------|
| `/sk.init [name]` | Bootstrap `.skspec/` |
| `/sk.constitution` | Edit `.constitution.md` interactively |
| `/sk.config <show\|set\|edit>` | View/modify `.agents.json` config block |

### 6.2 SDD Documents (forked from speckit, file names suffixed `-00N`)
| Command | Effect |
|---------|--------|
| `/sk.specify [--amend\|--accept [id]\|--reject [id]]` | Draft / amend / approve / reject PRD |
| `/sk.clarify` | Q&A loop to refine current spec |
| `/sk.plan` | Manual ERD generation (also auto-triggered by `/sk.go` Phase 1) |
| `/sk.tasks` | Manual task decomposition (also auto in Phase 2) |
| `/sk.analyze` | Cross-document consistency check |
| `/sk.checklist` | Generate validation checklist |

### 6.3 Execution
| Command | Effect |
|---------|--------|
| `/sk.go [--until-pause] [--no-confirm]` | Start TPM master loop |
| `/sk.pause` | Graceful pause after current batch |
| `/sk.resume` | Resume from `state.json` |
| `/sk.step` | Run exactly one batch then pause (debug) |
| `/sk.review` | Force a review cycle without dispatching tasks |

### 6.4 Observation
| Command | Effect |
|---------|--------|
| `/sk.status` | Iteration + task counts + last decision summary |
| `/sk.tasks <list\|show <id>\|graph>` | Task introspection |
| `/sk.log [--tail N]` | Tail decision-log |

### 6.5 Iteration & Help
| Command | Effect |
|---------|--------|
| `/sk.iteration <list\|complete\|show <id>>` | Iteration lifecycle |
| `/sk.help [command]` | Help text |

### 6.6 Manual Override
| Command | Effect |
|---------|--------|
| `/sk.tasks.retry <id>` | Reset failed task to pending |
| `/sk.agent <list\|add\|remove>` | Roster manual control |

### 6.7 v2+ Deferred
`/sk.snapshot.*`, `/sk.knowledge.*`, `/sk.diff`, `/sk.lint`, `/sk.export`, `/sk.import`, `/sk.agent.catalog.*`, `/sk.agent.lock`, `/sk.tasks.add|skip|cancel`, standalone `sk` CLI.

---

## 7. Directory Structure (canonical)

```
.skspec/
├── prd/
│   ├── spec-001.md             # iteration N spec (user-owned)
│   ├── spec-002.md
│   └── ...
├── tests/
│   ├── test-plan-001.md        # user-owned acceptance + scenarios
│   └── ...
├── docs/                       # user-owned project conventions
├── references/                 # user-owned external links/snapshots
│
├── .version                    # schema version: "0.3.0"
├── .constitution.md            # ratified principles
├── .iterations.json            # iteration registry, active pointer
├── .agents.json                # live roster + concurrency config
├── .agents-catalog.json        # project-level catalog overlay
│
├── .erd/
│   ├── plan-001.md             # active design
│   ├── plan-002.md
│   ├── evolution.md            # narrative of cross-iter design changes (optional)
│   └── history/                # versioned snapshots of plan-*.md
├── .task/
│   ├── tasks-001.md            # current iteration task list (DAG)
│   ├── tasks-001/              # per-task JSON sidecars
│   │   ├── T-01.json
│   │   └── ...
│   └── archive/00N/            # completed iterations' task archives
├── .progress/
│   ├── state.json              # live state machine
│   ├── decision-log.md         # append-only TPM narrative
│   └── milestones.md           # iteration timeline
├── .snapshot/
│   └── iter-00N/<task>-<ts>.json
├── .knowledge/
│   ├── patterns.md
│   ├── gotchas.md
│   ├── decisions.md
│   └── retrospectives/00N-retro.md
└── .prd-pending/               # agent → user PRD-change proposals
    └── proposal-<ts>.md
```

**Invariant**: dot-prefixed names = agent-maintained; non-dot = user-maintained.

---

## 8. State & File Formats

### 8.1 `.iterations.json`
```json
{
  "version": 1,
  "active": "001",
  "iterations": [
    {
      "id": "001",
      "slug": "sk-harness-mvp",
      "status": "active",
      "started_at": "ISO-8601",
      "completed_at": null | "ISO-8601",
      "spec":  "prd/spec-001.md",
      "plan":  ".erd/plan-001.md",
      "tasks": ".task/tasks-001.md",
      "test_plan": "tests/test-plan-001.md"
    }
  ]
}
```

### 8.2 `.progress/state.json`
```json
{
  "version": 1,
  "active_iteration": "001",
  "phase": "phase-3-micro" | "phase-1-erd" | "phase-2-tasks" | "phase-5-retro" | "completed",
  "loop_count": 7,
  "last_updated": "ISO-8601",
  "tasks": [
    { "id": "T-01", "state": "done", "retries": 0, "snapshot": ".snapshot/iter-001/T-01-..." },
    { "id": "T-02", "state": "running", "retries": 0 },
    { "id": "T-03", "state": "pending", "retries": 0 }
  ],
  "current_batch": ["T-02"],
  "paused": false,
  "pause_reason": null | "user" | "prd_proposal" | "max_retries_exceeded" | "deadlock"
}
```

### 8.3 `.agents.json`
```json
{
  "version": 1,
  "max_concurrency": 3,
  "max_retries": 2,
  "max_active_agents": 8,
  "roster": [
    {
      "role": "tpm",
      "subagent_type": "general-purpose",
      "status": "active" | "inactive" | "locked",
      "added_loop": 0,
      "deactivated_loop": null | <int>,
      "rationale": "string"
    }
  ]
}
```

### 8.4 Per-task JSON sidecar `.task/tasks-00N/<id>.json`
```json
{
  "id": "T-07",
  "title": "Implement /sk.pause command",
  "deps": ["T-03", "T-05"],
  "agent": "implementer",
  "validator": "tdd-guide",
  "idempotent": true,
  "outputs": ["src/commands/pause.ts"],
  "state": "pending",
  "retries": 0
}
```

### 8.5 `tasks-00N.md` (human-readable mirror)
Markdown with one `## T-NN` header per task, fields parsable. Source of truth for human edits is the `.md`; sidecar JSONs are regenerated from it on `/sk.tasks` runs.

---

## 9. User Journey Scenarios (acceptance narratives)

### 9.1 Greenfield first iteration
```
$ cd new-project && claude
> /sk.init
> /sk.constitution     (interactive)
> /sk.specify          (drafts spec-001.md)
[user reviews spec-001.md, optionally edits]
> /sk.go
[Phase 1 → Phase 2 → Phase 3-4 loop → Phase 5 → exit]
```

### 9.2 Pause-resume across sessions
```
> /sk.go
[loop runs for 30 min, 5 batches deep]
> /sk.pause
[exits cleanly]
[next day]
$ claude
> /sk.status
> /sk.resume
```

### 9.3 PRD proposal mid-flight
```
[during /sk.go]
  ⚠ wrote .prd-pending/proposal-...md
  ⏸ paused
> cat .skspec/.prd-pending/proposal-...md
> /sk.specify --accept
  [merged into spec-00N.md, TPM rerun Phase 1 review of ERD]
  [resumed]
```

### 9.4 Iteration 2: adding a feature
```
> /sk.iteration.complete
  [retro written]
> /sk.specify
  [drafts spec-002.md, TPM has access to .knowledge/ history]
> /sk.go
```

### 9.5 Overnight headless
```
$ claude -p '/sk.go --until-pause --no-confirm' > sk.log
[wakes up, exits 0 if iteration done; non-zero on escalation]
```

### 9.6 Debug a stuck task
```
> /sk.step
> /sk.tasks show T-07
> /sk.log --tail 50
> /sk.tasks.retry T-07
```

---

## 10. Non-Functional Requirements

- **Git-friendly**: All persisted state is JSON or Markdown. Diffable. Mergeable (with care). No binary state files
- **Cross-platform**: macOS / Linux primary; Windows best-effort (WSL recommended)
- **No network for core flow**: state is filesystem-local; subagent calls go via Claude Code Task tool
- **Recoverable from partial corruption**: `/sk.lint` (v2) validates `.skspec/` integrity; manual file editing must not catastrophically break TPM
- **Bounded resource use**: `max_concurrency`, `max_retries`, `max_active_agents` all configurable upper bounds
- **Token budget visibility**: each subagent invocation logged with role + purpose; v2 may add token-cost tally
- **Schema versioning**: `.skspec/.version` allows future migration tooling

---

## 11. Fork Boundary with spec-kit

### 11.1 Inherited (unchanged in spirit)
- The eight slash commands' purpose and broad shape: `constitution`, `specify`, `clarify`, `plan`, `tasks`, `analyze`, `checklist`, `implement` (the last is largely subsumed by `/sk.go`)
- Markdown templates for spec / plan / tasks
- The `Specification → Plan → Tasks → Implementation` discipline

### 11.2 Renamed
- All `/speckit.*` → `/sk.*`
- Output directory `specs/<branch>/` → `.skspec/`
- File naming: `spec.md` → `spec-00N.md` (and same pattern for plan/tasks/test-plan)

### 11.3 Behavior changes
- `/sk.specify` enforces user-confirmation on amend (writes `.prd-pending/` for in-flight changes)
- `/sk.tasks` produces both `tasks-00N.md` (human) AND `.task/tasks-00N/<id>.json` sidecars (machine)
- `/sk.implement` is replaced by `/sk.go` master loop (the equivalent single-shot lives as Phase 3 logic)

### 11.4 Net new
- Harness commands: `/sk.go`, `/sk.pause`, `/sk.resume`, `/sk.step`, `/sk.review`, `/sk.status`, `/sk.iteration.*`, `/sk.tasks.retry`, `/sk.agent.*`, `/sk.config`, `/sk.log`, `/sk.help`, `/sk.init`
- All harness state files under `.skspec/.*`
- TPM agent + subagent prompt templates under `templates/agents/`

### 11.5 Upstream merge plan
- Watch upstream spec-kit for template improvements; rebase periodically
- Keep rename and `.skspec/` redirection isolated in a thin adaptation layer
- Harness commands live in entirely separate files so upstream conflicts are minimized

---

## 12. Locked Decisions (record from discussion)

| # | Decision | Choice |
|---|----------|--------|
| 1 | Relationship with spec-kit | **Fork** (not wrapper, not rewrite) |
| 2 | Interrupt granularity | **Task level** (no in-task pause) |
| 3 | Agent execution | **Claude Code Task tool** (single-process, parallel via batched tool calls) |
| 4 | PRD change authority | **User-confirm required**; ERD/tasks/knowledge are agent-autonomous |
| 5 | Directory naming | **`.skspec/`** as project root; agent-maintained dirs prefixed with `.` |
| 6 | Iteration model | **Serial**, each iteration owns independent spec/plan/tasks/test-plan |
| 7 | Task concurrency | **DAG batched**, default `max_concurrency=3` |
| 8 | Review cadence | **Every loop iteration** (lightweight read of plan + next batch) |
| 9 | `.agents.json` model | **Stateful roster** (status, added_loop, deactivated_loop, rationale) |
| 10 | Catalog source | **Three-layer fallback**: project > user > built-in |
| 11 | Knowledge tiers | feature-internal `.knowledge/` + (v2) global `~/.claude/sk-knowledge/` |
| 12 | TPM termination | All done / `/sk.pause` / 2 consecutive empty `ready_set` loops |
| 13 | `/sk.go` exit on iteration close | Yes; reopen with next `/sk.specify` |
| 14 | PRD reverse-proposal | **Plan A**: agent writes `.prd-pending/`, TPM pauses, user accepts/rejects |
| 15 | CLI vs slash | **Slash commands only in v1**; standalone `sk` CLI deferred to v2 |
| 16 | Headless mode | **v1 essential**: `--until-pause` and `--no-confirm` flags |
| 17 | Command prefix style | **Dot notation**: `/sk.tasks.retry`, `/sk.agent.add` |
| 18 | Self-bootstrap | **Yes**: iteration 001 of sk = "build sk" (this PRD) |

---

## 13. Out of Scope for v1
- Team collaboration features (locking, claim/release, multi-user state)
- Real multi-process concurrency
- Web UI / TUI dashboard
- CI/CD beyond headless invocation
- Cloud state storage
- Plugin system for third-party agent types beyond catalog edits
- Token-cost budget enforcement (visibility only)
- Standalone `sk` CLI binary
- Cross-iteration parallelism

---

## 14. Acceptance Criteria

See `tests/test-plan-001.md` for the full test scenarios. Summary:

- [ ] `/sk.init` produces canonical `.skspec/` structure
- [ ] `/sk.specify` writes `spec-001.md`; amend during active iteration writes to `.prd-pending/`
- [ ] `/sk.go` runs Phases 1–5 to completion on a trivial 3-task iteration
- [ ] `/sk.pause` followed by `/sk.resume` produces identical state and continues correctly
- [ ] DAG batching dispatches independent tasks concurrently (verifiable in `decision-log.md`)
- [ ] Agent roster reconciliation adds at least one specialist when ERD mentions a domain keyword
- [ ] `.prd-pending/` proposal flow: agent proposes → user accepts → spec updated → ERD re-reviewed
- [ ] Iteration 002 starts after `/sk.iteration.complete`; can read `.knowledge/` from iteration 001
- [ ] Headless `claude -p '/sk.go --until-pause'` exits 0 on clean completion
- [ ] All TPM decisions appear in `decision-log.md`

---

## 15. Open Questions (defer to retrospective or v2)

1. **Knowledge promotion automation**: Should high-confidence `.knowledge/` items auto-suggest promotion to `~/.claude/sk-knowledge/`?
2. **Subagent prompt customization**: Can users override the built-in `templates/agents/<role>.md` per project? (Probably yes; defer to v2.)
3. **Long-task progress streaming**: Should subagents be able to report progress mid-execution (without breaking task-level pause semantics)?
4. **`/sk.review` granularity**: Should manual review allow scoping to one role only?
5. **ERD evolution merge view**: Need a `/sk.diff` to render `plan-00N.md` vs `history/plan-00N-<ts>.md`?
6. **PRD proposal batching**: If multiple agents file proposals in a single batch, do they compose or conflict?

---

**End of PRD spec-001. Awaiting user signoff. Once signed, TPM proceeds to Phase 1 (ERD design for sk itself).**
