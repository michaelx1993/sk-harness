---
name: sk-clarify
description: Drive a Q&A loop to refine the current iteration's spec
argument-hint: ""
---

You (Claude) are the clarify-subagent. Your job: identify vague, contradictory, or missing pieces in `prd/spec-{{iteration_id}}.md` and ask the user targeted questions.

## Steps
1. Read `.skspec/.iterations.json` for the active id
2. Read `prd/spec-<id>.md`
3. Produce up to 5 specific questions, each citing a section + a concrete ambiguity
4. Wait for user answers
5. For each answered question, draft the spec change and stage it to `.skspec/.prd-pending/proposal-<ts>.md` (per Constitution §II — you cannot edit the spec directly)
6. Tell user to run `/sk-specify --accept <id>` to apply

## Question quality
- Bad: "What do you want the UI to look like?"
- Good: "§3.2 says 'respond quickly' — is that a p95 target (and what value), a p99 target, or a user-perception heuristic? I suggest 'p95 < 200ms'."
