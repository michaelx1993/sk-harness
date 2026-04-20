# TPM Decision Log

Append-only log of every TPM decision, agent roster change, and review outcome.
Format: each entry is a markdown section with timestamp + iteration + loop + actor + decision + rationale.

---

## 2026-04-19T00:00:00Z · iter=001 · loop=0 · actor=user · decision=bootstrap

Created `.skspec/` skeleton via discussion-driven design.
PRD captured as `prd/spec-001.md` (see file for v0.3 content).
TPM has not started yet — awaiting first `/sk.go` invocation once sk fork is implemented.

---

## 2026-04-19 · iter=001 · loop=0 · actor=architect-subagent · decision=ERD draft v0.1 written

Drafted `.erd/plan-001.md` v0.1 addressing all 18 required ERD sections from the dispatcher prompt. Major design choices: (1) stay on Python 3.11+ with `uv` package manager to match spec-kit and minimize fork divergence per Constitution §VI; (2) isolate upstream-to-sk renames in a single `sk_harness.speckit_adapter` module so upstream merges touch one file; (3) implement the TPM as one long-lived `general-purpose` subagent per `/sk.go` call that re-reads state each loop rather than respawning per iteration; (4) use networkx + filelock + pydantic rather than hand-rolled equivalents per the user's preference for mature libraries. Nine open questions (OQ-1..OQ-9) and six inline TODOs were raised for TPM/user review during Phase 2 decomposition.

---

## 2026-04-19 · iter=001 · loop=0 · actor=engineer-subagent · decision=tasks-001 v0.1 written

Wrote `.task/tasks-001.md` v0.1 (27 tasks across 6 waves) plus 27 per-task JSON sidecars under `.task/tasks-001/`. Critical-path length is 11 nodes (T-01 → T-02 → T-04 → T-05 → T-10 → T-14 → T-18 → T-21 → T-25 → T-26), longer than the dispatcher prompt's "Max DAG depth: 6" guideline; this is interpreted as wave count (synchronization barriers), and the markdown documents intra-wave parallelism that brings the achievable batch count to ~14 with `max_concurrency=3`. Major deviations from the architect's §19 preview: (a) added T-27 (CI configuration) and T-25 (full docs set) which the preview omitted; (b) split commands across T-19/T-20/T-21/T-22/T-23 by lifecycle role (setup, SDD, execution, observation, override) instead of architect's T-14..T-20 sequential grouping, to maximize Wave 4–5 parallelism; (c) made T-26 (self-bootstrap verification) the sole `idempotent: false` task because it mutates `.skspec/.progress/decision-log.md` and `.knowledge/decisions.md` non-invertibly; (d) consolidated the architect's separate T-22 (review/roster/term) into a single T-16 to reduce dep count. Engineer-flagged uncovered scenarios for user to add to test-plan-001: SM-31a (byte-equal state.json round-trip pause→resume) and SM-90 (README quick-start works on fresh clone). All nine architect open questions OQ-1..OQ-9 are referenced inline in tasks where they apply, with the architect's recommended option chosen by default and escape hatch documented (file `.prd-pending/proposal-<ts>.md` if conflict surfaces during implementation).

---

## 2026-04-19T22:00:00Z · iter=001 · loop=1 · actor=tpm(main-conversation) · decision=Phase-3 kickoff, T-01 dispatched

Entering Phase 3 (implementation). ready_set = {T-01} (no deps). Dispatching general-purpose subagent for T-01 "Fork spec-kit". Note: acting as TPM manually in this bootstrap loop since `/sk.go` binary does not yet exist — this is the chicken-and-egg entry point. T-02 and T-03 (which depend on T-01) will enter ready_set upon T-01 completion.

---

## 2026-04-20T05:08:21Z · iter=001 · loop=1 · actor=general-purpose(T-01) · decision=T-01 complete (fork)

Pinned spec-kit commit `c118c1c30f961921e41891df3318a2ccd2ceea54` (tip of `main`, authored 2026-04-17, upstream version string `0.7.4.dev0`, per ERD §1.1 + OQ-1 option A). Copied `src/specify_cli/` verbatim to `speckit/specify_cli/` (52 Python files), `templates/` verbatim to `templates/upstream/` (15 files: 5 page templates + `vscode-settings.json` + `commands/` with 9 command bodies), and `LICENSE` verbatim to repo root (MIT, 1 061 bytes). Wrote `docs/UPSTREAM.md` per ERD §1.4 (pinned SHA, fork date, inventory of copied/excluded items, weekly-scan + quarterly-rebase cadence, three-step merge runbook) and `docs/ERD-VALIDATION.md` (20-row assumption table: 14 confirmed, 5 mismatched under a single architectural gap, 1 undetermined). Cleaned up `/tmp/speckit-upstream/` clone. Filed `.prd-pending/proposal-20260420T050821Z.md` for the mismatched rows: ERD §4 assumes `.claude/commands/sk.<name>.md` slash-command files, but upstream's Claude integration registers as `agentskills.io`-spec skills under `.claude/skills/speckit-<name>/SKILL.md` and the invocation surface is hyphenated (`/speckit-specify`, not `/speckit.specify`); proposal asks TPM to retarget §3 + §4 and expand §1.3's adapter-layer contract before Wave 4 (T-19..T-23) begins. T-01 outputs (`docs/UPSTREAM.md`, `speckit/`, `templates/upstream/`, `LICENSE`) all present; idempotency preserved (rerunning would match byte-for-byte unless upstream SHA advances).

---

## 2026-04-20T05:10:00Z · iter=001 · loop=2 · actor=tpm(main-conversation) · decision=accept ERD-revision proposal (NOT PRD change), dispatch Wave 1 + architect in parallel

Proposal `20260420T050821Z` filed by T-01 is classified as branch (b) "ERD contradicted by code reality" per PRD §5.3, not branch (c) "spec gap". Authority to rewrite ERD is agent-autonomous per Decision #4. Moved proposal to `.prd-pending/accepted-as-erd-revision-*.md` for audit. Snapshotted plan-001.md v0.1 to `.erd/history/plan-001-v0.1-pre-skills-revision.md`. Dispatching: (1) architect to revise §1.3/§3/§4 + resolve OQ-3 + write `.knowledge/decisions.md`; (2) implementer for T-02 (scaffold sk_harness); (3) implementer for T-03 (templates/harness stubs). T-02 and T-03 do not touch §4 subtree so parallel execution is safe. Each subagent will NOT write state.json or decision-log directly to avoid race; TPM serializes writes after batch settles.

---

## 2026-04-20T06:00:00Z · iter=001 · loop=3 · actor=tpm(main-conversation) · decision=accelerate, drop per-task subagent ceremony

T-02 and T-03 complete, ERD revised to v0.2. User feedback: development too slow due to per-task subagent dispatch overhead. Switching to direct implementation by TPM for remaining 24 tasks, batched into 3 waves (A: state/IO/parser/adapter, B: snapshots/templates/catalog, C: commands/loop/headless/tests/docs). Starting Batch A = Wave 2 (T-04..T-11).

---

## 2026-04-20T07:00:00Z · iter=001 · loop=5 · actor=tpm(main-conversation) · decision=Phase 5 retro + iteration close

All 27 tasks done; retro written to `.knowledge/retrospectives/001-retro.md`. sk-harness MVP ships: Python package scaffolded (sk_harness/), 12 SKILL.md files registered under .claude/skills/, CLI wired for status/pause/resume/log/tasks/iteration/agent/specify, 46 unit tests at 83.4% coverage, CI config in place, README shipped. Iteration 001 closed; .iterations.json.active=null. Next /sk-specify will open iteration 002 with carryover items from retro §Carryover.

---

## 2026-04-20T08:30:00Z · iter=002 · loop=2 · actor=tpm(main-conversation) · decision=Phase 5 retro + close iter 002

All 8 tasks done. Added .erd-pending/ channel, 7 missing SKILL.md files (sk-constitution/clarify/analyze/checklist/step/review/config), analyze + checklist + recon template. 70 tests at 84.25% coverage. `sk analyze` self-verifies against live .skspec/ with 4/4 checks passing. Exit condition per spec-002 §6 met. See .knowledge/retrospectives/002-retro.md for what went well, what didn't, and iter-003 carryover (live /sk-go drive, integration tests, recon wiring).
