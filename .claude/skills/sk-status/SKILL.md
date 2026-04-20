---
name: sk-status
description: Show current iteration, task counts, pause state, and recent decisions
argument-hint: ""
---

```bash
sk status
```

Reports:
- Active iteration id, slug, status, phase, loop count
- Task state counts (pending / running / done / failed / blocked)
- Pause flag and reason
- Current batch in flight
- Agent roster size
- Any pending `.prd-pending/` proposals
