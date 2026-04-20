# Test Plan — Iteration 002 (Harness Completion)

**Owner**: User (per Constitution §II)
**Status**: baseline, will grow as features land.

## Environment

Same as iter-001 (`tests/test-plan-001.md §1`).

## New acceptance scenarios

| ID | Scenario | Expected |
|----|----------|----------|
| SM-100 | `file_erd_proposal(...)` writes `.erd-pending/proposal-<ts>.md` | file created, returned path valid |
| SM-101 | `accept_erd_proposal` snapshots current plan-NNN.md then appends proposal body | `.erd/history/` has new file; `plan-NNN.md` has appended section; original proposal archived |
| SM-102 | `sk analyze` passes on iter-001 artifacts | exit 0; 4 checks reported |
| SM-103 | `sk analyze` fails when a sidecar references missing §Z | exit 1; explicit message |
| SM-104 | `sk step` sets pause + logs | state.paused=False but pause_reason flagged after next batch; decision-log entry |
| SM-105 | `sk review` sets pause with `review_requested` | state.paused=True; pause_reason=review_requested |
| SM-106 | `sk config show` prints 3 keys | stdout contains max_concurrency, max_retries, max_active_agents |
| SM-107 | `sk config set max_concurrency 5` persists | `.agents.json.max_concurrency == 5` |
| SM-108 | `sk erd-pending list` on empty dir | exits 0 with "none pending" |

## Self-bootstrap verification

- SM-5.2: `sk analyze` passes on this very `.skspec/` after iter-002 artifacts land (at least: spec/plan/tasks/test-plan exist with matching IDs).
