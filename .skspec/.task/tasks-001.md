# Tasks — Iteration 001 (sk Harness MVP)

**Version**: 0.1
**Date**: 2026-04-19
**Status**: Draft for /sk.go Phase 3 dispatch
**Total tasks**: 27
**Waves**: 6 (synchronization barriers — see §"Wave structure" below)
**Max DAG depth**: 11 (longest dep chain; achievable in 6 wave-batches via intra-wave sub-batching)
**Source ERD**: `.erd/plan-001.md` v0.1
**Source PRD**: `prd/spec-001.md` v0.3
**Source test-plan**: `tests/test-plan-001.md`

---

## Reading guide

Each task is self-contained: one subagent dispatch, ≤6h focused work, 1–5 output files. Fields are bullet lists per the grammar in ERD §8.1. `acceptance` IDs map to `tests/test-plan-001.md` scenarios; missing-coverage proposals are flagged in the engineer-subagent's report (decision-log).

**Wave structure**: a wave is a synchronization barrier — all wave N tasks must complete before any wave N+1 task starts. **Within a wave**, the dispatcher (PRD §5.4 max_concurrency=3) batches tasks honoring intra-wave deps. Several waves contain small intra-wave dep chains (e.g., Wave 2 has `T-04 → T-05`) which the dispatcher resolves with multiple sub-batches inside one wave.

**Idempotency convention**: `idempotent: true` means rerunning produces the same outputs. The only `false` entry is **T-26** (self-bootstrap verification), because it runs `/sk.status` and `/sk.iteration.complete` against the live `.skspec/`, which appends to the decision-log and may write to `.knowledge/decisions.md` — both non-invertible.

**ERD open questions** OQ-1..OQ-9 are referenced inline where the task touches them; the implementing subagent must follow the architect's recommendation or escalate via `.prd-pending/proposal-<ts>.md`.

**Constitution §IV note**: every command-implementing task (T-19..T-23) MUST call `decision_log.append_decision` from the writer in T-06 before any user-visible side effect; this is restated in each task's description.

---

## Wave 1: Scaffolding (3 tasks)

### T-01: Fork spec-kit, pin upstream SHA, write UPSTREAM.md

- deps: []
- agent: general-purpose
- validator: code-reviewer
- idempotent: true
- outputs: ["docs/UPSTREAM.md", "speckit/", "templates/upstream/", "LICENSE"]
- acceptance: SM-01, OBS-01
- estimate: M

Implements ERD §1. Clones `github/spec-kit` at tip of `main`, copies `speckit/` and `templates/upstream/` verbatim into the sk repo, inherits LICENSE, and writes `docs/UPSTREAM.md` recording the pinned commit SHA, fork date, and merge cadence per ERD §1.4. References OQ-1 (fork pinning); follow architect recommendation A (tip-of-main + pin SHA) unless user has overridden via `.knowledge/decisions.md`. Appends a decision-log entry with the SHA before completion (Constitution §IV — note: this entry is added by the implementing subagent, not by `decision_log.py` which doesn't exist yet).

### T-02: Scaffold sk_harness package and pyproject.toml

- deps: ["T-01"]
- agent: general-purpose
- validator: python-reviewer
- idempotent: true
- outputs: ["pyproject.toml", "uv.lock", "sk_harness/__init__.py", "sk_harness/__main__.py", "tests/conftest.py"]
- acceptance: SM-01
- estimate: S

Implements ERD §2 and §3. Creates `sk_harness/` Python package with `__init__.py` (declaring `__version__` and `schema_version = "0.3.0"` per ERD §15.1), `__main__.py` stub for `python -m sk_harness`, and `pyproject.toml` declaring Python 3.11+ and the seven runtime deps from ERD §2.4 (pydantic>=2, ruamel.yaml, filelock, rich, networkx, jsonschema, click). Generates `uv.lock`, sets up `pytest --cov=sk_harness --cov-fail-under=80` per ERD §14.5, and creates an empty `tests/conftest.py`. No business logic.

### T-03: Set up templates/harness/ stubs and skspec-skeleton blueprint

- deps: ["T-01"]
- agent: general-purpose
- validator: code-reviewer
- idempotent: true
- outputs: ["templates/harness/spec-NNN.md", "templates/harness/plan-NNN.md", "templates/harness/tasks-NNN.md", "templates/harness/test-plan-NNN.md", "templates/harness/skspec-skeleton/.gitkeep"]
- acceptance: SM-01, SM-02
- estimate: S

Implements ERD §3 templates layout. Creates the four `-NNN.md` template files by copying upstream `spec.md`/`plan.md`/`tasks.md` and renaming the title block per ERD §1.3 (manual one-off; the runtime `rename_artifact` helper comes in T-11). Creates `templates/harness/skspec-skeleton/` directory tree mirroring PRD §7's canonical layout (empty `.gitkeep` files in each agent-owned directory) for `/sk.init` to copy via T-19.

---

## Wave 2: State, observability, paths, parser, templating foundations (8 tasks)

This wave intentionally includes intra-wave dependencies (T-04 → T-05/T-06/T-08; T-07 → T-11). The dispatcher will execute as multiple sub-batches honoring deps. All eight tasks finish before Wave 3 begins.

### T-04: Define pydantic state models and JSON schemas

- deps: ["T-02"]
- agent: general-purpose
- validator: python-reviewer
- idempotent: true
- outputs: ["sk_harness/state/__init__.py", "sk_harness/state/models.py", "sk_harness/state/schemas/iterations.schema.json", "sk_harness/state/schemas/agents.schema.json", "sk_harness/state/schemas/state.schema.json", "sk_harness/state/schemas/task.schema.json"]
- acceptance: SM-01, SM-32, INT-20
- estimate: M

Implements ERD §3 state subtree and §7.4 validation. Pydantic models for `IterationsFile`, `AgentsFile` (incl. `RosterEntry` + status enum), `StateFile` (incl. `TaskState`, `pause_reason` enum, `runtime_flags`), and `TaskDef`. Mirrors PRD §8.1–§8.4 field-for-field. Generates four `jsonschema` files used by `load_validated`. Models must round-trip via `.model_dump_json(indent=2, sort_keys=True)` byte-identically (ERD §7.1). Writes table-driven unit tests per `tdd-guide` discipline; coverage target 80%.

### T-05: Atomic IO, cooperative lock, load_validated

- deps: ["T-04"]
- agent: general-purpose
- validator: tdd-guide
- idempotent: true
- outputs: ["sk_harness/state/io.py", "tests/unit/test_state_io.py"]
- acceptance: SM-32, INT-20
- estimate: M

Implements ERD §7.1–§7.4. Exports `atomic_write_json(path, data)` (validate→tempfile→fsync→rename), `atomic_write_text(path, text)` for markdown, `load_validated(path) -> BaseModel` (schema lookup by path pattern, raises `SchemaViolationError` with line diagnostics), `acquire_lock(timeout=5)` and `acquire_pause_flag()` (ERD §7.2 side-channel `.skspec/.pause-requested`). **Resolves OQ-4 per architect recommendation A** (ship the lock). Unit tests use `tmp_path` and assert atomic-write crash-safety (write half a tempfile then assert original intact).

### T-06: Decision-log writer and event schema

- deps: ["T-04"]
- agent: general-purpose
- validator: tdd-guide
- idempotent: true
- outputs: ["sk_harness/observability/__init__.py", "sk_harness/observability/decision_log.py", "sk_harness/observability/events.py", "tests/unit/test_decision_log.py"]
- acceptance: OBS-01, OBS-02, OBS-03, OBS-04, OBS-05
- estimate: M

Implements ERD §16. `decision_log.append_decision(iter, loop, actor, decision, rationale, metadata=None)` opens `decision-log.md` in append mode and fsyncs (ERD §16.1). `events.py` defines the event-type enum (LOOP_START, ROSTER_CHANGE, BATCH_DISPATCH, TASK_TRANSITION, SNAPSHOT_TAKEN, ERD_REWRITE, PRD_PROPOSAL, PAUSE, ITERATION_START, ITERATION_COMPLETE, SCHEMA_MISMATCH per ERD §16.4) and the `TaskResult` pydantic envelope (ERD §5.4). Heading format must match ERD §16.3 byte-for-byte so `/sk.log --tail N` parses reliably. **Every command-implementing task in Waves 4–6 calls this writer**; do not skip the byte-format tests.

### T-07: Paths resolver, constants, schema-version check

- deps: ["T-02"]
- agent: general-purpose
- validator: python-reviewer
- idempotent: true
- outputs: ["sk_harness/paths.py", "sk_harness/constants.py", "sk_harness/state/migrations.py", "tests/unit/test_paths.py"]
- acceptance: INT-20
- estimate: S

Implements ERD §3 + §15. `paths.py` exports `skspec_root()`, `state_json()`, `iterations_json()`, `agents_json()`, `decision_log()`, `snapshot_dir(iter)`, `task_archive_dir(iter)`, `prd_pending_dir()` etc. — every fixed path in the canonical layout (PRD §7) goes here, never hard-coded elsewhere. `constants.py` holds defaults (`MAX_CONCURRENCY=3`, `MAX_RETRIES=2`, `MAX_ACTIVE_AGENTS=8`, `LOCK_TIMEOUT=5`, `EXIT_CODE_*` per ERD §13.3 OQ-6 recommendation A). `migrations.py` ships the empty migration registry plus `is_compatible(actual, expected)` per ERD §15.2 (same major.minor → ok). Zero migrations land in v1 by design; the registry exists so v2 authors don't invent it ad hoc.

### T-08: DAG markdown parser and JSON sidecar generator

- deps: ["T-04"]
- agent: general-purpose
- validator: tdd-guide
- idempotent: true
- outputs: ["sk_harness/dag/__init__.py", "sk_harness/dag/parser.py", "sk_harness/dag/grammar.py", "tests/unit/test_dag_parser.py"]
- acceptance: SM-15, INT-02
- estimate: M

Implements ERD §8.1–§8.5. `parser.parse_tasks_md(path) -> list[TaskDef]` per the grammar in §8.1; tolerates unknown fields, coerces single-string `deps` to `[deps]` with warning (§8.4). `parser.write_sidecars(tasks, dir)` regenerates `.task/tasks-001/T-NN.json` files with `_generated_from` and `_generated_at` markers per §8.2. `parser.diff_against_sidecars(tasks, dir)` powers the resync flow in §8.5 (added/removed/dep-mutated). `grammar.py` is a pure-doc module describing the grammar for users. Unit tests cover happy path + every error case in §8.4 (cycle, dangling dep, malformed field, empty file). Note: cycle detection itself comes from T-09's `graph.detect_cycle`; this task only validates field shapes.

### T-09: DAG graph, ready-set, cycle detection, topo sort

- deps: ["T-08"]
- agent: general-purpose
- validator: tdd-guide
- idempotent: true
- outputs: ["sk_harness/dag/graph.py", "tests/unit/test_dag_graph.py"]
- acceptance: SM-20, SM-21, SM-22, SM-43, INT-10
- estimate: S

Implements ERD §3 dag/graph and ERD §9.4 (ready-set semantics). Thin networkx wrapper exposing `build_graph(tasks)`, `ready_tasks(graph, state) -> list[TaskDef]`, `detect_cycle(graph) -> list[str] | None`, `topo_levels(graph)` (used by `/sk.tasks graph` rendering in T-22). Cycle-detection unit test uses the ERD §8.4 `CyclicTaskGraphError` shape. Ready-set test asserts |ready_set|=3 dispatches 3 even when `max_concurrency=10` (INT-10).

### T-11: speckit_adapter and templating engine

- deps: ["T-07"]
- agent: general-purpose
- validator: python-reviewer
- idempotent: true
- outputs: ["sk_harness/speckit_adapter.py", "sk_harness/templating.py", "tests/unit/test_templating.py"]
- acceptance: SM-10, SM-71, SM-72
- estimate: M

Implements ERD §1.3, §4.2, and §6.4. `speckit_adapter` is the **single** module that knows upstream paths: exports `resolve_upstream_command(sk_name) -> Path`, `rename_artifact(src, iteration) -> Path` (handles `spec.md → spec-00N.md`, `specs/<branch>/ → .skspec/prd/`), and `inherit_body(upstream_md, harness_header) -> str`. `templating.render_agent_prompt(role, context) -> str` uses `string.Template.safe_substitute` with the variable set in ERD §6.2 (zero-deps choice; no Jinja2). `templating.render_skeleton(target_dir)` copies `templates/harness/skspec-skeleton/` to a target while creating any missing parents (used by T-19 for `/sk.init`). Unit tests assert the variable list is exhaustive (no `${unbound}` in any rendered prompt with the §6.2 context dict). Note: this task only needs `paths` (T-07); template *files* themselves (T-12/T-13) need not exist yet — those tests use fixture templates in `tests/fixtures/`.

### T-27: CI configuration and lint baseline

- deps: ["T-02"]
- agent: general-purpose
- validator: code-reviewer
- idempotent: true
- outputs: [".github/workflows/test.yml", ".github/workflows/lint.yml", "ruff.toml", ".gitignore"]
- acceptance: SM-01
- estimate: S

GitHub Actions matrix (Python 3.11/3.12/3.13 per ERD §2.1) running `pytest --cov=sk_harness --cov-fail-under=80` (ERD §14.5). `ruff` for formatting/linting; `mypy` optional in v1 (revisit in v2). `.gitignore` excludes `__pycache__/`, `*.pyc`, `.pytest_cache/`, `.coverage`, `dist/`, `build/`, but preserves `.skspec/` (the project's working artifact must be tracked). **Resolves OQ-7 per architect recommendation A** (no real Task-tool calls in CI; nightly manual smoke). Placed in Wave 2 because the workflow only needs the `pyproject.toml` to exist; tests run as they get added across subsequent waves.

---

## Wave 3: Snapshots, agent templates, PRD merge, roster (5 tasks)

### T-10: Snapshot serializer and restore

- deps: ["T-05", "T-06"]
- agent: general-purpose
- validator: tdd-guide
- idempotent: true
- outputs: ["sk_harness/snapshots/__init__.py", "sk_harness/snapshots/serializer.py", "sk_harness/snapshots/restore.py", "tests/unit/test_snapshot.py"]
- acceptance: SM-32, INT-03, INT-11
- estimate: M

Implements ERD §10. `serializer.capture(task_id, captured_before, iter)` writes `.snapshot/iter-00N/<task>-<ts>.json` per §10.1 schema, including `state_json`, `agents_json`, `iterations_json`, `workspace_diff` (subprocess `git diff` against HEAD, truncated at 1MB per OQ-5 recommendation A with explicit `diff_truncated_at` marker). `restore.restore(path)` follows §10.5 (validate version, atomic-write the three JSON files, prompt before applying `workspace_diff`, log the restore). v1 exposes these as TPM-internal only (§10.5; no `/sk.snapshot.*` user command). Round-trip unit test captures, mutates state, restores, asserts byte-equality.

### T-12: Core subagent templates (_base, tpm, architect, engineer, qa, security)

- deps: ["T-11"]
- agent: general-purpose
- validator: code-reviewer
- idempotent: true
- outputs: ["templates/harness/agents/_base.md", "templates/harness/agents/tpm.md", "templates/harness/agents/architect.md", "templates/harness/agents/engineer.md", "templates/harness/agents/qa.md", "templates/harness/agents/security.md"]
- acceptance: SM-20, SM-24, OBS-05
- estimate: L

Implements ERD §5.2 (the TPM prompt skeleton verbatim) and §6.3 entries 1–6. `_base.md` defines the envelope format (ERD §5.4 `--- sk-result-begin ---`), the "never mutate user-owned files" rule (Constitution §II), and the logging contract. `tpm.md` implements the Step 0..8 micro-loop per ERD §5.2; `${output_envelope_spec}` is interpolated from `_base.md`. The other four roles inherit `_base` and add role-specific instructions. **Resolves OQ-2 per architect recommendation A** (single TPM per `/sk.go`). All templates use `${var}` placeholders matching ERD §6.2; T-11's tests should be re-run after this lands to confirm no unbound variables.

### T-13: Auxiliary subagent templates and built-in agents-catalog

- deps: ["T-11"]
- agent: general-purpose
- validator: code-reviewer
- idempotent: true
- outputs: ["templates/harness/agents/knowledge-extractor.md", "templates/harness/agents/retro.md", "templates/agents-catalog.json", "tests/unit/test_agent_templates.py"]
- acceptance: SM-50, SM-70, SM-72
- estimate: M

Implements ERD §6.3 entries 7–8 plus the built-in catalog layer (PRD §4 catalog three-layer fallback). `knowledge-extractor.md` defines append rules for `.knowledge/{patterns,gotchas,decisions}.md`. `retro.md` is multi-perspective: same template instantiated 4x with `${perspective}` ∈ {architect, qa, engineer, pm} per ERD §12.3. `templates/agents-catalog.json` is the built-in catalog (lowest precedence) listing every subagent_type sk knows about; project-level `.agents-catalog.json` overrides this. Tests assert that every catalog domain keyword is matched by at least one ERD-mentioned scenario (otherwise reconciliation can't pick it).

### T-17: PRD proposal/merge engine and knowledge extractor

- deps: ["T-05", "T-06"]
- agent: general-purpose
- validator: tdd-guide
- idempotent: true
- outputs: ["sk_harness/prd/__init__.py", "sk_harness/prd/proposal.py", "sk_harness/prd/merge.py", "sk_harness/knowledge/__init__.py", "sk_harness/knowledge/extractor.py", "tests/unit/test_prd_merge.py"]
- acceptance: SM-11, SM-12, SM-13, SM-60, SM-61, SM-62, SM-63
- estimate: L

Implements ERD §11 (PRD diff & merge engine) and §6.3 entry 7 (knowledge extractor support). `proposal.write_proposal(filed_by_role, filed_by_task, problem, evidence, suggested_change, impact)` writes `.prd-pending/proposal-<ts>.md` per ERD §11.1 frontmatter. `merge.accept(id)` runs the full §11.2 algorithm (lock, snapshot, apply diff via `git apply --3way`, atomic write, archive proposal, schedule `post_merge_rerun=phase-1` flag, log). `merge.reject(id, reason)` per §11.3. **Resolves OQ-8 per architect recommendation A** (serialize by filed_at, refuse overlapping accepts with `OverlappingProposalError`; SM-63). `knowledge/extractor.py` provides the helpers the `knowledge-extractor` subagent calls to append to `.knowledge/{patterns,gotchas,decisions}.md` with dedup-by-content-hash so a re-run doesn't duplicate entries.

### T-16: Multi-role review, roster reconciliation, termination check

- deps: ["T-09", "T-13"]
- agent: general-purpose
- validator: tdd-guide
- idempotent: true
- outputs: ["sk_harness/loop/__init__.py", "sk_harness/loop/review.py", "sk_harness/loop/roster.py", "sk_harness/loop/termination.py", "tests/unit/test_roster.py", "tests/unit/test_termination.py"]
- acceptance: SM-24, SM-43, SM-50, SM-51, SM-52, SM-53
- estimate: L

Implements ERD §3 loop subtree (review, roster, termination). `review.run_review(loop_n)` is a *coordinator stub* in this task; the actual subagent dispatch happens via T-15's runner (later wave). `roster.reconcile(erd_path, tasks_path, current_roster, catalog) -> RosterDelta` implements the algorithm per PRD §5.5 + ERD's three-layer catalog merge (project > user > built-in); honors `max_active_agents=8` with deactivation-of-lowest-priority swap (SM-53). `termination.check(state) -> Termination` detects deadlock (≥2 consecutive empty `ready_set` loops with non-empty `pending`), iteration-complete (all done), and escalation. Unit tests cover SM-50 keyword-trigger (ERD adds "PostgreSQL" → adds `database-reviewer`) and SM-51 deactivation-after-2-quiet-loops. **Note: this task creates `sk_harness/loop/__init__.py` to anchor the subpackage; T-14 adds the remaining loop modules.**

---

## Wave 4: Loop integration, dispatcher, headless, init command (5 tasks)

### T-14: Phase entry points and micro-loop state machine

- deps: ["T-09", "T-10", "T-12", "T-16"]
- agent: general-purpose
- validator: tdd-guide
- idempotent: true
- outputs: ["sk_harness/loop/phases.py", "sk_harness/loop/micro_loop.py", "tests/unit/test_micro_loop.py"]
- acceptance: SM-20, SM-23, SM-43, OBS-01
- estimate: L

Implements ERD §5.3, §9.1, and PRD §5.3 Steps 0..8 + Phase 1/2/5 entry points. `phases.py` exposes `run_phase_1_erd()`, `run_phase_2_tasks()`, `run_phase_5_retro()` (each invokes the corresponding subagent via the `AgentRunner` from T-15 — circular by design, broken with a Protocol). `micro_loop.py` is the heart: a pure-Python state machine driven by `state.json` that decides next action (continue / pause / iteration_complete / escalate). Each Step 0..8 transition appends to decision-log via T-06 (Constitution §IV). Logic split from dispatcher (T-15) so unit tests can drive it without a Task-tool mock.

### T-15: Batch dispatcher with AgentRunner protocol

- deps: ["T-09", "T-11", "T-12"]
- agent: general-purpose
- validator: tdd-guide
- idempotent: true
- outputs: ["sk_harness/loop/dispatcher.py", "tests/unit/test_dispatcher.py", "tests/fixtures/mock_runner.py"]
- acceptance: SM-20, SM-21, SM-22, INT-10, INT-11
- estimate: M

Implements ERD §9 and §14.3. Defines the `AgentRunner(Protocol)` interface (ERD §14.3) so the production impl talks to Claude Code's Task tool while tests use `mock_runner.py` reading pre-recorded responses keyed by `(subagent_type, task_id)`. `dispatcher.dispatch_batch(ready, max_concurrency, runner)` enforces failure isolation (ERD §9.2), non-idempotent retry handling via snapshot.restore (ERD §9.3 — references T-10), and per-task envelope parsing (ERD §5.4 — calls into T-06). Unit tests use the mock runner; one test asserts `max_concurrency=1` forces strict serial dispatch (SM-22), another asserts |ready|=3 fully dispatches even with `max_concurrency=10` (INT-10).

### T-18: Headless mode runner

- deps: ["T-07", "T-14", "T-15", "T-17"]
- agent: general-purpose
- validator: tdd-guide
- idempotent: true
- outputs: ["sk_harness/headless/__init__.py", "sk_harness/headless/runner.py", "tests/unit/test_headless.py"]
- acceptance: SM-80, SM-81, SM-82
- estimate: M

Implements ERD §13. Plumbs `--until-pause` and `--no-confirm` flags into `state.json.runtime_flags` so any subagent re-reading state observes them (ERD §13.2). Implements the exit-code table from ERD §13.3 (OQ-6 recommendation A: 0 clean / 1 error / 2 max_retries / 3 deadlock / 4 prd_proposal-without-no-confirm). No `input()` anywhere on the headless code path (§13.4); all PRD-class confirmations respect `--no-confirm`. Unit tests cover SM-80/81/82 via the mock_runner from T-15. Designed as a library module so it can be invoked from both `/sk.go --until-pause` (T-21) and `claude -p` headless sessions (PRD §5.10).

### T-19: /sk.init + sk.constitution + sk.config + cli root

- deps: ["T-03", "T-05", "T-06", "T-07", "T-11"]
- agent: general-purpose
- validator: tdd-guide
- idempotent: true
- outputs: [".claude/commands/sk.init.md", ".claude/commands/sk.constitution.md", ".claude/commands/sk.config.md", "sk_harness/cli.py", "tests/integration/test_init_command.py"]
- acceptance: SM-01, SM-02, SM-03, OBS-10
- estimate: M

Setup commands per PRD §6.1. `/sk.init` copies `templates/harness/skspec-skeleton/` (T-11's `render_skeleton`) to the cwd, populates stub state files with schema-validated defaults from T-04, idempotent on rerun (PRD §5.1 — repair-only mode for SM-02). `/sk.constitution` opens `.constitution.md` for interactive edit. `/sk.config` exposes `show|set|edit` modes against `.agents.json`. `cli.py` is the click-based dispatch root that all `/sk.*` command bodies invoke; emits `SK:` JSON-prefixed structured output per ERD §4.4. **Each command body invokes `decision_log.append_decision` before exit** (Constitution §IV). **Resolves OQ-3 per architect recommendation A** (use `allowed-tools` + `$ARGUMENTS` Claude Code frontmatter); if Claude Code does not support this frontmatter, the implementer MUST file a `.prd-pending/proposal-<ts>.md` rather than silently fall back. Integration tests use a temp cwd and assert the canonical layout (PRD §7) is reproduced byte-for-byte.

### T-20: /sk.specify + sk.clarify + sk.plan + sk.tasks + sk.analyze + sk.checklist

- deps: ["T-08", "T-11", "T-17", "T-19"]
- agent: general-purpose
- validator: tdd-guide
- idempotent: true
- outputs: [".claude/commands/sk.specify.md", ".claude/commands/sk.clarify.md", ".claude/commands/sk.plan.md", ".claude/commands/sk.tasks.md", ".claude/commands/sk.analyze.md", ".claude/commands/sk.checklist.md", "tests/integration/test_specify_flow.py"]
- acceptance: SM-10, SM-11, SM-12, SM-13, SM-14, SM-15, SM-71
- estimate: L

SDD documents per PRD §6.2. `/sk.specify` enforces the `--amend|--accept|--reject` semantics (PRD §5.2 + §5.7) by delegating to T-17's `prd.proposal/merge`. The five inherited commands (clarify/plan/tasks/analyze/checklist) use T-11's `inherit_body` to delegate to upstream `speckit/*` bodies with path rewrites. `/sk.tasks` runs the parser from T-08 against the current iteration's `tasks-00N.md` and regenerates sidecars. `/sk.plan` and `/sk.tasks` refuse with explicit error if their prerequisite is missing (SM-14, SM-15). Each command body calls `decision_log.append_decision` (Constitution §IV). Integration test covers SM-10..SM-13 SDD flow.

---

## Wave 5: Execution + observation + override commands (4 tasks)

### T-21: /sk.go + sk.pause + sk.resume + sk.step + sk.review

- deps: ["T-14", "T-15", "T-16", "T-18", "T-19"]
- agent: general-purpose
- validator: tdd-guide
- idempotent: true
- outputs: [".claude/commands/sk.go.md", ".claude/commands/sk.pause.md", ".claude/commands/sk.resume.md", ".claude/commands/sk.step.md", ".claude/commands/sk.review.md", "tests/integration/test_go_pause_resume.py"]
- acceptance: SM-20, SM-22, SM-23, SM-24, SM-30, SM-31, SM-33
- estimate: L

Execution commands per PRD §6.3. `/sk.go` boots the TPM subagent with template from T-12, runs `phases.run_phase_1` then `phase_2` then enters `micro_loop.run` (T-14) with the dispatcher from T-15 and termination from T-16. Accepts `--until-pause` and `--no-confirm` per ERD §13.2 by handing off to T-18's `headless.runner`. `/sk.pause` writes `.skspec/.pause-requested` (ERD §7.2 side-channel) so the lock-holder picks it up at next Step 0. `/sk.resume` clears the pause flag and re-enters the loop. `/sk.step` runs exactly one batch then exits with `pause_reason: user` (SM-23). `/sk.review` invokes T-16 `review.run_review` without dispatching tasks (SM-24). Each command body calls `decision_log.append_decision` on entry (Constitution §IV). Integration test covers SM-30/31 round-trip and asserts byte-equal `state.json` before and after pause→resume per the engineer-flagged proposal SM-31a (see report).

### T-22: /sk.status + sk.log + sk.iteration + sk.help

- deps: ["T-06", "T-09", "T-17", "T-19"]
- agent: general-purpose
- validator: tdd-guide
- idempotent: true
- outputs: [".claude/commands/sk.status.md", ".claude/commands/sk.log.md", ".claude/commands/sk.iteration.md", ".claude/commands/sk.help.md", "tests/integration/test_observation.py"]
- acceptance: SM-70, SM-71, SM-73, OBS-10, OBS-11, OBS-12
- estimate: M

Observation + iteration lifecycle per PRD §6.4 + §6.5. `/sk.status` renders task-counts + current-batch + last-decision via `rich`. `/sk.log --tail N` parses `decision-log.md` by counting `##` headings (relies on T-06 byte-format guarantee). `/sk.tasks list|show|graph` (mode-dispatched inside one file body) — `graph` uses T-09's `topo_levels` to render mermaid/ASCII (OBS-12). `/sk.iteration list|show|complete` implements ERD §12.1 lifecycle: refuses `complete` if any tasks pending/failed without `--force` (SM-73); on success, dispatches Phase 5 retro via T-17 (knowledge extractor + retro template), archives `.task/tasks-00N.md` to `.task/archive/00N/` (SM-70), updates `.iterations.json`. `/sk.help` is static text per command. **Note: `/sk.tasks` mode dispatch shares its file with T-20**; this task only adds the `list|show|graph` modes via the shared dispatch table in `cli.py`. Each command body calls `decision_log.append_decision` (Constitution §IV).

### T-23: /sk.tasks.retry + sk.agent

- deps: ["T-16", "T-19"]
- agent: general-purpose
- validator: tdd-guide
- idempotent: true
- outputs: [".claude/commands/sk.tasks.retry.md", ".claude/commands/sk.agent.md", "tests/integration/test_overrides.py"]
- acceptance: SM-42, SM-52
- estimate: S

Manual override commands per PRD §6.6. `/sk.tasks.retry <id>` resets `retry_count=0` and `state=pending` for the named task; refuses if iteration not active or task not found. `/sk.agent list|add|remove` exposes T-16 roster operations to the user; manually-added entries are tagged `_manually_added: true` so reconciliation treats them as advisory (SM-52). Each call appends to decision-log (Constitution §IV). Integration test covers SM-42 (retry resets state) and SM-52 (manual add survives reconciliation).

### T-24: Golden-path integration tests

- deps: ["T-15", "T-16", "T-17", "T-18"]
- agent: general-purpose
- validator: tdd-guide
- idempotent: true
- outputs: ["tests/integration/test_micro_loop_goldens.py", "tests/fixtures/mock_task_responses/", "tests/fixtures/golden_iterations/", "tests/fixtures/skspec_skeleton/"]
- acceptance: SM-20, SM-21, SM-40, SM-41, SM-43, SM-60, SM-61, SM-62, SM-30, SM-31
- estimate: L

Implements ERD §14.4. Five golden integration tests covering: (1) trivial 3-task iteration end-to-end at the **module layer** (SM-20 — uses `phases.run_phase_*` + `micro_loop.run` directly, not slash commands); (2) parallelizable 1→{2,3}→4 DAG batches T-02/T-03 together (SM-21); (3) failure+retry with fail-fail-fail sequence reaching `max_retries_exceeded` (SM-40, SM-41); (4) PRD proposal flow: subagent files proposal → pause → simulated `merge.accept` → resume + ERD re-review (SM-60..SM-62); (5) pause-resume serialization byte-equal round-trip (SM-30, SM-31). Each golden ships with its `mock_task_responses/` keyed responses and `golden_iterations/` expected `.skspec/` snapshot. Together with all unit tests from Waves 2–4, this task proves coverage ≥80% (ERD §14.5) — runs `pytest --cov=sk_harness --cov-fail-under=80` as part of acceptance. **Placed in Wave 5 (parallel with T-21..T-23) because it tests the module layer; no slash-command files are required**.

---

## Wave 6: Documentation, self-bootstrap (2 tasks)

### T-25: Documentation: README, INSTALL, architecture, commands

- deps: ["T-19", "T-20", "T-21", "T-22", "T-23"]
- agent: doc-updater
- validator: code-reviewer
- idempotent: true
- outputs: ["README.md", "docs/INSTALL.md", "docs/architecture.md", "docs/commands.md", "docs/harness-internals.md"]
- acceptance: SM-90-proposed (see report)
- estimate: M

User-facing docs. `README.md` covers what sk is, install (skill drop-in + pipx), 5-minute walkthrough (`/sk.init` → `/sk.specify` → `/sk.go`). `docs/INSTALL.md` covers the three install channels from ERD §2.3 (skill drop-in primary, pipx secondary, brew deferred per OQ-9). `docs/architecture.md` is derived from `.skspec/.erd/plan-001.md` at ship (sanitized for public). `docs/commands.md` is the per-command reference for all 21 commands (PRD §6) with examples. `docs/harness-internals.md` documents the state machine + envelope formats so users can debug. **Engineer-flagged proposal: add SM-90 to test-plan-001 covering "README quick-start works on fresh clone" — see decision-log entry**.

### T-26: Self-bootstrap verification

- deps: ["T-21", "T-22", "T-24", "T-25"]
- agent: general-purpose
- validator: manual
- idempotent: false
- outputs: [".progress/decision-log.md", ".knowledge/decisions.md"]
- acceptance: test-plan-001 §5 (Self-Bootstrap Verification, all four checks)
- estimate: M

Implements test-plan §5. Once T-21..T-25 land, this task runs the freshly-built sk binary against the live `.skspec/` directory of iteration 001 itself: (1) `/sk.status` produces a meaningful report; (2) `/sk.iteration.complete` works on iteration 001 producing a real retro (`.knowledge/retrospectives/001-retro.md`); (3) iteration 002 can be drafted and `/sk.go`'d using the v1 binary; (4) no file in `.skspec/` was lost. **Marked idempotent: false** because invocations append to `.progress/decision-log.md` and may also append to `.knowledge/decisions.md` — these are non-invertible side effects on user-visible artifacts (Constitution §III: snapshot before running per the precondition note in the task body — implementer MUST snapshot `.skspec/` to a sibling tarball before first run). Validator is `manual` because acceptance is observation-driven against the actual behavior of the live binary, not unit-testable. **Note: this task ships the actual `001-retro.md` for this iteration** — Phase 5 retro is captured here, not separately.

---

## Acceptance-coverage summary

Mapping of test-plan-001 scenarios → implementing task(s):

| Scenario | Task(s) |
|----------|---------|
| SM-01 init structure | T-01..T-04, T-19, T-27 |
| SM-02 init repair-only | T-19 |
| SM-03 init alongside code | T-19 |
| SM-10..13 specify flow | T-17, T-20 |
| SM-14 plan w/o spec | T-20 |
| SM-15 tasks w/o plan | T-08, T-20 |
| SM-20 go end-to-end | T-14, T-15, T-21, T-24 |
| SM-21 parallel batch | T-15, T-21, T-24 |
| SM-22 max_concurrency=1 | T-15, T-21 |
| SM-23 step | T-21 |
| SM-24 review | T-16, T-21 |
| SM-30..33 pause/resume | T-21, T-24 |
| SM-32 crash recovery | T-04, T-05, T-10 |
| SM-40..43 failure/retry/deadlock | T-15, T-16, T-23, T-24 |
| SM-50..53 roster reconciliation | T-13, T-16, T-23 |
| SM-60..63 PRD proposal | T-17, T-20, T-24 |
| SM-70..73 iteration lifecycle | T-13, T-22 |
| SM-80..82 headless | T-18, T-21 |
| OBS-01..05 decision log | T-06, T-14 |
| OBS-10..12 status | T-22 |
| INT-01..03 hand-edits | T-04, T-08, T-10 |
| INT-10..11 concurrency | T-09, T-15 |
| INT-20 schema version | T-04, T-05, T-07 |
| Self-bootstrap §5 | T-26 |

**Engineer-flagged uncovered scenarios** proposed for user to add to test-plan-001 (NOT silently absorbed):
- **SM-31a**: byte-equal `state.json` round-trip on pause→resume (currently SM-31 only requires "no duplicate work")
- **SM-90**: README quick-start works on fresh clone (currently no automated coverage of T-25 docs)

---

## DAG visualization (waves and dependencies)

```
Wave 1 [3]: T-01 ──┬── T-02 ─────────────────────────────────────┐
                   └── T-03 ─────────────────────────────────────┤
Wave 2 [8]: from T-02:                                            │
              ├── T-04 ──┬── T-05 ──┐                             │
              │          ├── T-06 ──┤                             │
              │          ├── T-08 ──┘                             │
              │          └── T-09                                 │
              ├── T-07 ──── T-11                                  │
              └── T-27                                            │
Wave 3 [5]: T-10 (←T-05,T-06)                                     │
            T-12 (←T-11)                                          │
            T-13 (←T-11)                                          │
            T-17 (←T-05,T-06)                                     │
            T-16 (←T-09,T-13)                                     │
Wave 4 [5]: T-14 (←T-09,T-10,T-12,T-16)                           │
            T-15 (←T-09,T-11,T-12)                                │
            T-18 (←T-07,T-14,T-15,T-17)                           │
            T-19 (←T-03,T-05,T-06,T-07,T-11) ─────────────────────┤
            T-20 (←T-08,T-11,T-17,T-19)                           │
Wave 5 [4]: T-21 (←T-14,T-15,T-16,T-18,T-19)                      │
            T-22 (←T-06,T-09,T-17,T-19)                           │
            T-23 (←T-16,T-19)                                     │
            T-24 (←T-15,T-16,T-17,T-18)                           │
Wave 6 [2]: T-25 (←T-19..T-23)                                    │
            T-26 (←T-21,T-22,T-24,T-25)                           │
```

**Critical path** (longest dep chain, 11 nodes): T-01 → T-02 → T-04 → T-05 → T-10 → T-14 → T-18 → T-21 → T-25 → T-26 (with intermediate hop via T-09 or T-12 inside Wave 3-4 boundary).

**Engineer note on depth**: The dispatcher prompt specifies "Max DAG depth: 6". I interpret this as wave count (synchronization barriers), which matches the architect's §19 preview. The critical path (10 nodes) is longer than the wave count (6) because Wave 2 contains intra-wave deps (e.g., `T-04 → T-05`) that the dispatcher resolves with multiple sub-batches inside the wave. With `max_concurrency=3` and 27 tasks, the achievable batch count is approximately ceil((1+2+3+5+6+5+5+4+2)/3) ≈ 11 batches across 6 waves, which is acceptable for an iteration of this size. **Flagged for user/architect review** if a stricter "critical-path ≤ 6" reading is intended.

---

**End of tasks-001 v0.1. 27 tasks across 6 waves. Awaiting Phase 3 dispatch by /sk.go.**
