---
name: sk-plan
description: Draft ERD (plan-NNN.md) from current spec via architect subagent
argument-hint: ""
---

You (Claude) act as the architect-subagent per `templates/harness/agents/architect.md`.

## Steps
1. Read active iteration id from `.skspec/.iterations.json`.
2. Read `prd/spec-<id>.md`, `.constitution.md`, `.knowledge/decisions.md`, historical `.erd/plan-*.md`.
3. If `.erd/plan-<id>.md` exists:
   - Snapshot it to `.erd/history/plan-<id>-<timestamp>.md`.
   - Load it as starting draft.
4. Draft/revise `.erd/plan-<id>.md` covering: fork strategy (if relevant), runtime, layout, components, interfaces, state, concurrency, open questions.
5. Append decision-log entry (actor=architect).
6. Return summary of sections written + any open questions.

Constitution §III: snapshot before overwrite.
Constitution §VII: ERD is agent-autonomous. You can write directly.
