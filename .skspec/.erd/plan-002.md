# ERD — Iteration 002

**Version**: 0.1
**Source PRD**: `prd/spec-002.md` v0.1
**Inherits**: `.erd/plan-001.md` v0.2 in its entirety; this document describes only deltas.

## 1. Delta summary

| Area | Change |
|------|--------|
| `sk_harness/prd_merge.py` | Rename module to `sk_harness/proposals.py`; add `file_erd_proposal`, `accept_erd_proposal`, `reject_erd_proposal`, `list_erd_pending`. Keep old symbols as backward-compat re-exports. |
| `sk_harness/paths.py` | New property `erd_pending_dir`. |
| `sk_harness/cli.py` | New subcommands: `step`, `review`, `config`, `erd-pending` (group). Existing `specify --accept|--reject` preserved. |
| `sk_harness/state/models.py` | Extend `PauseReason` enum with `review_requested` and `step`. |
| `.claude/skills/` | 7 new SKILL.md files. |
| `templates/harness/agents/` | Add `recon.md`. |
| `templates/harness/skspec-skeleton/` | Add `.erd-pending/.gitkeep`. |

## 2. Analyze implementation (sk analyze)

Cross-reference checks:
1. Every `§X` reference in tasks-NNN.md sidecars maps to an `## X` or `### X` header in plan-NNN.md.
2. Every `acceptance_ids` entry in a sidecar appears as an ID in `tests/test-plan-NNN.md`.
3. No duplicate task IDs.
4. DAG acyclic (already enforced by `TaskGraph.__init__`).
5. Every `outputs` path is either under the repo OR is a known external target.

Report format:
```
analyze iter=<N>
- 4 checks passed
- 1 check failed: T-07 references §12 but plan has only §1..§11
```

Exit code 0 all pass; 1 any failure.

## 3. Checklist implementation (sk checklist)

From each task's `acceptance_ids`, emit a markdown checklist:
```
- [ ] T-01 → SM-01, OBS-01
- [ ] T-02 → SM-01
```
Output to stdout; user copies into PR description.

## 4. Config implementation (sk config)

`sk config show`: pretty-prints `.agents.json` top-level fields (max_concurrency, max_retries, max_active_agents, roster size).

`sk config set <key> <value>`: only the three concurrency/retry keys; other keys return error.

## 5. Step & review implementation

`sk step`: set `state.paused=false`, `state.pause_reason=null`, but add a transient `state.step_requested=true`. Next loop does one batch then auto-pauses with `pause_reason=step`.

Actually simpler: define a new PauseReason.step and the `/sk-go` SKILL.md logic honors it. CLI command `sk step` clears pause and logs intent; `/sk-go` after one batch sets `pause_reason=step` and stops.

`sk review`: sets `state.paused=true` with `pause_reason=review_requested` and a decision-log entry. User reads the latest review subagent output, then `sk resume` + `/sk-go`.

## 6. Recon template

Dispatched as an optional Phase 1 Step 0 subagent. Input: list of external refs (upstream repos, URLs). Output: a structured "reality report" section the architect reads before drafting. For iter-003+, the `/sk-go` SKILL.md is updated to spawn recon when ERD references `speckit/` or an external URL.

## 7. Task decomposition (8 tasks, 2 waves)

```
Wave A:  T-01 proposals module rename + .erd-pending/  [deps: none]
         T-02 paths + skeleton update                  [deps: T-01]
         T-03 pause reason enum extension              [deps: none]

Wave B:  T-04 CLI config/step/review/erd-pending       [deps: T-01, T-03]
         T-05 Seven SKILL.md files                     [deps: T-03, T-04]
         T-06 analyze + checklist implementation       [deps: T-04]
         T-07 recon.md template                        [deps: none]
         T-08 tests + coverage + retro                 [deps: T-04..T-07]
```

Max depth: 3. Ideal batches: 3 + 4 + 1.

## 8. Open questions

OQ-10: Should `sk review` actually dispatch the review subagents inline (requires being inside Claude Code), or just mark the state for `/sk-go` to pick up? **Decision**: mark only. Real dispatch is `/sk-go` step 2's job. Justification: CLI is a sync helper, not a Claude proxy.

OQ-11: `analyze` check 5 (outputs path validity) is fuzzy. **Decision**: skip for v0.1; only check "starts with letter or dot (relative)" as weak guard.
