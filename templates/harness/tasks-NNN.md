# Tasks — Iteration {{iteration_id}}

**Feature Slug**: `{{iteration_slug}}`
**Version**: 0.1
**Date**: {{created_date}}
**Status**: Draft for `/sk.go` Phase 3 dispatch
**Total tasks**: {{total_tasks}}
**Waves**: {{wave_count}}
**Source ERD**: `.skspec/.erd/plan-{{iteration_id}}.md`
**Source PRD**: `.skspec/prd/spec-{{iteration_id}}.md`
**Source test-plan**: `.skspec/tests/test-plan-{{iteration_id}}.md`

<!--
  sk Harness task-list template. Output path: `.skspec/.task/tasks-{{iteration_id}}.md`.
  Written by engineer + qa subagents during Phase 2 of `/sk.go` (or via
  `/sk.tasks` explicitly). The DAG parser (`sk_harness.dag.parser`) reads
  this file on every loop iteration; per-task JSON sidecars under
  `.skspec/.task/tasks-{{iteration_id}}/T-NN.json` are regenerated from it.

  Human edits to this file win over the sidecars (see ERD §8.2/§8.5).
-->

---

## Reading guide

Each task is **self-contained**: one subagent dispatch, bounded work (≤ 6 h),
1–5 output files. Fields follow the grammar below. `acceptance` IDs map to
`tests/test-plan-{{iteration_id}}.md` scenarios.

**Task grammar** (ERD §8.1):

- Each task begins at a `##` header of the form `T-NN: <title>` or `T-NNN: <title>`
- Fields are bullet-list items at depth 1 with `key: value` form
- `deps` and `outputs` are JSON arrays; `idempotent` is `true|false`
- Everything after the field block is free-form description (stored as `description`)
- Unknown fields are tolerated but logged as warnings

**Wave structure**: a wave is a **synchronization barrier** — all wave-N tasks
must complete before any wave-(N+1) task starts. Within a wave, the dispatcher
batches ready tasks honoring intra-wave deps up to `max_concurrency` (default 3).

**Idempotency convention**: `idempotent: true` means rerunning produces the
same outputs. `false` entries require a snapshot before dispatch so a failed
retry can be rolled back (ERD §9.3).

---

## Wave 1: [Wave title, e.g., Scaffolding] ({{wave_1_count}} tasks)

<!--
  ACTION REQUIRED: Replace these sample tasks with real ones for this iteration.
  Keep the bullet-list field format exactly — the DAG parser depends on it.
-->

### T-01: [Short task title]

- deps: []
- agent: general-purpose
- validator: code-reviewer
- idempotent: true
- outputs: ["path/to/output-1", "path/to/output-2"]
- acceptance: [SC-001, SM-01]
- estimate: S

[Free-form description: what this task does, which ERD sections it implements,
which tests it should satisfy, any OQ-N cross-references.]

### T-02: [Short task title]

- deps: ["T-01"]
- agent: general-purpose
- validator: tdd-guide
- idempotent: true
- outputs: ["path/to/output"]
- acceptance: [SM-02]
- estimate: M

[Description]

---

## Wave 2: [Wave title, e.g., Core infrastructure] ({{wave_2_count}} tasks)

### T-03: [Short task title]

- deps: ["T-02"]
- agent: general-purpose
- validator: code-reviewer
- idempotent: true
- outputs: ["path/to/output"]
- acceptance: [SC-002]
- estimate: S

[Description]

---

## Wave 3: [Wave title] ({{wave_3_count}} tasks)

<!-- Add more tasks as needed, following the same pattern. -->

---

## Dependencies & Execution Order

### Phase / Wave Dependencies

- **Wave 1**: No dependencies — can start immediately
- **Wave 2**: Depends on Wave 1 completion
- **Wave 3+**: Each depends on all prior waves; list explicit cross-wave task deps above

### Parallel Opportunities

- Tasks within a wave whose `deps` arrays don't reference siblings can run concurrently
- Ready-set computation: `{t | t.state == 'pending' ∧ all(d.state == 'done' for d in t.deps)}`
- Batch size: `min(|ready_set|, max_concurrency)` per loop iteration (ERD §9.1)

---

## Notes

- The engineer subagent writes this file; user edits win over regenerated sidecars
- Commit after each task or logical group; see ERD §10 for snapshot semantics
- Never delete task entries — archive by setting `state: cancelled` in `.progress/state.json` (Constitution §III)
- Add a task here when a subagent files a PRD proposal that, once accepted, implies new work
