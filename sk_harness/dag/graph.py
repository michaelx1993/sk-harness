"""DAG graph wrapper around networkx for ready-set, cycle, depth queries."""

from __future__ import annotations

import networkx as nx

from sk_harness.state.models import TaskMeta, TaskState


class TaskGraph:
    def __init__(self, tasks: list[TaskMeta]) -> None:
        self.tasks: dict[str, TaskMeta] = {t.id: t for t in tasks}
        self.g = nx.DiGraph()
        for t in tasks:
            self.g.add_node(t.id)
        for t in tasks:
            for d in t.deps:
                if d not in self.tasks:
                    raise ValueError(f"Task {t.id} depends on unknown task {d}")
                self.g.add_edge(d, t.id)
        if not nx.is_directed_acyclic_graph(self.g):
            cycle = list(nx.find_cycle(self.g))
            raise ValueError(f"Cycle detected in tasks DAG: {cycle}")

    def ready_set(self, states: dict[str, TaskState]) -> list[str]:
        out = []
        for tid in nx.topological_sort(self.g):
            st = states.get(tid, TaskState.pending)
            if st != TaskState.pending:
                continue
            deps_ok = all(states.get(d) == TaskState.done for d in self.g.predecessors(tid))
            if deps_ok:
                out.append(tid)
        return out

    def topological(self) -> list[str]:
        return list(nx.topological_sort(self.g))

    def critical_path(self) -> list[str]:
        return nx.dag_longest_path(self.g)

    def depth(self) -> int:
        return nx.dag_longest_path_length(self.g)

    def descendants(self, tid: str) -> set[str]:
        return set(nx.descendants(self.g, tid))
