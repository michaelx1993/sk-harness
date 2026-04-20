---
name: sk-init
description: Bootstrap .skspec/ workspace for a new sk-harness project
argument-hint: "[project-name]"
---

Initialize the sk-harness workspace in the current directory.

## Execute

```bash
sk init $ARGUMENTS
```

## What it creates

A `.skspec/` directory with:
- `prd/` `tests/` `docs/` `references/` — user-maintained
- `.erd/` `.task/` `.progress/` `.snapshot/` `.knowledge/` `.prd-pending/` — agent-maintained
- Seed state files: `.version`, `.iterations.json`, `.agents.json`, `.agents-catalog.json`, `.constitution.md`

## Next steps

1. `/sk-constitution` — ratify project principles
2. `/sk-specify` — draft PRD for your first iteration
3. `/sk-go` — hand off to TPM loop

Idempotent: rerunning only adds missing files; existing files untouched.
