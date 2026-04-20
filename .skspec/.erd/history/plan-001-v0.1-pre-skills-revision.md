# ERD — sk Harness MVP (Iteration 001)

**Version**: 0.1
**Date**: 2026-04-19
**Status**: Draft for TPM Phase 2 input
**Author**: architect-subagent (dispatched by TPM during iteration 001 bootstrap loop 0)
**Source PRD**: `prd/spec-001.md` v0.3
**Constitution**: `.constitution.md` (ratified 2026-04-19)

---

## 0. Reading Guide

This ERD is organized to map 1:1 onto Phase 2 task decomposition. Sections §4 through §16 are each candidate groupings for 2–4 tasks in `tasks-001.md`. §17 lists explicit deferrals; §18 lists open questions that may themselves become tasks or PRD-proposals depending on user input.

Every design decision here is answerable from the PRD and Constitution. Where it is not, the choice is marked with a `TODO(OQ-N)` cross-reference to §18.

---

## 1. Fork Strategy

### 1.1 Upstream and fork point

- **Upstream**: `github/spec-kit` (canonical URL: `https://github.com/github/spec-kit`)
- **Fork point**: tip of `main` at the time of iteration 001 kickoff. The task-level implementer will pin the exact commit SHA in `docs/UPSTREAM.md` when the fork is initialized (Task T-01).
- **Rationale**: taking `main` tip maximizes access to recent template improvements; pinning a SHA preserves reproducibility. See OQ-1 if user prefers a named release tag.

### 1.2 Upstream-mergeability principle (Constitution §VI)

The physical layout must minimize merge conflicts on future `git pull upstream main`:

1. **Do not rename or relocate upstream files in place.** Every speckit markdown / script / template stays where it originated.
2. **Rename exposure, not storage.** The `/sk.*` command prefix is achieved by a *thin adaptation layer* that registers new command files referencing the upstream originals, not by sed'ing the originals.
3. **All new Harness code lives in new directories** (`sk_harness/`, `templates/harness/`, `.claude/commands/sk.*.md`) so git diff surface between upstream and fork is almost entirely *additions*.
4. **Upstream templates are preserved verbatim** when a new file with a `-00N` naming convention is derived from them; derivation happens via a Python helper (`sk_harness.templating`) at runtime, not at fork time.

### 1.3 The adaptation layer

A single Python module, `sk_harness/speckit_adapter.py`, exports:

- `resolve_upstream_command(sk_name: str) -> Path` — maps `/sk.specify` back to the upstream `specify` template
- `rename_artifact(src: Path, iteration: str) -> Path` — maps `spec.md` → `spec-00N.md` and redirects `specs/<branch>/` → `.skspec/prd/`
- `inherit_body(upstream_md: Path, harness_header: dict) -> str` — concatenates harness frontmatter + upstream body for any command that is "speckit logic plus a harness entry point"

This is the **only** place upstream paths are referenced. When upstream renames something, we fix one file.

### 1.4 Merge cadence

- **Weekly scan** during active iteration development: `git fetch upstream main` + `git log upstream/main..HEAD -- templates/ scripts/`
- **Quarterly rebase** post-v1 ship
- **Never auto-merge**: upstream changes to `/speckit.*` command semantics may require matching changes to `/sk.*` wrappers; a human (or future doc-updater agent) reviews first

---

## 2. Runtime & Language

### 2.1 Choice: Python 3.11+

Matches spec-kit's existing runtime. Deviating would force a rewrite, violating Constitution §VI.

- **Minimum version**: 3.11 (for `tomllib` stdlib, `Self` type, structured `typing`)
- **Maximum tested**: 3.13 (CI matrix at v1 ships 3.11, 3.12, 3.13)

### 2.2 Package manager: `uv`

- `uv` is an order of magnitude faster than pip and is becoming the modern default in the Python packaging community
- Lockfile: `uv.lock` checked in
- Fallback: `pip install -e .` still works because we ship a standard `pyproject.toml`
- No Poetry or Hatch: adds lock-file conflict risk with upstream

### 2.3 Distribution

Three equally supported install channels (ordered by expected user frequency):

1. **Claude Code skill/plugin** (primary). sk ships as a directory droppable under `~/.claude/skills/sk/` or installable via `claude skill install ./`. The "commands" are `.claude/commands/sk.*.md` files that the Claude Code runtime picks up automatically.
2. **`pipx install sk-harness`** for the optional `sk` CLI helper (v2 item, but we reserve the name). In v1 any CLI invocation is a thin shell script.
3. **`brew install sk-harness`** deferred to v2 (OQ-9).

### 2.4 Dependencies (target set for v1)

| Library | Purpose | Why not hand-roll |
|--|--|--|
| `pydantic>=2` | state/JSON schema validation | already a transitive of speckit toolchain; battle-tested |
| `ruamel.yaml` | frontmatter in command markdown | preserves round-trip ordering, unlike PyYAML |
| `filelock` | `.skspec/.lock` cooperative lock | 80-line lockfile impl would be wrong |
| `rich` | `/sk.status`, `/sk.tasks graph` rendering | tree/graph output quality matters for DX |
| `networkx` | DAG parse, cycle detection, topo sort | five lines replace 200 of hand-rolled graph code |
| `jsonschema` | validate `.iterations.json`, `.agents.json`, state | catches hand-edit regressions per test INT-02/INT-20 |
| `click` | internal CLI helper used by slash-command scripts | speckit already uses it |

No new large runtime deps beyond this set. Per `common/patterns.md`, prefer mature libraries.

---

## 3. Repository Layout (post-fork)

Target layout of the sk source code repo (separate from `.skspec/` which is the *working artifact* of iteration 001):

```
sk/                                # repo root (this is /Users/a/cc/sk in bootstrap)
├── pyproject.toml
├── uv.lock
├── README.md
├── LICENSE                        # inherit speckit's LICENSE
├── docs/
│   ├── UPSTREAM.md                # pinned commit, merge notes
│   ├── architecture.md            # published ERD (derived from .skspec/.erd/plan-001.md at ship)
│   ├── commands.md                # user-facing command reference
│   └── harness-internals.md
│
├── speckit/                       # UPSTREAM: unchanged from spec-kit
│   ├── ... (verbatim)
│
├── templates/
│   ├── upstream/                  # UPSTREAM templates, verbatim
│   │   ├── spec.md
│   │   ├── plan.md
│   │   └── ...
│   ├── harness/                   # NEW: sk-specific templates
│   │   ├── spec-NNN.md            # spec-kit spec.md with -NNN naming added
│   │   ├── plan-NNN.md
│   │   ├── tasks-NNN.md
│   │   ├── test-plan-NNN.md
│   │   ├── skspec-skeleton/       # directory tree blueprint for /sk.init
│   │   └── agents/                # NEW: subagent prompt templates (§6)
│   │       ├── _base.md
│   │       ├── architect.md
│   │       ├── engineer.md
│   │       ├── qa.md
│   │       ├── security.md
│   │       ├── knowledge-extractor.md
│   │       ├── retro.md
│   │       └── tpm.md             # the outer-loop orchestrator prompt
│   └── agents-catalog.json        # built-in catalog layer (§5.5 of PRD)
│
├── sk_harness/                    # NEW: all Python code for the Harness layer
│   ├── __init__.py
│   ├── __main__.py                # entry for `python -m sk_harness`
│   ├── speckit_adapter.py         # the only module that knows upstream paths (§1.3)
│   ├── state/
│   │   ├── __init__.py
│   │   ├── models.py              # pydantic models for all JSON state files
│   │   ├── io.py                  # atomic read/write, locking (§7)
│   │   ├── migrations.py          # schema-version migrations (§15)
│   │   └── schemas/               # jsonschema files
│   │       ├── iterations.schema.json
│   │       ├── agents.schema.json
│   │       ├── state.schema.json
│   │       └── task.schema.json
│   ├── dag/
│   │   ├── __init__.py
│   │   ├── parser.py              # tasks-00N.md ↔ sidecar JSONs (§8)
│   │   ├── graph.py               # networkx wrapper
│   │   └── grammar.py             # markdown task grammar docs
│   ├── loop/
│   │   ├── __init__.py
│   │   ├── phases.py              # Phase 1..5 entry points
│   │   ├── micro_loop.py          # the Step 0..8 state machine (§9)
│   │   ├── dispatcher.py          # batch Task-tool invocation (§9)
│   │   ├── review.py              # multi-role review coordinator
│   │   ├── roster.py              # agent-roster reconciliation
│   │   └── termination.py         # deadlock / completion checks
│   ├── snapshots/
│   │   ├── __init__.py
│   │   ├── serializer.py          # §10
│   │   └── restore.py
│   ├── prd/
│   │   ├── __init__.py
│   │   ├── proposal.py            # .prd-pending/ writer + parser
│   │   └── merge.py               # accept/merge engine (§11)
│   ├── knowledge/
│   │   ├── __init__.py
│   │   └── extractor.py           # invoked by knowledge-extractor subagent
│   ├── observability/
│   │   ├── __init__.py
│   │   ├── decision_log.py        # append-only writer (§16)
│   │   └── events.py              # event type enum, schema
│   ├── headless/
│   │   ├── __init__.py
│   │   └── runner.py              # claude -p plumbing (§13)
│   ├── templating.py              # inherit_body, rename_artifact helpers
│   ├── paths.py                   # canonical .skspec/ path resolver
│   └── constants.py
│
├── .claude/
│   └── commands/                  # NEW: sk slash-command registration files
│       ├── sk.init.md
│       ├── sk.constitution.md
│       ├── sk.specify.md
│       ├── sk.clarify.md
│       ├── sk.plan.md
│       ├── sk.tasks.md
│       ├── sk.analyze.md
│       ├── sk.checklist.md
│       ├── sk.go.md
│       ├── sk.pause.md
│       ├── sk.resume.md
│       ├── sk.step.md
│       ├── sk.review.md
│       ├── sk.status.md
│       ├── sk.log.md
│       ├── sk.iteration.md
│       ├── sk.config.md
│       ├── sk.help.md
│       ├── sk.tasks.retry.md
│       └── sk.agent.md
│
└── tests/
    ├── unit/
    │   ├── test_state_io.py
    │   ├── test_dag_parser.py
    │   ├── test_snapshot.py
    │   ├── test_prd_merge.py
    │   └── test_roster.py
    ├── integration/
    │   ├── test_init_command.py
    │   ├── test_specify_flow.py
    │   ├── test_micro_loop_goldens.py
    │   └── test_headless.py
    ├── fixtures/
    │   ├── skspec_skeleton/
    │   ├── mock_task_responses/
    │   └── golden_iterations/
    └── conftest.py
```

**Design principle**: all new Python code lives in `sk_harness/`; all new templates in `templates/harness/`; all new command registrations in `.claude/commands/sk.*.md`. The upstream `speckit/` and `templates/upstream/` trees are read-only from the fork's perspective.

---

## 4. Command Registration

### 4.1 Claude Code command file format (assumed)

Claude Code picks up `.claude/commands/<name>.md` files with YAML frontmatter. Each file looks like:

```markdown
---
name: sk.specify
description: Draft or amend the PRD for the current or next iteration
allowed-tools: Read, Write, Edit, Bash, Grep, Glob, Task
argument-hint: "[--amend] [--accept <id>] [--reject <id>]"
---

# /sk.specify

<command body: instructions to the model running the slash command>

When invoked:
1. Call `python -m sk_harness.cli specify "$ARGUMENTS"` which writes/updates state
2. Read back the generated artifact and present to user
3. If action requires confirmation, ask user before proceeding

<detailed step-by-step instructions per PRD §5.2, 5.7>
```

TODO(OQ-3): confirm that current Claude Code supports `allowed-tools` frontmatter and `$ARGUMENTS` substitution as used by spec-kit. If not, fall back to plain prompts.

### 4.2 Renames from speckit

The adaptation layer (§1.3) lets each `/sk.*` file be short (20–40 lines each) and delegate to upstream body via `inherit_body()`. Example `sk.clarify.md`:

```markdown
---
name: sk.clarify
description: Run Q&A loop to refine the current iteration's spec
allowed-tools: Read, Write, Edit, Ask
---

# /sk.clarify

Apply the upstream /speckit.clarify discipline to the **current active iteration's** spec file (`prd/spec-00N.md`, where N is `.iterations.json.active`).

<inherited body from speckit/clarify.md, with path rewrites applied by sk_harness.speckit_adapter.rename_artifact>
```

This gives us: zero logic duplication for the 8 inherited commands, 13 fresh files for the 13 new Harness commands, 21 total.

### 4.3 Which commands exist in v1

Per PRD §6, exactly 21 commands (counts: 3 setup + 6 SDD + 5 execution + 3 observation + 2 iteration/help + 2 override):

Setup: `sk.init`, `sk.constitution`, `sk.config`
SDD: `sk.specify`, `sk.clarify`, `sk.plan`, `sk.tasks`, `sk.analyze`, `sk.checklist`
Execution: `sk.go`, `sk.pause`, `sk.resume`, `sk.step`, `sk.review`
Observation: `sk.status`, `sk.tasks` (list/show/graph modes), `sk.log`
Iteration: `sk.iteration` (list/complete/show), `sk.help`
Override: `sk.tasks.retry`, `sk.agent` (list/add/remove)

Mode dispatch (`list|show|graph`, `list|complete|show`, `list|add|remove`, `show|set|edit`) is parsed inside the command body, not by separate files; this keeps the file count at 20 (one file per primary command, multiplexed internally). Note: `sk.tasks.retry` is its own file because the dot in the URL-style name maps to a filename character.

### 4.4 Command invocation contract

Every `/sk.*` command body, after its preamble, invokes a Python subprocess:

```
python -m sk_harness.cli <command> [args...]
```

The CLI produces **structured output** (JSON over stdout, prefixed with `SK:`) that the command body parses and surfaces to the user. This makes the Python layer testable independently of Claude Code.

---

## 5. TPM Agent Design

### 5.1 What the TPM is

The TPM is a **single Claude Code Task invocation with `subagent_type: general-purpose`** spawned by `/sk.go`. It is **not** a separate process, not a daemon. Its lifetime is bounded by the `/sk.go` assistant turn chain.

TODO(OQ-2): confirm "one TPM per /sk.go call" vs "fresh TPM per loop iteration". Recommendation: single TPM, because context accumulates and state.json rehydration is cheap.

### 5.2 TPM prompt skeleton (`templates/harness/agents/tpm.md`)

```
You are the TPM (Technical Project Manager) subagent for the sk Harness.
Your scope is iteration {{iteration_id}} of the project at {{project_root}}.

## Non-negotiable constraints
- Read .constitution.md at the start of every loop; if user has edited it, obey the new version
- Never mutate files under prd/, tests/, docs/, references/ — those are user-owned
- Every decision appends to .progress/decision-log.md before the action completes
- Before any task dispatch, write a snapshot-eligible state to .snapshot/iter-{{iter}}/
- Pause at task boundaries, not inside tasks

## Your loop (Phase 3-4 micro loop per PRD §5.3)
For each iteration of the outer loop you control:

Step 0: Rehydrate state
  - Read .progress/state.json, .agents.json, .iterations.json
  - Re-read prd/spec-{{iter}}.md, .erd/plan-{{iter}}.md, tests/test-plan-{{iter}}.md
  - Re-read .knowledge/{patterns,gotchas,decisions}.md (excerpts relevant to current tasks)

Step 1: Agent roster reconciliation
  - Invoke sk_harness.loop.roster.reconcile() via Python subprocess
  - If the tool returns new_roster != current, write .agents.json, log decision

Step 2: Multi-role review (skip if loop_count == 0)
  - Dispatch architect / qa / security / engineer subagents IN PARALLEL (single assistant turn, multiple Task tool calls)
  - Aggregate their verdicts. If any flags blocking, branch accordingly in Step 3.

Step 3: Decision branch (first match wins). See PRD §5.3 Step 3 for the list.

Step 4: Compute ready set via sk_harness.dag.graph.ready_tasks()

Step 5: Dispatch batch
  - N = min(|ready_set|, max_concurrency)
  - Single assistant turn with N Task() calls
  - Each Task gets a per-role prompt loaded from templates/harness/agents/<role>.md with {{task_context}} interpolated

Step 6: Settle
  - For each returned result: update state.json, write snapshot on success, record retry on failure

Step 7: Knowledge extraction
  - For tasks flagged "notable" by the subagent's own output, dispatch knowledge-extractor subagent (parallel batch)

Step 8: Termination check

## Output contract at end of each turn (between loop iterations)
Emit a single JSON block:
{
  "loop_n": <int>,
  "decisions": [ { "action": "...", "rationale": "..." } ],
  "dispatched_tasks": ["T-07", "T-08"],
  "next_action": "continue" | "paused" | "iteration_complete" | "escalate",
  "state_dirty": true|false
}

The harness reads this envelope to update state.json and decide whether to start a new assistant turn (next loop iteration) or exit.
```

### 5.3 Context TPM loads each loop

Per Constitution §IV (observability) and §VII (agent-in-the-loop-for-execution), the TPM never works from stale context. Each loop's **Step 0** reloads:

- `.progress/state.json` (always)
- `.iterations.json` (always, small file)
- `.agents.json` (always)
- `prd/spec-{{iter}}.md` (always — cheap re-read catches user hand-edits per INT-01)
- `.erd/plan-{{iter}}.md` (always)
- `.task/tasks-{{iter}}.md` (always)
- `tests/test-plan-{{iter}}.md` (always)
- Selective knowledge excerpts: only entries tagged with domain keywords matching currently-running task titles (grep-based retrieval, not vector search)

Token budget per reload: target <4k tokens; if the sum exceeds budget, knowledge is truncated first, then design history.

### 5.4 How TPM parses sub-subagent results

Every dispatched specialist subagent emits its final reply with a machine-parseable envelope:

```
--- sk-result-begin ---
{ "task_id": "T-07", "status": "done"|"failed"|"needs_prd_change",
  "outputs": ["src/commands/pause.ts"], "notable": true|false,
  "error": null | "...", "prd_gap": null | "...", "hints": [] }
--- sk-result-end ---
```

The TPM regexes these envelopes out of each Task return, validates with pydantic (`sk_harness.observability.events.TaskResult`), and uses them to drive Step 6. If an envelope is missing or malformed, the task is marked `failed` with error `malformed_envelope` — the subagent's raw output is preserved in the decision log for debugging.

---

## 6. Subagent Prompt Templates

### 6.1 Directory

`templates/harness/agents/` — one markdown file per role. Files are loaded as *template strings* with Python's `string.Template` (chosen over Jinja2 for zero-deps and simplicity; the variable set is tiny).

### 6.2 Interpolation variables (common)

| Variable | Source |
|--|--|
| `${iteration_id}` | `.iterations.json.active` |
| `${iteration_slug}` | same |
| `${task_id}` | current task's `id` |
| `${task_title}` | current task's `title` |
| `${task_deps}` | comma-joined dep IDs |
| `${task_outputs}` | expected output paths |
| `${spec_excerpt}` | PRD section relevant to this task |
| `${erd_excerpt}` | ERD section relevant to this task |
| `${knowledge_excerpt}` | knowledge entries tagged with task's domain |
| `${constraints}` | constitution distilled to bullet list |
| `${max_retries}` | from `.agents.json` |
| `${output_envelope_spec}` | the `--- sk-result-begin ---` format spec |

### 6.3 Minimum viable role set for v1

Per PRD §6 and §5.3, v1 must ship these subagent prompt templates:

1. `_base.md` — included by all via `${base}`; defines the envelope format, logging contract, "never mutate user-owned files" rule
2. `tpm.md` — §5.2 above
3. `architect.md` — drafts/updates ERD; outputs `.erd/plan-00N.md` or a diff against it
4. `engineer.md` — implements code changes for one task; outputs files listed in `${task_outputs}`
5. `qa.md` — writes/updates tests per `tests/test-plan-00N.md`; never mutates `test-plan-00N.md` itself
6. `security.md` — review-only role in v1; emits findings, no writes
7. `knowledge-extractor.md` — appends to `.knowledge/patterns.md`, `gotchas.md`, or `decisions.md` based on what surfaced
8. `retro.md` — Phase 5; multi-role instance (architect/qa/engineer/pm perspectives) synthesized into `.knowledge/retrospectives/00N-retro.md`

TODO(§6.4): the PRD mentions `implementer` validator pairings with `tdd-guide` (PRD §8.4 sample). For v1 we map `agent: implementer` in task JSON to the `engineer` template; `validator: tdd-guide` triggers the `qa` template on the test side. Confirm terminology in Phase 2.

### 6.4 Template loading path

```python
def load_agent_prompt(role: str, context: dict) -> str:
    base = read("templates/harness/agents/_base.md")
    body = read(f"templates/harness/agents/{role}.md")
    return Template(body).safe_substitute({"base": base, **context})
```

All template rendering happens in `sk_harness.templating.render_agent_prompt`. The TPM calls this and passes the result as the Task tool's `prompt` argument.

---

## 7. State I/O Layer

### 7.1 Atomic write contract

All writes to files under `.skspec/.*` use this pattern:

```python
def atomic_write_json(path: Path, data: dict) -> None:
    # 1. Validate against jsonschema
    validate(data, load_schema_for(path))
    # 2. Write to sibling tempfile
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n")
    # 3. fsync + rename
    os.fsync(tmp.open("rb").fileno())
    tmp.replace(path)  # atomic on POSIX
```

Markdown files (`decision-log.md`, `tasks-00N.md`) use the same pattern; markdown validation is structural (headers match expected grammar) not schema-based.

### 7.2 Cooperative lock (`.skspec/.lock`)

Prevents two concurrent `/sk.go` invocations on the same project (e.g., user double-invokes in two terminals).

```python
from filelock import FileLock

LOCK_PATH = Path(".skspec/.lock")
with FileLock(LOCK_PATH, timeout=5) as _:
    # any state-mutating command holds this
    ...
```

Lock file content:
```json
{"pid": 12345, "command": "/sk.go", "acquired_at": "2026-04-19T10:23:00Z"}
```

Non-mutating commands (`/sk.status`, `/sk.log`, `/sk.tasks list`) skip the lock. `/sk.pause` uses a 1-second retry loop; if still contended, it writes `paused: true` to state via a side-channel flag file (`.skspec/.pause-requested`) that the lock-holder polls at Step 0 of each loop. This gives true pause-without-conflict semantics.

TODO(OQ-4): confirm `.lock` is wanted given Decision #3 "single process is enough". Keeping it defends against user error; removing it simplifies.

### 7.3 Concurrency model recap

- **One TPM subagent per `/sk.go`** (not multiple)
- **One Python process per slash-command invocation** (no long-running daemon)
- **Parallelism is Task-tool batch dispatch only** (Constitution §IX)
- **No threading, no multiprocessing** in `sk_harness.*` Python code
- State mutations are serial within a process; lock serializes across processes

### 7.4 Schema validation on read

Every load path goes through `sk_harness.state.io.load_validated(path)` which:

1. Reads the file
2. Looks up its schema by path pattern
3. Validates; on failure raises `SchemaViolationError` with line-level diagnostics
4. Returns the pydantic model instance

This catches user hand-edit regressions immediately (per SM-32, INT-02).

---

## 8. DAG Parser

### 8.1 `tasks-00N.md` grammar

Canonical minimal form (mirrors PRD §8.5 and §8.4):

```markdown
# Tasks — Iteration 001

## T-01: Scaffold sk_harness/ package

- deps: []
- agent: engineer
- validator: tdd-guide
- idempotent: true
- outputs: [sk_harness/__init__.py, pyproject.toml, uv.lock]

<free-form description / acceptance notes>

## T-02: Write state.io module

- deps: [T-01]
- agent: engineer
- validator: tdd-guide
- idempotent: true
- outputs: [sk_harness/state/io.py, sk_harness/state/models.py]

...
```

Grammar rules:
- Each task begins at the first `##` header that matches `T-\d{2,3}:`
- Fields are bullet lines at list depth 1 with `key: value` form; values can be JSON arrays or bare scalars
- `deps`, `outputs` are JSON arrays
- `idempotent` is `true|false`
- Unknown fields tolerated; unparseable fields logged as warnings
- Everything after the field block, until the next `## T-`, is the free-form description (stored as `description` in JSON sidecar)

### 8.2 Parsing pipeline

```
tasks-00N.md  ──[parser]──►  list[TaskDef (pydantic)]
                                │
                                ├──[write-back]──► .task/tasks-00N/T-NN.json  (sidecars)
                                │
                                └──[graph-build]──► networkx.DiGraph
```

The sidecars are **regenerated from the .md on every `/sk.tasks` run** (PRD §8.5). Human edits to the `.md` win. Human edits to sidecars are overwritten — this is explicitly documented and enforced by a staleness check at the top of every sidecar JSON (`"_generated_from": "tasks-00N.md", "_generated_at": "..."`).

### 8.3 Sidecar state fields

State mutations (`state`, `retries`, `last_error`, `snapshot`) live only in `.progress/state.json` per-task array, NOT in the sidecar. Sidecars are *definitional* and overwrite-safe; state.json is *runtime* and append-only-update.

### 8.4 Error handling

- **Cycle detected** in DAG → raise `CyclicTaskGraphError`, write diagnostic to decision-log with the cycle's node list, pause
- **Unknown dep ID** → raise `DanglingDependencyError`, log, pause
- **Malformed field** (e.g., `deps: T-01` instead of array) → warn, coerce if unambiguous (single-string → single-element array), otherwise fail
- **Empty file** → legal; zero tasks; TPM skips dispatch and moves to Phase 5

### 8.5 Hand-edit round-trip

Per test INT-02: user edits `tasks-00N.md` during pause.

On resume:
1. TPM re-parses `.md`
2. Diff against existing sidecars
3. If task added: create sidecar, add to state.json as pending
4. If task removed: archive its sidecar to `.task/tasks-00N/removed/`, mark state as `cancelled` in state.json (NOT deleted — Constitution §III)
5. If deps mutated: re-check for cycles, log the diff

Never silently drop user edits.

---

## 9. Batch Dispatcher

### 9.1 The single-turn N-call pattern

Per Constitution §IX and PRD §5.3 Step 5: in a single assistant turn, the TPM emits N parallel Task tool calls, then waits for all to return before proceeding. Claude Code guarantees parallel execution when tool calls are in the same turn.

Pseudocode executed inside the TPM subagent:

```
ready = compute_ready_set(state)
batch = ready[:max_concurrency]

# Single assistant turn — fire all:
results = [
    Task(subagent_type=task.agent, prompt=render_agent_prompt(task)),
    Task(subagent_type=task2.agent, prompt=render_agent_prompt(task2)),
    ...
]
# After turn completes, TPM parses envelopes from results
for r in results:
    envelope = parse_envelope(r.text)
    update_state(task_id=envelope.task_id, new_state=envelope.status, ...)
    if envelope.status == "done":
        write_snapshot(task_id=envelope.task_id)
```

### 9.2 Failure isolation

If Task #3 of 5 fails, the other four continue. No sibling-abort semantics. On Settle (Step 6), failed tasks are marked and eligible for retry on the next loop unless `retry_count >= max_retries`.

### 9.3 Non-idempotent retry handling (PRD §5.4)

If a non-idempotent task fails:
1. Look up the last snapshot taken *before* this task started
2. If present and restorable, TPM runs `snapshot.restore(before_task_id)` automatically
3. If no clean pre-task snapshot exists, mark task `blocked` with `needs_manual_restore` and pause with `pause_reason=non_idempotent_retry`

Escalation is explicit; user must choose `/sk.snapshot.restore` (v2) or `/sk.tasks.retry --force`.

### 9.4 Concurrency cap semantics

`max_concurrency=3` (default): at most 3 in-flight Task calls per batch. If `ready_set` has 7 tasks, batch is 3; remaining 4 wait for next loop. Per INT-10, `max_concurrency=10` with `|ready|=3` dispatches exactly 3 (no padding).

TODO(§9): the PRD doesn't say whether `max_concurrency` is per-iteration or per-global. Recommend per-global (a single knob in `.agents.json`). If future cross-iteration parallelism lands, revisit.

---

## 10. Snapshot Serialization

### 10.1 What a snapshot captures

Path: `.skspec/.snapshot/iter-00N/<task_id>-<YYYYMMDDTHHMMSSZ>.json`

```json
{
  "version": 1,
  "iter": "001",
  "task_id": "T-07",
  "captured_at": "2026-04-19T10:34:12Z",
  "captured_before": true,   // true = pre-task, false = post-task success
  "state_json": { ... full state.json content ... },
  "agents_json": { ... full .agents.json content ... },
  "iterations_json": { ... },
  "workspace_diff": {
    "base_commit": "abc123...",   // git HEAD at capture time
    "diff": "<unified diff of .skspec/ changes since base>"
  },
  "artifacts": {
    ".erd/plan-001.md.sha256": "...",
    ".task/tasks-001.md.sha256": "..."
  }
}
```

### 10.2 What it does NOT capture

- **Source code outside `.skspec/`** — that is covered by git commits made by the engineer subagent. Snapshots reference the git SHA; restoring means `git checkout <sha> -- <paths>` plus JSON overlay.
- **Subagent conversation history** — not available via Task tool API; the decision-log is the substitute.
- **.snapshot/ itself** — would explode in size; by design, snapshots reference prior snapshots by filename, they don't nest.

### 10.3 When snapshots are taken

- **Before Step 5 dispatch** of any non-idempotent task ("pre-task snapshot")
- **After Step 6 success** of any task (always, for rollback capability)
- **Before any ERD rewrite** (Phase 1 redesign branch)
- **Before iteration complete** (Phase 5 start)

### 10.4 Size bound

Target: each snapshot < 256 KB compressed. Typical case: state.json (~5 KB) + agents.json (~1 KB) + iterations.json (~1 KB) + tiny workspace diff = well under budget.

TODO(OQ-5): if `workspace_diff` exceeds 1 MB (bulk file changes), truncate with explicit note `"diff_truncated_at": 1048576` and fall back to "restore via git" narrative. Do not silently drop data.

### 10.5 Restore semantics

`sk_harness.snapshots.restore.restore(snapshot_path)`:

1. Validate snapshot version matches current schema (migrate if needed)
2. Write `state.json`, `.agents.json`, `.iterations.json` atomically
3. If `workspace_diff` present: prompt user before applying (restore is destructive per Constitution §III; we snapshot *before* restoring, creating a nested safety net)
4. Log the restore to decision-log with before/after state summaries
5. Return list of files touched

v1 does not expose `/sk.snapshot.*` user commands (deferred per PRD §6.7); TPM uses these functions internally for non-idempotent retries.

---

## 11. PRD Diff & Merge Engine

### 11.1 `.prd-pending/proposal-<ts>.md` structure

```markdown
---
proposal_id: 20260419T103412Z
filed_by_role: engineer
filed_by_task: T-07
filed_at: 2026-04-19T10:34:12Z
affects_sections: ["5.3", "5.5"]
status: pending   # pending | accepted | rejected
---

# PRD Proposal: <short title>

## Problem
<description of the spec gap discovered>

## Evidence
<code paths, observed behavior, test failures>

## Suggested Change
<the proposed diff to spec-00N.md, in unified diff format if mechanical; prose if semantic>

### Diff (if applicable)
```diff
--- a/prd/spec-001.md
+++ b/prd/spec-001.md
@@ -X,Y +X,Y @@
 existing
-old line
+new line
```

## Impact
- ERD sections to re-review: <list>
- Tasks to regenerate: <list>
- Knowledge entries implicated: <list>
```

### 11.2 Accept-merge algorithm (`/sk.specify --accept <id>`)

1. Acquire `.skspec/.lock`
2. Load proposal frontmatter
3. Validate `status: pending`
4. Take pre-merge snapshot
5. Apply the merge:
   - If proposal has machine-applicable diff: try `git apply --3way` on a copy of `spec-00N.md`
   - If conflict or no diff: fall back to "show user the two versions, ask to confirm manual merge" (PRD §5.7)
6. Write updated `spec-00N.md` atomically
7. Update proposal frontmatter to `status: accepted`, move to `.prd-pending/accepted/`
8. Clear `paused: true` if `pause_reason: prd_proposal`
9. Schedule Phase 1 partial re-review (flag in state.json: `"post_merge_rerun": "phase-1"`)
10. Log the accept to decision-log with the diff
11. Release lock

### 11.3 Reject flow (`/sk.specify --reject <id>`)

1. Move proposal to `.prd-pending/rejected/<id>.md` with status frontmatter updated
2. Clear pause if applicable
3. Log with reason (user-provided or empty)
4. The subagent that filed it is NOT retried automatically — the original task is marked `failed` with `last_error: prd_proposal_rejected`, user must `/sk.tasks.retry <id>` after deciding how to proceed (work around or refile with better evidence)

### 11.4 Multiple queued proposals

Per PRD §15 OQ #6 and test SM-63:

- Proposals are ordered by `filed_at`
- User is presented one at a time via `/sk.specify --list` (v1 subcommand) or `/sk.specify --accept <id>` explicitly
- **If two proposals edit overlapping lines**: second accept attempt fails with `OverlappingProposalError`; user must reject one or manually merge
- **If two proposals are orthogonal**: each accept is independent and each triggers its own Phase 1 partial re-review (may produce two ERD history snapshots)

TODO(OQ-8): the PRD open question asks "if multiple agents file proposals in a single batch, do they compose or conflict?" — recommendation above is "queue, resolve serially, overlap = user-mediated". Confirm with user.

---

## 12. Iteration Lifecycle Implementation

### 12.1 `/sk.iteration.complete`

1. Acquire lock
2. Verify `state.json.phase` is consistent: all tasks `done`, `current_batch` empty
3. If any tasks are `failed` or `pending` and user didn't pass `--force`: refuse, list blockers (test SM-73)
4. Dispatch Phase 5 retro (batch of 4 Task calls in one turn): `architect`, `qa`, `engineer`, `pm-retro` perspectives
5. Synthesize the four responses into `.knowledge/retrospectives/00N-retro.md`
6. Snapshot pre-archive state
7. Update `.iterations.json`:
   - `iterations[N].status: completed`
   - `iterations[N].completed_at: <ISO>`
   - `active: null`
8. Archive `.task/tasks-00N.md` → `.task/archive/00N/tasks-00N.md`
9. Archive `.task/tasks-00N/` (sidecars) → `.task/archive/00N/sidecars/`
10. Keep `.snapshot/iter-00N/` in place (cross-iteration forensic value)
11. Keep `.erd/plan-00N.md` in place (part of iteration's permanent record)
12. Update `.progress/state.json`: `phase: idle`, `active_iteration: null`
13. Update `.progress/milestones.md` row for this iteration
14. Log to decision-log with iteration summary
15. Release lock

### 12.2 Starting iteration N+1

Triggered by `/sk.specify` when `.iterations.json.active` is null:

1. Increment N
2. Create `prd/spec-00(N+1).md` from `templates/harness/spec-NNN.md`
3. Create `tests/test-plan-00(N+1).md` stub
4. Add entry to `.iterations.json.iterations[]`, set `active: "00(N+1)"`
5. Write `.progress/state.json` with `active_iteration: "00(N+1)"`, `phase: spec-drafted`
6. Log to decision-log
7. Display new spec to user for initial edit pass

Iteration N's `.erd/`, `.knowledge/`, `.snapshot/` remain available to iteration N+1 via the reading paths hard-coded in the architect template.

### 12.3 Retro dispatch detail

Four subagents in one batch (max_concurrency override honored — retro is always at least 4 concurrent even if `max_concurrency=1`, because retro is read-only):

- `retro.md` template instantiated 4x with `perspective: architect | qa | engineer | pm`
- Each writes a partial `.knowledge/retrospectives/00N-retro-<perspective>.md`
- A single synthesis Task call (general-purpose) merges the four partials into the canonical `00N-retro.md`
- Partials are archived, not deleted

---

## 13. Headless Mode

### 13.1 Entry point

`claude -p '/sk.go --until-pause' > sk.log` (PRD §5.10). The Claude Code `-p` flag runs a single print-mode session; we ensure `/sk.go` reaches a natural pause and then exits the session.

### 13.2 Flag plumbing

`/sk.go` accepts:
- `--until-pause` — when TPM reaches a pause (any `pause_reason`), emit final status and exit cleanly. Without this flag, TPM may wait for user input interactively when a proposal is filed (interactive mode).
- `--no-confirm` — any PRD proposal filed during the run is auto-rejected (logged with reason `headless-no-confirm`), loop continues. Without this flag, proposals cause a pause.

Both flags set state flags in `state.json.runtime_flags.{until_pause, no_confirm}` at the start of the run so any subagent that re-reads state sees them.

### 13.3 Exit code semantics

| Code | Meaning |
|--|--|
| 0 | Clean termination: iteration completed OR user-requested pause (non-error `pause_reason`) |
| 1 | General error (Python exception escaped, state corrupt, lock acquisition failed) |
| 2 | Escalation: `pause_reason=max_retries_exceeded` |
| 3 | Escalation: `pause_reason=deadlock` |
| 4 | Escalation: `pause_reason=prd_proposal` AND `--no-confirm` was NOT set |

TODO(OQ-6): PRD §5.10 only distinguishes 0 vs non-zero. Recommendation above gives finer-grained codes for CI/CD; user may prefer the simpler 0/1 convention. Decide.

### 13.4 Differences from interactive mode

- No `input()` calls anywhere in the call path
- User-facing prompts (e.g., "confirm ERD rewrite?") auto-proceed with the default per PRD §VII (agent-autonomous for ERD/tasks/knowledge)
- PRD-class confirmations: respect `--no-confirm` flag
- Progress is logged to stdout in structured form; `/sk.status` style output is also emitted every N loops (N=5 default)

---

## 14. Test Harness

### 14.1 What's hard to test

The only hard-to-test piece is the TPM's orchestration of Task-tool calls — those are Claude Code runtime features, not plain functions.

### 14.2 Layer-by-layer test strategy

| Layer | Tool | How |
|--|--|--|
| `sk_harness.state.*` | pytest unit | straightforward; pydantic models, atomic write, schema validation |
| `sk_harness.dag.*` | pytest unit | fixture markdown files, assert parse output and graph topology |
| `sk_harness.prd.merge` | pytest unit | fixture before/after spec files, assert diff apply |
| `sk_harness.snapshots.*` | pytest unit | capture + restore round-trip using tmp_path |
| `sk_harness.loop.*` | pytest with **mock Task tool** | see §14.3 |
| Slash commands | integration tests | spawn a subprocess invoking `python -m sk_harness.cli`, assert filesystem side effects |
| End-to-end (TPM loop) | golden fixtures | see §14.4 |

### 14.3 Mocking Task-tool calls

The `sk_harness.loop.dispatcher` module depends on an abstract `AgentRunner` interface:

```python
class AgentRunner(Protocol):
    def run(self, subagent_type: str, prompt: str) -> AgentResult: ...
```

Production impl calls Claude Code's Task tool. Test impl (`tests/fixtures/mock_runner.py`) looks up pre-recorded responses keyed by `(subagent_type, task_id)`. This lets us run the full Phase 1..5 loop deterministically in CI, reading pre-recorded envelopes from `tests/fixtures/mock_task_responses/`.

### 14.4 Golden-path integration tests (v1 minimum)

`tests/integration/test_micro_loop_goldens.py` runs:

1. **Trivial 3-task iteration** (SM-20): creates a fresh `.skspec/` in `tmp_path`, pre-populates spec/plan/tasks, runs `/sk.go` with mock runner, asserts final state matches golden JSON and decision-log contains 12+ expected entries.
2. **Parallelizable DAG** (SM-21): 1 → {2,3} → 4 graph, asserts T-02 and T-03 are in the same batch in decision-log.
3. **Failure + retry** (SM-40, SM-41): mock response sequence produces fail-fail-fail for T-02, asserts final state `paused, pause_reason=max_retries_exceeded`.
4. **PRD proposal flow** (SM-60, SM-61): mock response for T-03 files a proposal, asserts pause, simulates `/sk.specify --accept`, asserts resume and ERD re-review.
5. **Pause-resume** (SM-30, SM-31): assert identical state before-and-after serialization round-trip.

Five goldens is v1 minimum; more added as regressions surface per test-plan §5.

TODO(OQ-7): is running real Task-tool calls in CI desirable at all? Recommendation: no for PR gates (slow, expensive); yes for nightly against a real Claude Code instance. Confirm with user.

### 14.5 Coverage target

Per `rules/common/testing.md`: 80% line coverage minimum over `sk_harness/`. Enforced via `pytest --cov=sk_harness --cov-fail-under=80` in CI.

---

## 15. Schema Versioning & Migrations

### 15.1 `.skspec/.version`

Single line, semantic version. Current: `0.3.0` (matches PRD v0.3 state schemas).

### 15.2 Version check on every command

`sk_harness.cli` entry point, before any business logic:

```python
expected = sk_harness.__version__.schema_version   # "0.3.0"
actual = read_version_file()
if actual != expected:
    if is_compatible(actual, expected):
        warn_and_continue()
    else:
        refuse_with_migration_hint()
```

Compatibility rule: same major.minor = compatible; different = must run `/sk.lint --migrate` (v2) or user edits manually.

### 15.3 Migration shape (for v2 authoring)

Migrations live in `sk_harness/state/migrations.py` as ordered pure functions:

```python
@migration(from_="0.3.0", to="0.4.0")
def add_token_budget_field(state: dict) -> dict: ...

@migration(from_="0.4.0", to="1.0.0")
def rename_paused_reason_field(state: dict) -> dict: ...
```

v1 ships with zero migrations (0.3.0 is the first schema). The infrastructure is in place so v2 authors don't invent it ad hoc.

### 15.4 Backwards incompat = schema minor bump

Rule: any field removal, field rename, or semantic meaning change bumps minor. Additions (new optional fields) bump patch. This is stricter than SemVer because state files are parsed by older binaries.

---

## 16. Observability

### 16.1 Decision-log writer (`sk_harness.observability.decision_log`)

```python
def append_decision(
    iter: str,
    loop: int,
    actor: str,          # "tpm" | "architect-subagent" | "user" | "engineer:T-07" | ...
    decision: str,        # short verb phrase, <80 chars
    rationale: str,       # multi-line markdown
    metadata: dict|None = None,
) -> None:
    """Append-only. Opens decision-log.md in 'a' mode; fsyncs.
    Never rewrites existing entries."""
```

### 16.2 Required fields per entry

Every entry MUST include:
- Timestamp (ISO-8601 UTC)
- Iteration ID
- Loop number (0 for pre-loop actions like `/sk.init`)
- Actor (role + optional task ID)
- Decision (short verb phrase)
- Rationale (prose)

Optional but encouraged:
- `metadata.affected_files: []`
- `metadata.task_id: str`
- `metadata.subagent_dispatch: {role, subagent_type, prompt_hash}`
- `metadata.before/after: {state snippet}` for state-mutating entries
- `metadata.snapshot_ref: path` when a snapshot was taken

### 16.3 Markdown format

```markdown
## <ISO timestamp> · iter=<ID> · loop=<N> · actor=<name> · decision=<short>

<rationale prose, possibly multi-line>

<optional metadata block as indented JSON>
```

One entry = one level-2 heading. `/sk.log --tail N` parses by counting `##` boundaries.

### 16.4 What MUST be logged

Per Constitution §IV, these events are mandatory:
- Every TPM loop start (even if no actions taken)
- Every roster reconciliation result (even "no change")
- Every batch dispatch (with task IDs)
- Every task state transition (pending→running→done/failed)
- Every snapshot taken
- Every ERD rewrite
- Every PRD proposal filed/accepted/rejected
- Every pause event (with reason)
- Every iteration start and complete
- Every schema-version check (only on mismatch)

### 16.5 Log file rotation

Not implemented in v1 (PRD §10: diffable, mergeable — large files stay readable). If the log exceeds 10 MB it is split via `decision-log-00N.md` rotation per iteration, with the active iteration always writing to `decision-log.md`. TODO(§16): move this to v2 explicitly.

---

## 17. Out of Scope for plan-001 (deferred items)

Explicitly not designed here:

1. **Team collaboration**: locks beyond single-process, claim/release, multi-user state merge (PRD §13)
2. **Real multi-process concurrency**: threading/process pools inside Python (Constitution §IX + PRD Decision #3)
3. **Plugin system** for third-party agent types beyond catalog edits (PRD §13)
4. **Web UI / dashboard / TUI** (PRD §2.2)
5. **Cloud state storage** (PRD §2.2)
6. **Token-cost enforcement** — visibility only in v1 per PRD §10
7. **Standalone `sk` CLI binary** beyond module invocation (`python -m sk_harness`); deferred to v2 per Decision #15
8. **`/sk.snapshot.*` user commands** (PRD §6.7) — restore is TPM-internal only in v1
9. **`/sk.knowledge.promote`** cross-project lift (PRD §5.6)
10. **`/sk.diff`, `/sk.lint`, `/sk.export`, `/sk.import`** (PRD §6.7)
11. **`/sk.agent.lock`** read-only roster entries (PRD §5.5)
12. **`/sk.tasks.add|skip|cancel`** beyond `.retry` (PRD §6.7)
13. **Cross-iteration parallelism** (PRD §13)
14. **ERD `evolution.md` auto-curation** (optional per PRD §7; v1 writes entries manually when TPM rewrites ERD, no cross-iter synthesis)
15. **Log rotation** (see §16.5)
16. **Subagent prompt per-project customization** (PRD §15 OQ #2)
17. **`/sk.review` scoping to a single role** (PRD §15 OQ #4)
18. **Long-task progress streaming** (PRD §15 OQ #3, incompatible with task-level pause granularity in v1)
19. **Token-cost tally on subagent invocations** — log the dispatch, not the cost (PRD §10)
20. **Windows native support** — best-effort only; WSL is the recommended path per PRD §10

---

## 18. Open Questions

Each is labeled `OQ-N`. Recommendation given; user / next review decides.

### OQ-1: Fork commit pinning
**Options**:
- A) Tip of `main` at iteration start (my current recommendation), pin SHA
- B) Named release tag (e.g., `v0.x`)
- C) Vendored snapshot (no live remote)

**Recommendation**: A. Most flexible, lowest cost, enables §1.4 merge cadence. User may override to B if they want stability over recency.

### OQ-2: TPM lifetime
**Options**:
- A) One TPM subagent per `/sk.go` call, loops internally across multiple assistant turns (current recommendation)
- B) Fresh TPM subagent per loop iteration; harness drives the outer loop
- C) Hybrid: one TPM but force a full context reload if conversation exceeds M tokens

**Recommendation**: A. Aligned with Claude Code's Task-tool model. Context bloat is mitigated by Step 0's selective re-read. Revisit if context pressure observed in practice.

### OQ-3: Claude Code command-file frontmatter support
**Options**:
- A) Use `allowed-tools: ...` and `$ARGUMENTS` as spec-kit does (current recommendation)
- B) Use plain command bodies without frontmatter
- C) Invent our own registration system

**Recommendation**: A, pending verification by whichever implementer task first touches `.claude/commands/`. If unsupported, fall back to B for v1; revisit in v2.

### OQ-4: `.skspec/.lock` file
**Options**:
- A) Ship filelock-based cooperative lock (current recommendation)
- B) No lock; trust single-user single-process convention
- C) OS-advisory lock only (flock on a sentinel fd)

**Recommendation**: A. Low cost, defends against user error, doesn't contradict Decision #3.

### OQ-5: Snapshot size bounds
**Options**:
- A) Soft cap 256 KB, truncate diff with explicit note (current recommendation)
- B) Hard cap, fail snapshot
- C) No cap, compress aggressively

**Recommendation**: A. Failing snapshots violates Constitution §III (reversibility). Truncation with explicit record preserves 99% of forensic value.

### OQ-6: Headless exit codes
**Options**:
- A) Five codes: 0 clean, 1 error, 2 max_retries, 3 deadlock, 4 prd_proposal (current recommendation)
- B) Two codes: 0 clean, 1 anything-else
- C) Three codes: 0 clean, 1 internal-error, 2 escalation

**Recommendation**: A for CI/CD richness; user may override to B for simplicity.

### OQ-7: Real Task-tool calls in CI
**Options**:
- A) Never (mock everything); nightly manual smoke against real Claude Code (current recommendation)
- B) Real calls in nightly CI against a live Claude Code
- C) Real calls in PR gates (most expensive)

**Recommendation**: A for v1; consider B once iteration 2 proves the flow is stable and not token-bankrupting.

### OQ-8: Overlapping PRD proposals
**Options**:
- A) Serialize by filed_at, refuse overlapping accepts (current recommendation)
- B) Auto-merge when 3-way possible, escalate otherwise
- C) User resolves offline, re-files combined proposal

**Recommendation**: A. Matches PRD §15 OQ #6 defaulting to safety.

### OQ-9: Homebrew distribution
**Options**:
- A) Defer entirely to v2 (current recommendation)
- B) Ship a homebrew-tap repo in v1 alongside pipx
- C) Ship formula upstream after 50 users

**Recommendation**: A. Claude Code skill install is the primary surface in v1; pipx is the secondary; brew is marketing, not function.

---

## 19. Task-Decomposition Preview for Phase 2

This ERD maps to approximately **24 tasks**, grouped into 6 implementation waves. This preview is advisory for Phase 2; the engineer+qa subagents will produce the authoritative `tasks-001.md`.

```
Wave 1: Scaffolding (3 tasks)
  T-01  fork speckit, set up pyproject, pin upstream SHA, docs/UPSTREAM.md
  T-02  scaffold sk_harness/ package, tests/, CI config
  T-03  templates/upstream/ copy-in + templates/harness/ stubs

Wave 2: State & I/O foundation (4 tasks)
  T-04  sk_harness.state.models + jsonschema files
  T-05  sk_harness.state.io (atomic write, lock, load_validated)
  T-06  sk_harness.observability.decision_log writer
  T-07  sk_harness.paths + constants

Wave 3: DAG & snapshots (3 tasks)
  T-08  sk_harness.dag.parser (markdown ↔ JSON sidecars)
  T-09  sk_harness.dag.graph (networkx wrapper, ready-set, cycle check)
  T-10  sk_harness.snapshots.{serializer,restore}

Wave 4: Subagent templates & adapter (3 tasks)
  T-11  sk_harness.speckit_adapter + sk_harness.templating
  T-12  templates/harness/agents/{_base,tpm,architect,engineer,qa,security}.md
  T-13  templates/harness/agents/{knowledge-extractor,retro}.md + agents-catalog.json

Wave 5: Commands (7 tasks — one per command file group)
  T-14  .claude/commands/sk.init.md + sk_harness.cli subcommand
  T-15  sk.constitution + sk.config
  T-16  sk.specify (incl. --amend, --accept, --reject, .prd-pending flow)
  T-17  sk.clarify + sk.plan + sk.tasks + sk.analyze + sk.checklist (inherited)
  T-18  sk.go + sk.pause + sk.resume + sk.step + sk.review
  T-19  sk.status + sk.log + sk.iteration + sk.help
  T-20  sk.tasks.retry + sk.agent

Wave 6: Loop integration & headless (4 tasks)
  T-21  sk_harness.loop.{phases,micro_loop,dispatcher}
  T-22  sk_harness.loop.{review,roster,termination}
  T-23  sk_harness.prd.{proposal,merge} + sk_harness.knowledge.extractor
  T-24  sk_harness.headless.runner + integration goldens
```

Rough dependency graph:

```
T-01 → T-02 → T-03
               ├── T-04 → T-05 → T-06 → T-07
               │                           ├── T-08 → T-09
               │                           └── T-10
               └── T-11 → T-12 → T-13
                            ├── T-14 ...→ T-20  (all depend on T-07 + T-11)
                            └── T-21 → T-22 → T-23 → T-24  (depends on T-05..T-13)
```

Total: **24 tasks**, within the 10–30 range specified by the dispatching TPM. Engineer+qa subagents in Phase 2 may adjust (split T-17 into per-command, merge Wave 2 tasks if trivial, etc.).

---

**End of ERD plan-001 v0.1. Awaiting Phase 2 task-decomposition dispatch.**
