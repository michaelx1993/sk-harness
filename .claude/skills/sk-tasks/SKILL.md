---
name: sk-tasks
description: Decompose ERD into task DAG (tasks-NNN.md + sidecars), OR inspect tasks
argument-hint: "[list|show <id>|graph|retry <id>]"
---

## Inspection mode (if $ARGUMENTS starts with list/show/graph/retry)

```bash
sk tasks $ARGUMENTS
```

## Decomposition mode (no arguments)

You (Claude) act as the engineer-subagent per `templates/harness/agents/engineer.md`.

### Steps
1. Read active iteration id.
2. Read `prd/spec-<id>.md`, `.erd/plan-<id>.md`, `tests/test-plan-<id>.md`, `.knowledge/`.
3. Draft `.task/tasks-<id>.md` as markdown with per-task grammar (see `templates/harness/tasks-NNN.md`):
   - `## Wave N: <name>` headers as synchronization barriers
   - `### T-NN: <title>` per task with fields: deps, agent, validator, idempotent, outputs, acceptance, estimate
4. After markdown is written, regenerate sidecars:
   ```bash
   python -m sk_harness.dag.regen_sidecars <id>    # (helper — if not present, parse manually)
   ```
   or programmatically: read the markdown → parse with `sk_harness.dag.parser.parse_tasks_markdown` → write via `write_sidecars`.
5. Initialize `.progress/state.json` task list with all IDs in state=pending.
6. Append decision-log entry.

### Principles
- **Size the task count to the project.** Rubric: toy/script = 3–6 tasks; small feature = 6–12; medium = 12–20; large = 20–30 (hard cap). **Under-decompose by default.**
- Merge siblings that share agent + validator + output dir, or that have linear 1:1 deps fitting in ≤ 6h
- Don't split "write X" and "test X" — one task with `validator: tdd-guide` is almost always better
- Only split when tasks can actually run in parallel (different files AND different reviewers)
- Max wave depth 6; each task ≤ 6h; idempotent by default
- Validator catalog-specific (python-reviewer, tdd-guide, code-reviewer, etc.)

### When in doubt: merge.
You can always split a task mid-execution via `.prd-pending/` proposal if it turns out too chunky. Over-decomposition is harder to undo.
