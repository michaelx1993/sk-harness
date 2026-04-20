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
- ≤ 30 tasks, max wave depth 6
- Each task = one dispatch, ≤ 6h
- Idempotent by default
- Validator catalog-specific (python-reviewer, tdd-guide, code-reviewer, etc.)
