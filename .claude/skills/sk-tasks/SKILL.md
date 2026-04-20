---
name: sk-tasks
description: Decompose ERD into task DAG (rolling wave) OR inspect OR refine next wave
argument-hint: "[list|show <id>|graph|retry <id>|--refine]"
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

### Rolling-wave principle (CORE)
**Detail the near wave; sketch the far.**

- Only Wave 1 (the NEXT ≤6 tasks to execute) gets full T-NN detail + sidecars
- Wave 2, 3, ... are **one-line milestones** in the markdown, no sidecars
- When Wave 1 completes: `/sk-tasks --refine` details Wave 2 **using what was actually learned from Wave 1**
- Repeat until iteration complete

Why: over-planned far tasks rot. Planning fresh with ground truth is cheaper than rewriting stale tasks.

### Near-term per-wave size
- Toy/script: 2–4 tasks per detailed wave
- Small app: 3–5
- Medium: 4–6
- Large: 5–7

### Merge-first heuristics (inside the detailed wave)
- Share agent + validator + output dir → merge
- Linear 1:1 dep, ≤ 6h combined → merge
- "write X" + "test X" → one task with `validator: tdd-guide`
- Only split when tasks can actually run in parallel (different files AND different reviewers)

### Hard rules
- Max wave depth 6 total (detailed + milestones combined)
- Detailed task ≤ 6h; idempotent by default
- Validator catalog-specific

### Milestone format (markdown-only, no sidecar)
```markdown
## Wave 2: Rendering core  [milestone]

One-line goal. Will be detailed via `/sk-tasks --refine` after Wave 1 completes.
```

### `--refine` mode
When $ARGUMENTS contains `--refine`:
1. Find the first wave marked `[milestone]` with no detailed tasks
2. Read `.knowledge/`, settled snapshots, recent decision-log
3. Detail that wave with T-NN tasks + sidecars (still ≤ per-wave size cap)
4. Leave later milestones untouched
5. Append decision-log entry: "refined Wave N based on Wave N-1 actuals"
