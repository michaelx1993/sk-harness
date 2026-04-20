---
name: sk-resume
description: Clear the pause flag. Use /sk-go to actually continue.
argument-hint: ""
---

```bash
sk resume
```

Clears `paused` and `pause_reason` in state. Does NOT itself run tasks — invoke `/sk-go` afterward to resume the loop.
