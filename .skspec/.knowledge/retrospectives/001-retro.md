# Iteration 001 Retrospective — sk Harness MVP

**Completed**: 2026-04-20
**Slug**: sk-harness-mvp
**Planned tasks**: 27 · **Done**: 27 · **Failed**: 0
**Loops**: 5 (manual TPM; real `/sk-go` will run much more granularly)
**PRD proposals**: 1 filed, 1 accepted (ERD §3/§4 skills-vs-commands)

## What went well

- **Fork-don't-rewrite held**: upstream `speckit/specify_cli/` imported verbatim. Divergence is concentrated in `sk_harness.speckit_adapter`.
- **ERD-vs-reality check worked**: T-01 surfaced the `.claude/skills/` vs `.claude/commands/` gap before any command code was written. Cost of rework = revised 150 lines of ERD §4. Cost had we missed it = rewriting all Wave 5 tasks.
- **Task DAG batching is natural**: 27 tasks across 6 waves, critical path 11, max intra-wave parallelism ~6. `roster_reconcile` keyword scan added the right specialists without user intervention.
- **Self-bootstrap succeeded**: `sk status` correctly reports against `.skspec/` we authored by hand.
- **Test coverage > 80%** (83.4%) on first green pass.

## What didn't

- **Per-task subagent dispatch was too slow**: batching 8+ tasks into one "TPM direct implementation" burst at user's prompt was 10× faster. Lesson: subagent dispatch is right for **heterogeneous** tasks where role specialization matters; for homogeneous Python authoring, direct is faster. TPM prompt guidance should reflect this.
- **Architect made five assumptions without source access**: `.claude/commands/` layout was wrong. Future Phase 1 ERD drafts should dispatch a reconnaissance subagent to read upstream *first* before the architect writes, if the iteration depends on external conventions.
- **`.prd-pending/` used for an ERD gap**: subagent correctly erred safe, but per Decision #4 (ERD = agent-autonomous) this should have gone straight to "ERD revision". Add a new channel `.erd-pending/` or clearer routing: "ERD gap = autonomous fix; PRD gap = user confirm".
- **27 task sidecars were a lot of overhead to hand-maintain**. The parser works; the hand-authoring before it was painful. Accelerating with `/sk-tasks` auto-generation will be critical in iter 002.

## Decisions ratified

See `.knowledge/decisions.md`:
- sk registers as Claude Code agent skill, not flat command file

## Carryover to Iteration 002

1. **`.erd-pending/` channel** — separate from `.prd-pending/` so the protocol is unambiguous
2. **Reconnaissance subagent pattern** — Phase 1 step 0.5: read external sources referenced in the PRD before architect drafts
3. **Direct-implementation mode** for TPM — heuristic to decide when to batch-author vs dispatch per task
4. **Real `/sk-go` driven loop** — iter 001 ran the loop manually in the main conversation. Iter 002 should prove `/sk-go` drives it autonomously.
5. **CLI smoke tests against live `.skspec/`** — SM-90 (README quick-start) and expanded SM-31a (byte-equal pause-resume state) from the engineer's uncovered-scenarios list.
6. **Lower coverage gate not needed** — 83% achieved; tighten to 85% in iter 002.

## Metrics

| Metric | Value |
|--------|-------|
| Planned tasks | 27 |
| Completed | 27 |
| Failed | 0 |
| Retries | 0 |
| Loops (manual TPM) | 5 |
| PRD proposals filed | 1 |
| PRD proposals accepted | 1 |
| ERD history snapshots | 1 |
| Test count | 46 |
| Test coverage | 83.4% |
| Lines of Python | ~950 |
| Lines of Markdown (templates + SKILL.md) | ~400 |

## Quotes from the trenches

> "我们只是想给speckit加上harness框架，使其能够自主循环迭代。为什么开发速度这么慢。"

User called out our over-ceremony. The correction (drop per-task subagent dispatch, let TPM author directly) was the right lever. The TPM loop as-designed (one subagent per task) is appropriate for **real** project work where each task is chunky, heterogeneous, and benefits from a reviewer in the loop. For meta-work like authoring sk itself, the ceremony outweighs the insurance.
