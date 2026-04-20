# PRD — Iteration 002: Harness Completion

**Version**: 0.1
**Status**: Draft, autonomously advanced (user authorized "continue until done")
**Slug**: harness-completion
**Date**: 2026-04-20

## 1. Background

Iteration 001 shipped the sk-harness MVP (27 tasks, 83.4% coverage, self-bootstrap working). The retro surfaced concrete carryovers. Iteration 002 closes those gaps so sk-harness is feature-complete relative to `spec-001.md §6`.

## 2. Goals

1. Implement the 7 skills not shipped in iter-001: `/sk-constitution`, `/sk-clarify`, `/sk-plan` (SDD variant), `/sk-analyze`, `/sk-checklist`, `/sk-step`, `/sk-review`, `/sk-config`
2. Split ERD-gap from PRD-gap routing: add `.erd-pending/` channel
3. Add reconnaissance subagent template so Phase 1 of iter-003+ reads external sources before architect drafts
4. Wire CLI subcommands for `step`, `review`, `config`, `erd-pending`
5. Ship a runnable demo that exercises `/sk-init` on a fresh dir and reports back

## 3. Non-goals

- Real `/sk-go` autonomous drive on a non-trivial iteration (deferred to iter-003; requires live Claude Code session outside the harness)
- Multi-process concurrency
- Web UI

## 4. Functional requirements

### 4.1 Missing skills
- `sk-constitution`: CLI-backed. Opens `.constitution.md` in `$EDITOR` if set, else prints path. Logs decision on exit.
- `sk-clarify`: delegates to Claude directly (user Q&A); SKILL.md provides the prompt.
- `sk-plan`: already shipped as drafting skill in iter-001; add CLI alias `sk plan` that runs a validation check on `.erd/plan-<N>.md` exists.
- `sk-analyze`: scans spec/plan/tasks/test-plan for cross-reference consistency. CLI-backed with pattern checks (e.g., tasks reference ERD §X that exists, acceptance IDs appear in test-plan).
- `sk-checklist`: generates a per-iteration checklist from the test-plan + task acceptance IDs.
- `sk-step`: sets a `step` flag in state so `/sk-go`'s next loop does one batch and then pauses.
- `sk-review`: writes a "review-requested" marker to decision-log and sets state.paused with a new reason `review_requested`.
- `sk-config`: view/set three values in `.agents.json`: `max_concurrency`, `max_retries`, `max_active_agents`.

### 4.2 `.erd-pending/` channel
- New directory `.skspec/.erd-pending/`
- New `file_erd_proposal` function mirroring `file_proposal` but targeting ERD
- Agent-autonomous acceptance: `accept_erd_proposal` snapshots current plan then appends (or inline-merges) without user confirmation. Logs decision.
- CLI: `sk erd-pending <list|accept|reject>`.

### 4.3 Reconnaissance subagent template
- New file `templates/harness/agents/recon.md`
- Role: read external sources (upstream repos, referenced URLs — the latter via other tools when available), produce a grounded "reality check" report for the architect to use
- Not CLI-invoked; dispatched by `/sk-go` Phase 1 before architect drafts ERD

### 4.4 Concrete acceptance scenarios added to test-plan
- New SM-100..SM-108 covering the above
- Self-bootstrap SM-5.1 is expanded: fresh-dir `/sk-init` → `sk status` → `sk tasks list` round-trip

## 5. Out of scope

- ERD proposals filed by users (the channel is agent-only; users still use `.prd-pending/` for user-facing surfaces)
- Per-user catalog overrides (keep three-layer fallback from iter-001)

## 6. Acceptance

See `tests/test-plan-002.md`. Short form:
- All 7 new skills present under `.claude/skills/sk-*/SKILL.md`
- CLI subcommands `step`, `review`, `config`, `erd-pending` callable
- `.erd-pending/` accept flow exercised by a test
- Recon template file exists and is referenced in the sk-go SKILL.md
- Overall test coverage ≥ 80%
