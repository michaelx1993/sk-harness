---
name: sk-log
description: Tail the TPM decision log
argument-hint: "[N]"
---

```bash
sk log --tail ${ARGUMENTS:-50}
```

Shows the last N lines (default 50) of `.skspec/.progress/decision-log.md` — every TPM decision, roster change, review outcome, and task transition.
