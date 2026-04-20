---
name: sk-iteration
description: Iteration lifecycle — list, complete, show
argument-hint: "<list|complete> [iteration-id]"
---

```bash
sk iteration $ARGUMENTS
```

Subcommands:
- `list` — enumerate all iterations with status
- `complete` — close current iteration (refuses if pending/running tasks), triggers retro via `/sk-go` next phase
