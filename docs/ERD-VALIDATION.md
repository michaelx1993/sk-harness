# ERD Validation — Iteration 001, performed during T-01

**Date**: 2026-04-19
**Performed by**: implementer-subagent dispatched by sk Harness TPM
**Scope**: compare ERD assumptions about upstream `github/spec-kit`
(`.skspec/.erd/plan-001.md`) against the actual pinned upstream tree at
SHA `c118c1c30f961921e41891df3318a2ccd2ceea54`.

Per Constitution §VII, the implementer has no authority to silently adapt
ERD specifications. Confirmed-mismatch rows below are accompanied by PRD
proposals filed under `.skspec/.prd-pending/`.

---

## Legend

- [OK] — ERD assumption matches observed upstream state.
- [GAP] — Mismatch. PRD proposal filed.
- [?] — Cannot determine from upstream files alone; defers to Phase 2/3
  implementer who first touches the affected subsystem.

---

## Validation table

| # | ERD reference | Assumption | Observed | Status |
|---|---|---|---|---|
| 1 | §2.1 | Python 3.11+ minimum | `pyproject.toml: requires-python = ">=3.11"` | [OK] |
| 2 | §2.3 | Upstream installs via pip / uvx; sk ships as Claude Code skill + pipx | Upstream publishes `specify-cli` on PyPI; skill mode is first-class via `--ai claude --ai-skills` flag | [OK] |
| 3 | §2.4 | Shared deps: `click`, `rich` | Both are upstream deps (`click>=8.2.1`, `rich`) | [OK] |
| 4 | §2.4 | sk adds `pydantic`, `filelock`, `networkx`, `jsonschema`, `ruamel.yaml` on top | None of these are upstream deps; additive set is clean | [OK] |
| 5 | §2.4 | Upstream uses `click`; sk uses `click` | Upstream also uses `typer>=0.24.0` (Typer wraps Click). sk ERD picks Click directly, which works; no merge conflict. | [OK] |
| 6 | §3 repo layout | `LICENSE` inherited verbatim | Upstream LICENSE copied byte-identical (1 061 bytes, MIT) | [OK] |
| 7 | §3 `speckit/` tree | Upstream code copied verbatim into `speckit/` | Copied `src/specify_cli/` into `speckit/specify_cli/` (52 files). Upstream has no code outside `src/`. ERD §3 shows `speckit/` directly receiving upstream contents; this is interpreted as "mirror `src/` under `speckit/`" so that subsequent `git pull upstream main -- src/specify_cli` rebases cleanly. | [OK] |
| 8 | §3 `templates/upstream/` | Upstream templates copied verbatim | Copied `templates/` (15 files, including `commands/`, `*-template.md`, `vscode-settings.json`) into `templates/upstream/` | [OK] |
| 9 | §1.2 | Do not rename / relocate upstream files in place | Copy preserved full subtree; no renames | [OK] |
| 10 | §1.1 | Fork point = tip of `main` at iteration start | `c118c1c30f961921e41891df3318a2ccd2ceea54`, authored 2026-04-17 (2 days before fork), upstream version string `0.7.4.dev0` | [OK] |
| 11 | §4.1 | Slash commands live at `.claude/commands/<name>.md` | **MISMATCH**: upstream Claude integration writes to `.claude/skills/speckit-<name>/SKILL.md` following the `agentskills.io` spec; see `speckit/specify_cli/integrations/claude/__init__.py` (`commands_subdir: "skills"`, `registrar_config.dir: ".claude/skills"`, `extension: "/SKILL.md"`) and `speckit/specify_cli/integrations/base.py:1260-1320` (the `SkillsIntegration` base class). | [GAP-1] |
| 12 | §4.2 / §4.3 | Command invocations are `/sk.init`, `/sk.specify`, etc. (dot-delimited) and inherit bodies from `/speckit.specify` etc. | **MISMATCH**: In Claude skills mode, upstream commands are invoked as `/speckit-specify`, `/speckit-clarify`, etc. (hyphenated) because skills directory names are hyphenated and Claude Code surfaces skill names as their directory stem. `speckit/specify_cli/integrations/base.py:1311-1320` (`build_command_invocation`) explicitly maps `speckit.<x>` → `/speckit-<x>`. Upstream `README.md:121` acknowledges this: "Codex CLI in skills mode uses `$speckit-*` instead". | [GAP-1] |
| 13 | §4.1 (TODO OQ-3) | Command-file YAML frontmatter supports `allowed-tools:` and `$ARGUMENTS` substitution | **PARTIAL**: `$ARGUMENTS` is confirmed used across upstream command bodies. `allowed-tools:` is NOT a frontmatter key that Claude skills use; skills use the `agentskills.io` spec (keys: `name`, `description`, `argument-hint`, plus skills-registrar-specific metadata). This specific ERD assumption is therefore refuted for skills mode. Non-skills integrations (gemini, roo, etc.) may still support it. | [GAP-1] |
| 14 | §4.3 | v1 ships exactly 21 `/sk.*` commands | Upstream ships 9 command templates (`analyze, checklist, clarify, constitution, implement, plan, specify, tasks, taskstoissues`). sk's 21-command set adds 12 Harness-native commands and drops `implement` (replaced by `sk.go`). No blocker — but the adapter layer (T-11) must tolerate the 9-command upstream catalog, not a 21-command one. | [OK] |
| 15 | §1.3 | `sk_harness.speckit_adapter` is the single module that knows upstream paths | Not yet built; verified by counting that T-11 is the first task touching `speckit/*` paths. | [?] |
| 16 | §3 | `.claude/commands/` target for Harness commands | See GAP-1 impact: sk will likely need to register itself as a skills integration, meaning Harness commands live under `.claude/skills/sk-<name>/SKILL.md`, not `.claude/commands/sk.<name>.md`. T-19, T-20, T-21, T-22, T-23 are all affected. | [GAP-1] |
| 17 | §3 `scripts/` (upstream) | Not referenced in sk layout | Upstream ships `scripts/bash/*.sh` + `scripts/powershell/*.ps1` invoked by upstream `specify init`. sk has opted to reimplement in Python per ERD §2. If sk's init flow needs to drive `specify init` at runtime (it does not, per T-19's scope), we'd need these. Current plan is fine, but flagging so the Wave 4 implementer confirms. | [OK with note] |
| 18 | §16 | Decision-log markdown format | File exists and matches ERD §16.3 format — observed in current `.skspec/.progress/decision-log.md`. Not blocked by upstream. | [OK] |
| 19 | §2.3 distribution | sk ships as Claude Code skill droppable under `~/.claude/skills/sk/` | This aligns with observed upstream Claude skills-mode behaviour — in fact, the `/sk.*` → `/sk-*` rename is already enforced by Claude Code itself, not something sk needs to invent. Reinforces GAP-1 resolution direction. | [OK] |
| 20 | §3 | `.claude/commands/sk.init.md` etc. | Directly blocked by GAP-1. | [GAP-1] |

---

## Summary counts

- **Confirmed**: 14 (rows 1–10, 14, 17–19)
- **Mismatched**: 5 (rows 11, 12, 13, 16, 20 — all parts of a single architectural gap, GAP-1)
- **Undetermined**: 1 (row 15 — cannot be validated until T-11 ships)

---

## Proposals filed

- **`.skspec/.prd-pending/proposal-20260419T220000Z.md`** — covers GAP-1
  (rows 11, 12, 13, 16, 20). The gap is architectural: sk must register as a
  Claude **skills** integration, not a plain commands integration, and
  command invocations surface as `/sk-<name>` rather than `/sk.<name>`.

No other proposals needed: all other rows are [OK] or deferred.

---

## Non-blocking observations

These are not ERD mismatches but are worth recording:

- Upstream exposes **29 integrations** (claude, codex, gemini, copilot, …)
  via the `speckit/specify_cli/integrations/*/` subtree. sk Iteration 001
  targets Claude Code only. Future iterations can extend sk across
  integrations without copying more upstream code — the adapter layer
  (T-11) just routes per active integration.
- The `specify-cli` package includes a `core_pack` runtime-staging
  mechanism (`_locate_core_pack` in upstream `__init__.py:621`). sk does
  not re-implement this because sk's adapter layer (T-11) will resolve
  template paths directly from the fork tree, not from a bundled wheel.
- Upstream ships `AGENTS.md` (17 KB subagent definitions) and
  `spec-driven.md` (25 KB SDD methodology). sk's subagent templates
  (T-12, T-13) will reference these for context but won't copy them —
  they belong to upstream as educational material, not executable code.

---

**End of ERD validation for iteration 001 T-01.**
