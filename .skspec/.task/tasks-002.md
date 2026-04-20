# Tasks — Iteration 002 (Harness Completion)

**Version**: 0.1
**Total tasks**: 8
**Waves**: 2

## Wave A: Foundations

### T-01: Rename prd_merge → proposals, add .erd-pending/ flow
- deps: []
- agent: general-purpose
- validator: python-reviewer
- idempotent: true
- outputs: [sk_harness/proposals.py, sk_harness/prd_merge.py]
- acceptance: SM-100, SM-101
- estimate: S

Refactor `sk_harness/prd_merge.py` into `sk_harness/proposals.py`. Add `file_erd_proposal`, `accept_erd_proposal`, `reject_erd_proposal`, `list_erd_pending`. Keep `prd_merge.py` as a backward-compat shim that re-exports from `proposals`.

### T-02: paths.erd_pending_dir + skeleton update
- deps: [T-01]
- agent: general-purpose
- validator: code-reviewer
- idempotent: true
- outputs: [sk_harness/paths.py, templates/harness/skspec-skeleton/.erd-pending/.gitkeep]
- acceptance: SM-101
- estimate: S

Add `erd_pending_dir` property. Add `.erd-pending/.gitkeep` to the skeleton so `/sk-init` creates the directory.

### T-03: PauseReason enum extension
- deps: []
- agent: general-purpose
- validator: python-reviewer
- idempotent: true
- outputs: [sk_harness/state/models.py]
- acceptance: SM-104, SM-105
- estimate: S

Add `step` and `review_requested` to `PauseReason` enum.

## Wave B: Commands + tests

### T-04: CLI subcommands (config, step, review, erd-pending)
- deps: [T-01, T-03]
- agent: general-purpose
- validator: python-reviewer
- idempotent: true
- outputs: [sk_harness/cli.py]
- acceptance: SM-102, SM-103, SM-104, SM-105, SM-106, SM-107
- estimate: M

Add `sk config <show|set>`, `sk step`, `sk review`, `sk erd-pending <list|accept|reject>`. Also add `sk analyze` and `sk checklist` since they're thin.

### T-05: Seven SKILL.md files
- deps: [T-03, T-04]
- agent: general-purpose
- validator: code-reviewer
- idempotent: true
- outputs: [.claude/skills/sk-constitution/SKILL.md, .claude/skills/sk-clarify/SKILL.md, .claude/skills/sk-analyze/SKILL.md, .claude/skills/sk-checklist/SKILL.md, .claude/skills/sk-step/SKILL.md, .claude/skills/sk-review/SKILL.md, .claude/skills/sk-config/SKILL.md]
- acceptance: SM-108
- estimate: S

### T-06: analyze + checklist implementation
- deps: [T-04]
- agent: general-purpose
- validator: python-reviewer
- idempotent: true
- outputs: [sk_harness/analyze.py, sk_harness/checklist.py]
- acceptance: SM-102, SM-103
- estimate: M

Cross-reference consistency checker per ERD §2 and §3.

### T-07: Recon subagent template
- deps: []
- agent: general-purpose
- validator: code-reviewer
- idempotent: true
- outputs: [templates/harness/agents/recon.md]
- acceptance: SM-108
- estimate: S

### T-08: Tests + coverage + retro
- deps: [T-04, T-05, T-06, T-07]
- agent: general-purpose
- validator: tdd-guide
- idempotent: true
- outputs: [tests/unit/test_proposals.py, tests/unit/test_cli_iter002.py, tests/unit/test_analyze.py, .skspec/.knowledge/retrospectives/002-retro.md]
- acceptance: SM-100..SM-108
- estimate: M

Run pytest, confirm ≥ 80% coverage, write iter-002 retro, close iteration.
