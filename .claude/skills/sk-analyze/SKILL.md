---
name: sk-analyze
description: Cross-reference consistency check across spec, plan, tasks, test-plan
argument-hint: ""
---

```bash
sk analyze
```

Runs checks:
1. ERD §N references in task sidecars exist as `## N` headers in plan-NNN.md
2. `acceptance_ids` (SM-XX, OBS-XX, INT-XX) appear in test-plan-NNN.md
3. Task IDs are unique
4. Task DAG is acyclic

Exit 0 = pass; exit 1 = one or more failures (printed with details).
