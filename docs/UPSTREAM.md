# UPSTREAM — spec-kit fork metadata

This file pins and documents the sk Harness relationship with the upstream
`github/spec-kit` project. Constitution §VI ("Fork, don't rewrite") makes the
values below load-bearing: any merge of upstream improvements must begin by
reading this file.

---

## Pinned commit SHA

```
c118c1c30f961921e41891df3318a2ccd2ceea54
```

This is the tip of `main` observed at iteration 001 bootstrap. Authored at
`2026-04-17T14:33:38-05:00`; commit message `chore: release 0.7.3, begin
0.7.4.dev0 development (#2263)`. Upstream `pyproject.toml` at this SHA declares
`version = "0.7.4.dev0"`.

## Fork date

`2026-04-19`

## Upstream URL

<https://github.com/github/spec-kit>

## Upstream branch

`main`

## Rationale for SHA pinning (vs. tagged release)

ERD §1.1 + OQ-1 recommendation A: tip-of-main gives us the freshest templates
and integration surface, and pinning a SHA preserves reproducibility. The cost
is that we track a pre-release snapshot (`0.7.4.dev0`) rather than a tagged
version, but the upstream release cadence is fast enough that a tag would lag
material improvements to templates and the Claude integration.

If this trade-off becomes painful, revisit OQ-1 option B (named release tag).

---

## What was copied

Verbatim copies (no edits) were made from the upstream tree at the pinned SHA:

| Destination in sk/ | Source in spec-kit/ | Files |
|---|---|---|
| `speckit/specify_cli/` | `src/specify_cli/` | 52 (all Python) |
| `templates/upstream/` | `templates/` | 15 (md + json) |
| `LICENSE` | `LICENSE` | 1 (MIT) |

### `speckit/specify_cli/` subtree inventory

```
specify_cli/
├── __init__.py                  (CLI entry; declares `specify:main`)
├── agents.py
├── extensions.py
├── presets.py
├── integrations/
│   ├── base.py  + manifest.py + catalog.py
│   └── one subdirectory per supported agent integration:
│       agy, amp, auggie, bob, claude, codebuddy, codex, copilot,
│       cursor_agent, forge, gemini, generic, goose, iflow, junie,
│       kilocode, kimi, kiro_cli, opencode, pi, qodercli, qwen, roo,
│       shai, tabnine, trae, vibe, windsurf
└── workflows/
    ├── base.py + catalog.py + engine.py + expressions.py
    └── steps/
```

Noteworthy files referenced by later Harness tasks:

- `speckit/specify_cli/integrations/claude/__init__.py` — Claude Code
  integration; sets `commands_subdir: "skills"` and writes
  `speckit-<name>/SKILL.md` files under `.claude/skills/`. This is how sk
  surfaces `/speckit-*` commands in Claude Code. See
  `docs/ERD-VALIDATION.md` for the gap this exposes vs. ERD §4.
- `speckit/specify_cli/integrations/base.py` (lines 1260–1320) — defines
  the `SkillsIntegration` base class that Claude integration extends.

### `templates/upstream/` inventory

```
templates/upstream/
├── checklist-template.md
├── constitution-template.md
├── plan-template.md
├── spec-template.md
├── tasks-template.md
├── vscode-settings.json
└── commands/
    ├── analyze.md
    ├── checklist.md
    ├── clarify.md
    ├── constitution.md
    ├── implement.md
    ├── plan.md
    ├── specify.md
    ├── tasks.md
    └── taskstoissues.md
```

Each `commands/*.md` is a slash-command body template. The Harness adaptation
layer (ERD §1.3, implemented in T-11 as `sk_harness.speckit_adapter`) will
reference these files by path and never edit them in place.

---

## What was NOT copied, and why

The following upstream artifacts were intentionally excluded. Each exclusion
has a rationale tied to Constitution §VI ("additive fork") or to Phase-2/3
tasks that will author a replacement.

| Skipped | Reason |
|---|---|
| `.git/` | New repo gets its own history. Upstream history is referenced via this file's pinned SHA. |
| `.github/` (workflows, issue templates, etc.) | sk ships its own CI per T-27. Copying upstream workflows would run them against a fork that has different test targets and dependencies. |
| `.devcontainer/` | sk has not committed to a devcontainer story yet; revisit in v2. |
| `.gitattributes`, `.gitignore`, `.markdownlint-cli2.jsonc` | sk will author its own in T-27 / later docs pass; upstream defaults conflict with `.skspec/` tracking rule (T-27 AC). |
| `README.md` | sk authors its own in T-25 (Wave 6). The upstream README is 57 KB and describes `specify init`, which sk does not re-expose 1:1. |
| `AGENTS.md`, `CHANGELOG.md`, `CODE_OF_CONDUCT.md`, `CONTRIBUTING.md`, `DEVELOPMENT.md`, `SECURITY.md`, `SUPPORT.md`, `spec-driven.md` | Governance/docs bound to upstream's own org. sk will author project-appropriate replacements or link upstream from `docs/UPSTREAM.md` (this file). |
| `docs/` (upstream) | Would collide with sk's own `docs/` tree. sk authors its own architecture and command reference in T-25. |
| `extensions/`, `integrations/` (repo-root trees, not the `src/…/integrations/` package) | These are upstream's plugin-catalog surface — community-owned JSON and guidance. sk's Harness does not ingest them yet; revisit in v2 when plugin surface is defined. |
| `media/`, `newsletters/`, `presets/`, `workflows/` (top-level) | Marketing / release collateral and preset bundles that are orthogonal to the Harness bootstrap. The `workflows/speckit/workflow.yml` equivalent for sk's own workflow will be authored in later waves. |
| `scripts/` | Bash/PowerShell helpers used by upstream `specify init`. sk's Python-first architecture (ERD §2) will replace these; revisit if they prove needed. |
| `tests/` | sk ships its own `tests/` in later waves; mixing upstream tests with sk tests would confuse coverage gates (T-27 sets `--cov=sk_harness`). |
| `pyproject.toml` | sk authors its own in T-02 with the sk-Harness dependency set (ERD §2.4). Upstream `pyproject.toml` is also not copied in raw form, but its `force-include` mapping is documented here for reference. |
| `spec-kit.code-workspace` | VSCode workspace file for upstream's repo layout. |

### Upstream hatch-build `force-include` mapping (for reference)

Upstream bundles templates into its wheel at install time via:

```toml
[tool.hatch.build.targets.wheel.force-include]
"templates/checklist-template.md" = "specify_cli/core_pack/templates/checklist-template.md"
"templates/constitution-template.md" = "specify_cli/core_pack/templates/constitution-template.md"
"templates/plan-template.md" = "specify_cli/core_pack/templates/plan-template.md"
"templates/spec-template.md" = "specify_cli/core_pack/templates/spec-template.md"
"templates/tasks-template.md" = "specify_cli/core_pack/templates/tasks-template.md"
"templates/vscode-settings.json" = "specify_cli/core_pack/templates/vscode-settings.json"
"templates/commands" = "specify_cli/core_pack/commands"
"scripts/bash" = "specify_cli/core_pack/scripts/bash"
"scripts/powershell" = "specify_cli/core_pack/scripts/powershell"
"extensions/git" = "specify_cli/core_pack/extensions/git"
"workflows/speckit" = "specify_cli/core_pack/workflows/speckit"
"presets/lean" = "specify_cli/core_pack/presets/lean"
```

`sk_harness.speckit_adapter` (T-11) is responsible for preserving equivalent
path semantics at runtime; sk does not re-implement the `core_pack/` staging.

---

## Merge cadence (ERD §1.4)

### Weekly scan (active-development mode)

Every week during active iteration development:

```bash
git fetch upstream main
git log upstream/main..HEAD -- templates/ scripts/
git log HEAD..upstream/main -- templates/ scripts/
```

Skim the upstream-side commits. If a template or script changed in a way
that affects an sk-mirrored file (`templates/upstream/*`, future `scripts/`),
file an issue or a tracking entry in `.skspec/.knowledge/gotchas.md`. Do not
auto-apply.

### Quarterly rebase (post-v1)

Once sk v1 ships, promote the fork-point SHA on a quarterly cadence by:

1. Take snapshot (ERD §10 — `sk_harness.snapshots.capture` once built).
2. `git fetch upstream main && git checkout -b merge/upstream-YYYY-MM`.
3. Apply deltas selectively (see runbook below).
4. Update this file (new SHA, new date) + run the full test suite.
5. Log the merge to `.skspec/.progress/decision-log.md`.

### Never auto-merge

Upstream changes to command semantics (`/speckit.*` files in
`templates/upstream/commands/`) may require matching adjustments in the
Harness wrapper files (`.claude/commands/sk.*.md`, authored in later waves) or
in `sk_harness.speckit_adapter`. A human — or, in time, the `doc-updater`
subagent — reviews every merge before it lands on `main`.

---

## How to merge upstream (quick runbook)

```bash
# 1. Fetch and create a merge branch
git fetch upstream main
git checkout -b merge/upstream-$(date +%Y-%m)

# 2. Apply deltas for mirrored trees only
git checkout upstream/main -- src/specify_cli && \
  rm -rf speckit/specify_cli && mv src/specify_cli speckit/specify_cli && \
  git checkout upstream/main -- templates && \
  rm -rf templates/upstream && mv templates templates/upstream && \
  git checkout upstream/main -- LICENSE
```

After step 2, the working tree contains updated upstream files. Diff-review
every changed file, run `pytest` (once T-27 lands), update this file's SHA
and "What was copied" counts, and commit.

If upstream has renamed a mirrored path (e.g., moved `templates/commands/` to
`templates/skill-commands/`), the merge is non-mechanical — touch
`sk_harness.speckit_adapter` (single point of knowledge about upstream paths,
per ERD §1.3) before completing the merge.

---

**Pinned SHA must be updated atomically with the file tree.** If `speckit/` or
`templates/upstream/` ever diverge from the SHA on record, the Harness is in
an undocumented state — file a PRD proposal under `.skspec/.prd-pending/`
before continuing work.
