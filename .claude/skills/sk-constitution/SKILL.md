---
name: sk-constitution
description: Edit or show the project constitution
argument-hint: "[--show]"
---

```bash
sk constitution $ARGUMENTS
```

Without flags: prints the path to `.skspec/.constitution.md` so you can open in your editor.
With `--show`: streams contents to stdout.

Amendments to constitution are PRD-class edits (Constitution §I meta-rule): draft a `.prd-pending/` proposal rather than editing silently when automated.
