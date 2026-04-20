---
name: sk-step
description: Arm one-batch step. Next /sk-go dispatches exactly one batch then pauses.
argument-hint: ""
---

```bash
sk step
```

Sets `state.pause_reason=step`. The TPM's `/sk-go` loop honors this: completes one batch, then auto-pauses so you can inspect. Resume with `/sk-resume` + `/sk-go`.

Use for debugging a specific batch without risking unwanted progress.
