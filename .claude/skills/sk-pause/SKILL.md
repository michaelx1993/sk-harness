---
name: sk-pause
description: Pause the TPM loop after the current batch settles
argument-hint: ""
---

```bash
sk pause
```

Sets `paused=true` in `.skspec/.progress/state.json`. The TPM (when driven by `/sk-go`) checks this flag between batches and stops cleanly. In-flight subagents are NOT interrupted — pause is task-level per PRD §5.8.

Resume with `/sk-resume` then `/sk-go`.
