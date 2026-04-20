---
name: sk-specify
description: Draft / amend / accept / reject PRD for current or next iteration
argument-hint: "[--accept <id>|--reject <id>]"
---

## Accept / reject pending proposals

If `--accept <id>` or `--reject <id>`, delegate to CLI:

```bash
sk specify $ARGUMENTS
```

## Otherwise: draft / amend

You (Claude) are the specify-subagent. Steps:

1. Read `.skspec/.iterations.json`. If no active iteration, start a new one: iteration id = next zero-padded sequence; slug = user-provided or derived.
2. Read user input (passed as $ARGUMENTS or conversational).
3. If no active iteration exists:
   - Write fresh `prd/spec-<NNN>.md` using `templates/harness/spec-NNN.md` with placeholders filled.
   - Update `.iterations.json` to set this as active.
   - Initialize `.progress/state.json` with empty `tasks: []` and phase `spec-drafted`.
   - Write decision-log entry.
4. If active iteration exists (user is amending):
   - Do NOT overwrite `spec-NNN.md` directly.
   - Write proposal to `.skspec/.prd-pending/proposal-<ts>.md` with fields: `problem`, `evidence`, `suggested_change`, `impact`.
   - Set `state.paused=true`, `pause_reason=prd_proposal`.
   - Tell user to run `/sk-specify --accept <id>` or `--reject <id>` after reviewing.

Constitution §II: only user can sign off on PRD. Your job here is to draft or propose — not to commit without acceptance on amendments.
