---
name: sk-review
description: Force a review cycle (no task dispatch) on next /sk-go
argument-hint: ""
---

```bash
sk review
```

Pauses the loop with `pause_reason=review_requested`. Next `/sk-go` (after `/sk-resume`) will dispatch review subagents (architect / qa / security / engineer perspectives) and return findings BEFORE dispatching any tasks.

Use when you suspect ERD drift, want a security check before a risky batch, or simply want multi-role confirmation.
