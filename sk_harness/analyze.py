"""Cross-artifact consistency analyzer for an iteration."""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from sk_harness.dag.graph import TaskGraph
from sk_harness.dag.parser import read_sidecars
from sk_harness.paths import Paths


@dataclass
class AnalyzeResult:
    iteration: str
    checks_passed: int = 0
    failures: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.failures


_HEADER = re.compile(r"^#{1,6}\s+(?:§?\d+[\w.]*|[\w.]+)\b")
_SECTION_ANCHOR = re.compile(r"§(\d+(?:\.\d+)*)")
_ID_IN_TESTPLAN = re.compile(r"\b(?:SM|OBS|INT)-\d+[a-zA-Z]?")


def _extract_section_ids(markdown: str) -> set[str]:
    """Return set of '§N' or 'N' identifiers from headers like '## N. Foo' or '### N.M'."""
    ids: set[str] = set()
    for line in markdown.splitlines():
        if line.startswith("#"):
            m = re.match(r"^#{1,6}\s+§?(\d+(?:\.\d+)*)\b", line)
            if m:
                ids.add(m.group(1))
    return ids


def _extract_erd_refs(ref_list: list[str]) -> set[str]:
    out = set()
    for r in ref_list:
        m = _SECTION_ANCHOR.search(r)
        if m:
            out.add(m.group(1))
    return out


def _extract_test_ids(test_plan_text: str) -> set[str]:
    return set(_ID_IN_TESTPLAN.findall(test_plan_text))


def analyze_iteration(paths: Paths, iteration: str) -> AnalyzeResult:
    r = AnalyzeResult(iteration=iteration)

    plan_path = paths.plan(iteration)
    tasks_md = paths.tasks(iteration)
    sidecar_dir = paths.task_sidecar_dir(iteration)
    test_plan = paths.test_plan(iteration)

    if not plan_path.exists():
        r.failures.append(f"ERD plan-{iteration}.md missing at {plan_path}")
    if not tasks_md.exists():
        r.failures.append(f"tasks-{iteration}.md missing at {tasks_md}")
    if not sidecar_dir.exists():
        r.failures.append(f"sidecar dir missing at {sidecar_dir}")
    if not test_plan.exists():
        r.failures.append(f"test-plan-{iteration}.md missing at {test_plan}")

    if r.failures:
        return r

    plan_sections = _extract_section_ids(plan_path.read_text(encoding="utf-8"))
    test_ids = _extract_test_ids(test_plan.read_text(encoding="utf-8"))
    sidecars = read_sidecars(sidecar_dir)
    if not sidecars:
        r.failures.append("no sidecars found")
        return r

    # Check 1: erd_refs in sidecars match plan sections
    for t in sidecars:
        refs = _extract_erd_refs(t.erd_refs)
        missing = refs - plan_sections
        if missing:
            r.failures.append(
                f"{t.id} references §{','.join(sorted(missing))} missing from plan-{iteration}.md"
            )
    if not any("references" in x for x in r.failures):
        r.checks_passed += 1

    # Check 2: acceptance_ids exist in test-plan
    accept_fail = []
    for t in sidecars:
        missing = [a for a in t.acceptance_ids if a not in test_ids]
        if missing:
            accept_fail.append(f"{t.id}: {','.join(missing)}")
    if accept_fail:
        r.failures.append("acceptance IDs absent from test-plan: " + " | ".join(accept_fail))
    else:
        r.checks_passed += 1

    # Check 3: no duplicate task IDs
    ids = [t.id for t in sidecars]
    if len(ids) != len(set(ids)):
        dups = [i for i in ids if ids.count(i) > 1]
        r.failures.append(f"duplicate task IDs: {sorted(set(dups))}")
    else:
        r.checks_passed += 1

    # Check 4: DAG acyclic
    try:
        TaskGraph(sidecars)
        r.checks_passed += 1
    except ValueError as e:
        r.failures.append(f"DAG invalid: {e}")

    return r


def format_report(result: AnalyzeResult) -> str:
    lines = [f"analyze iter={result.iteration}"]
    lines.append(f"- checks passed: {result.checks_passed}")
    if result.ok:
        lines.append("- all checks passed ✓")
    else:
        for f in result.failures:
            lines.append(f"- FAIL: {f}")
    return "\n".join(lines)
