---
name: sk-config
description: View or modify concurrency + retry configuration
argument-hint: "<show | set KEY VALUE>"
---

```bash
sk config $ARGUMENTS
```

## Subcommands
- `show` — print current values
- `set <key> <value>` — only accepts `max_concurrency`, `max_retries`, `max_active_agents`; other keys refused

## Defaults (from iter-001)
- max_concurrency: 3
- max_retries: 2
- max_active_agents: 8
