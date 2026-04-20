# ERD — {{feature_name}} (Iteration {{iteration_id}})

**Feature Slug**: `{{iteration_slug}}` | **Date**: {{created_date}} | **Spec**: `.skspec/prd/spec-{{iteration_id}}.md`
**Input**: Feature specification from `.skspec/prd/spec-{{iteration_id}}.md`

<!--
  sk Harness ERD template. The ERD is the engineering / architecture /
  data design for an iteration (agent-owned per Constitution §II; can
  be rewritten freely with history snapshots landing under
  `.skspec/.erd/history/`). Output path: `.skspec/.erd/plan-{{iteration_id}}.md`.

  Writer: the `architect` subagent via `/sk.plan` or Phase 1 of `/sk.go`.
  This template supersedes the upstream spec-kit `plan.md` template by
  relocating the output tree and adding iteration-aware naming.
-->

## Summary

[Extract from feature spec: primary requirement + technical approach from research]

## Technical Context

<!--
  ACTION REQUIRED: Replace the content in this section with the technical details
  for the project. The structure here is presented in advisory capacity to guide
  the iteration process.
-->

**Language/Version**: [e.g., Python 3.11, Swift 5.9, Rust 1.75 or NEEDS CLARIFICATION]
**Primary Dependencies**: [e.g., FastAPI, UIKit, LLVM or NEEDS CLARIFICATION]
**Storage**: [if applicable, e.g., PostgreSQL, CoreData, files or N/A]
**Testing**: [e.g., pytest, XCTest, cargo test or NEEDS CLARIFICATION]
**Target Platform**: [e.g., Linux server, iOS 15+, WASM or NEEDS CLARIFICATION]
**Project Type**: [e.g., library/cli/web-service/mobile-app/compiler/desktop-app or NEEDS CLARIFICATION]
**Performance Goals**: [domain-specific, e.g., 1000 req/s, 10k lines/sec, 60 fps or NEEDS CLARIFICATION]
**Constraints**: [domain-specific, e.g., <200ms p95, <100MB memory, offline-capable or NEEDS CLARIFICATION]
**Scale/Scope**: [domain-specific, e.g., 10k users, 1M LOC, 50 screens or NEEDS CLARIFICATION]

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

[Gates determined based on `.skspec/.constitution.md`]

## Project Structure

### Documentation (this iteration)

```text
.skspec/
├── prd/spec-{{iteration_id}}.md        # PRD (user-owned)
├── .erd/plan-{{iteration_id}}.md       # This file (agent-owned)
├── .erd/history/                       # versioned snapshots of prior plan revisions
├── .task/tasks-{{iteration_id}}.md     # DAG (agent-owned, produced by /sk.tasks)
├── .task/tasks-{{iteration_id}}/       # per-task JSON sidecars
└── tests/test-plan-{{iteration_id}}.md # Acceptance + scenarios (user-owned)
```

### Source Code (repository root)
<!--
  ACTION REQUIRED: Replace the placeholder tree below with the concrete layout
  for this feature. Delete unused options and expand the chosen structure with
  real paths (e.g., apps/admin, packages/something). The delivered plan must
  not include Option labels.
-->

```text
# [REMOVE IF UNUSED] Option 1: Single project (DEFAULT)
src/
├── models/
├── services/
├── cli/
└── lib/

tests/
├── contract/
├── integration/
└── unit/

# [REMOVE IF UNUSED] Option 2: Web application (when "frontend" + "backend" detected)
backend/
├── src/
│   ├── models/
│   ├── services/
│   └── api/
└── tests/

frontend/
├── src/
│   ├── components/
│   ├── pages/
│   └── services/
└── tests/

# [REMOVE IF UNUSED] Option 3: Mobile + API (when "iOS/Android" detected)
api/
└── [same as backend above]

ios/ or android/
└── [platform-specific structure: feature modules, UI flows, platform tests]
```

**Structure Decision**: [Document the selected structure and reference the real
directories captured above]

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| [e.g., 4th project] | [current need] | [why 3 projects insufficient] |
| [e.g., Repository pattern] | [specific problem] | [why direct DB access insufficient] |
