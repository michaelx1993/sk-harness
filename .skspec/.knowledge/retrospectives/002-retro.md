# Iteration 002 Retrospective — Harness Completion

**Completed**: 2026-04-20 (same day as iter-001; no pause between)
**Slug**: harness-completion
**Planned tasks**: 8 · **Done**: 8 · **Failed**: 0
**Loops**: 1 (direct TPM authoring; no subagent dispatch needed for pure Python module work)
**Proposals filed**: 0 prd, 0 erd
**Test delta**: 46 → 70 tests; coverage 83.4% → 84.25%

## What went well

- **`.erd-pending/` channel worked on first design**: mirrored `.prd-pending/` structurally; only added auto-accept-with-snapshot. No architecture changes needed to the proposals module beyond a `Channel` Literal.
- **CLI additions composed cleanly**: `config`, `step`, `review`, `erd-pending`, `analyze`, `checklist`, `constitution` added without touching existing commands. Click's group-command pattern scaled.
- **`sk analyze` self-verifies**: running it against this very `.skspec/` after iter-002 passes all 4 checks. That's the dogfood we promised in spec-001 §14.
- **Direct authoring was correct choice**: per iter-001 retro carryover, iter-002 used zero subagent dispatches. 8 tasks done in one assistant turn's worth of writes. User-perceived speed jumped dramatically.
- **Backward compatibility via shim** (`sk_harness.prd_merge` → `sk_harness.proposals`): zero test breakage on the rename.

## What didn't

- **Edit-after-Write friction**: tried to Edit `prd_merge.py` shortly after Writing it; tool reported "not read yet" and forced a re-read. Not a harness bug, but a workflow lesson: after Write, re-Read before Edit within the same session boundary.
- **No live `/sk-go` test yet**: we shipped the improved SKILL.md (now honors step / review_requested / `.erd-pending/` scan in Step 0) but it was not driven by a real Claude Code session in this iteration. That's still iter-003's job.
- **No integration tests crossing CLI → state → filesystem**: all 70 tests are unit-level. A `pytest tests/integration/` folder would catch CLI regressions better. Adding is a straightforward iter-003 item.

## Decisions ratified

No new architectural decisions in iter-002 — everything followed from iter-001's constitution + ERD. The skills-layout decision from iter-001 continued to hold.

## Carryover to Iteration 003

1. **Live `/sk-go` drive**: spin up a real demo iteration (e.g., "add a toy feature to a new project") and let `/sk-go` actually orchestrate subagent dispatches end-to-end. This is the one remaining unverified claim from spec-001.
2. **Integration test suite**: `tests/integration/test_full_flow.py` exercising `sk init → sk status → manually seed spec → sk analyze → sk checklist → sk pause/resume → sk iteration complete`.
3. **Recon subagent usage**: currently we have the template but `/sk-go` SKILL.md doesn't dispatch it yet. Wire it into Phase 1 properly.
4. **Documentation for users outside the SDD flow**: README targets sk authors; a separate "Using sk for your project" quickstart is needed once iter-003 ships a working demo.

## Metrics

| Metric | iter-001 | iter-002 | Delta |
|--------|----------|----------|-------|
| Tasks | 27 | 8 | -19 |
| Completed | 27 | 8 | — |
| Failed | 0 | 0 | — |
| Loops | 5 (manual) | 1 | -4 |
| Tests | 46 | 70 | +24 |
| Coverage | 83.4% | 84.25% | +0.85pp |
| PRD proposals | 1 / 1 | 0 / 0 | — |
| Python LoC | ~950 | ~1240 | +290 |
| SKILL.md files | 12 | 19 | +7 |

## Note to future iterations

At iter-002 close, `sk-harness` has all 21 commands from spec-001 §6 either implemented (CLI + SKILL.md) or delegated (sk-constitution opens editor; sk-clarify is Claude-driven). The gap between "code complete" and "end-to-end verified" is one live session where `/sk-go` drives a real iteration. That's the exit condition.
