---
proposal_id: 20260420T050821Z
filed_by_role: implementer
filed_by_task: T-01
filed_at: 2026-04-20T05:08:21Z
affects_sections: ["ERD §4 (all)", "ERD §3 (`.claude/commands/` target subtree)", "tasks-001 T-19, T-20, T-21, T-22, T-23 (outputs list)"]
status: pending
---

# PRD/ERD Gap Discovered During T-01

## Problem

ERD §4 ("Command Registration") assumes that Claude Code slash commands for
the sk Harness are registered by dropping files at
`.claude/commands/<name>.md` with names like `/sk.init`, `/sk.specify`. ERD §3
(the repo-layout diagram, lines 185–206) lists 20 such files.

In reality, at upstream SHA `c118c1c30f961921e41891df3318a2ccd2ceea54`, the
Claude Code integration in spec-kit installs commands as **Agent Skills**
under `.claude/skills/speckit-<name>/SKILL.md`, and the invocation surface is
hyphenated: `/speckit-specify`, not `/speckit.specify`. This is enforced by
Claude Code itself via the `agentskills.io` specification that upstream
adopted — it is not a choice upstream can revert, and it is not something
sk can work around with frontmatter tweaks.

Because sk is additive on top of upstream (Constitution §VI, ERD §1.2), sk
should follow the same registration model Claude Code supports. Otherwise:

1. Users who install sk as a Claude Code skill will see `/sk-init`, not
   `/sk.init` (Claude Code substitutes dots for hyphens automatically).
2. The inherited commands (plan, tasks, clarify, analyze, checklist) already
   show up as `/speckit-*` in skills mode — mixing `/sk.*` wrappers with
   `/speckit-*` inheritors would create a schizophrenic UX.
3. The adapter layer (ERD §1.3) described `inherit_body` as copying upstream
   body into an sk-prefixed file. But upstream bodies target skill
   registrars, not command registrars — we'd need to reformat the body's
   frontmatter for the `agentskills.io` spec, which is a code path the ERD
   did not anticipate.

## Evidence

All paths are in the pinned upstream tree, now at `/Users/a/cc/sk/speckit/`:

1. **`speckit/specify_cli/integrations/claude/__init__.py` lines 41–54**:

   ```python
   class ClaudeIntegration(SkillsIntegration):
       key = "claude"
       config = {
           "name": "Claude Code",
           "folder": ".claude/",
           "commands_subdir": "skills",          # ← not "commands"
           "install_url": "...",
           "requires_cli": True,
       }
       registrar_config = {
           "dir": ".claude/skills",              # ← not ".claude/commands"
           "format": "markdown",
           "args": "$ARGUMENTS",
           "extension": "/SKILL.md",             # ← directory-plus-SKILL.md, not flat file
       }
   ```

2. **`speckit/specify_cli/integrations/base.py` lines 1260–1320**:

   ```python
   class SkillsIntegration(IntegrationBase):
       """Concrete base for integrations that install commands as agent skills.

       Skills use the ``speckit-<name>/SKILL.md`` directory layout following
       the `agentskills.io <https://agentskills.io/specification>`_ spec.
       """
       # …
       def build_command_invocation(self, command_name: str, args: str = "") -> str:
           """Skills use ``/speckit-<stem>`` (hyphenated directory name)."""
           stem = command_name
           if "." in stem:
               stem = stem.rsplit(".", 1)[-1]
           invocation = f"/speckit-{stem}"              # ← hyphen
   ```

3. **Upstream `README.md` line 121**:

   > Most agents expose spec-kit as `/speckit.*` slash commands; **Codex CLI
   > in skills mode uses `$speckit-*` instead**.

   Claude Code IS a skills-mode integration (it extends `SkillsIntegration`),
   so the same "hyphens in skills mode" rule applies.

4. **Non-skills contrast**: `speckit/specify_cli/integrations/gemini/__init__.py`
   lines 11–16 shows `"commands_subdir": "commands"` + `"dir": ".gemini/commands"`.
   Gemini and similar integrations DO use flat-file `.<agent>/commands/<name>.md`
   layout — ERD §4 is correct for *those* integrations, wrong for Claude.

## Suggested Change

### ERD §4.1 — replace the example frontmatter block

Instead of the current (incorrect for Claude Code):

```markdown
---
name: sk.specify
description: Draft or amend the PRD for the current or next iteration
allowed-tools: Read, Write, Edit, Bash, Grep, Glob, Task
argument-hint: "[--amend] [--accept <id>] [--reject <id>]"
---
```

Use the agentskills.io layout Claude Code expects. Each Harness command is a
directory under `.claude/skills/` containing a single `SKILL.md`:

```
.claude/skills/sk-specify/SKILL.md
```

with frontmatter modeled on the agentskills.io spec (keys: `name`,
`description`, plus skill-registrar-specific metadata such as `argument-hint`
and `source`). The `allowed-tools` key is NOT a recognized skill frontmatter
field in this spec and should be removed from ERD §4.

### ERD §4.2 / §4.3 — rename command scheme

Replace all `/sk.<name>` references with `/sk-<name>` (hyphenated).
Internally, task IDs, state JSON keys, and decision-log entries may still use
dot notation — the rename applies only to **user-facing slash invocations**.
Affected ERD lines: 185–206 (file list), 278 ("8 inherited, 13 fresh, 21
total" — count stays; just rename), 283–290 (the catalog, rename all rows).

### ERD §3 — retarget the `.claude/commands/` subtree

Replace:

```
├── .claude/
│   └── commands/                  # NEW: sk slash-command registration files
│       ├── sk.init.md
│       ├── sk.constitution.md
│       ├── …
```

with:

```
├── .claude/
│   └── skills/                    # NEW: sk skill directories (agentskills.io spec)
│       ├── sk-init/SKILL.md
│       ├── sk-constitution/SKILL.md
│       ├── …
```

### ERD §1.3 — expand the adapter layer

`sk_harness.speckit_adapter.inherit_body` must now translate between
`.claude/skills/speckit-<x>/SKILL.md` bodies (upstream) and
`.claude/skills/sk-<x>/SKILL.md` bodies (Harness). This is still a one-file
concentration of upstream-path knowledge, but the translation is non-trivial
(frontmatter reformat, not just path rewrite).

### ERD §4 (TODO OQ-3) — resolve in the negative

Resolve OQ-3 with: "Claude Code does NOT honor `allowed-tools:` frontmatter
on skills; skills use the `agentskills.io` frontmatter set. Remove
`allowed-tools` from all Harness command bodies. `$ARGUMENTS` substitution
IS honored and can stay."

## Impact

### Tasks affected (tasks-001.md)

- **T-19** (`/sk.init`, `/sk.constitution`, `/sk.config`): outputs change
  from `.claude/commands/sk.init.md` etc. to
  `.claude/skills/sk-init/SKILL.md` etc. Integration test in the task's
  spec must be updated to assert the new layout.
- **T-20** (SDD commands): same rename pattern; plus the `inherit_body`
  flow in T-11 must be extended to translate skill frontmatter. Upstream
  inherited commands go from `/speckit.plan` invocations (documented) to
  `/speckit-plan` (observed in skills mode) — cross-reference in the
  command body must match.
- **T-21, T-22, T-23**: all `.claude/commands/*.md` outputs rename to
  `.claude/skills/*/SKILL.md`.
- **T-11**: scope grows from "path rewrite" to "path rewrite + frontmatter
  reformat". Complexity rises from S/M → M/L depending on how much of the
  `SkillsIntegration.setup` logic we re-use vs. reimplement.

### ERD sections to re-review

- §1.2 (upstream-mergeability): the principle still holds, but the
  concrete example in §1.2.2 ("renamed exposure, not storage") needs a
  Claude-specific illustration using the skills layout.
- §1.3 (adapter layer): expand `inherit_body` contract.
- §3 (repo layout): retarget `.claude/` subtree.
- §4 (all four subsections).
- §6.4 (template loading path): unchanged, but the rendered prompt for
  `.claude/skills/<role>/SKILL.md` needs the skill frontmatter, not the
  old `allowed-tools:` block.

### Knowledge entries implicated

- None yet (`.knowledge/` is empty). When ERD is updated, add a
  `.knowledge/decisions.md` entry titled "sk registers as Claude skills
  integration, not commands" so Iteration 002+ does not re-discover this.

### No downstream rollback

This proposal does not require rolling back any already-completed task.
T-01 wrote `docs/UPSTREAM.md`, `docs/ERD-VALIDATION.md`, and copied
upstream files — all of that is layout-neutral and remains valid regardless
of the ERD §4 outcome.

---

**Recommendation to TPM**: accept this proposal before Wave 4 begins
(before T-19 dispatches). Accepting it after T-19 has authored files under
`.claude/commands/` would require repairing those outputs. Accepting it now
is cheap.
