---
name: sk-agent
description: Inspect or modify agent roster
argument-hint: "<list|add|remove> [role] [--type <subagent_type>]"
---

```bash
sk agent $ARGUMENTS
```

Subcommands:
- `list` — current roster with statuses and rationale
- `add <role> [--type subagent_type]` — manually add an agent
- `remove <role>` — remove an agent (TPM reconciliation may re-add if keywords match)
