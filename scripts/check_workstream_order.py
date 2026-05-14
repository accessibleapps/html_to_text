"""Validate the html_to_text improvement workstream order."""

from __future__ import annotations

from collections import defaultdict, deque


TASKS = [
    "order-check",
    "property-tests",
    "corpus-regression",
    "package-quality",
    "parser-hardening",
    "full-verification",
]

DEPENDENCIES = {
    "property-tests": {"order-check"},
    "corpus-regression": {"property-tests"},
    "package-quality": {"property-tests"},
    "parser-hardening": {"property-tests", "corpus-regression"},
    "full-verification": {
        "property-tests",
        "corpus-regression",
        "package-quality",
        "parser-hardening",
    },
}


def validate_order(tasks: list[str], dependencies: dict[str, set[str]]) -> list[str]:
    """Return a topological ordering or raise ValueError."""
    known_tasks = set(tasks)
    unknown = {
        dependency
        for required in dependencies.values()
        for dependency in required
        if dependency not in known_tasks
    }
    unknown.update(task for task in dependencies if task not in known_tasks)
    if unknown:
        raise ValueError(f"unknown task(s): {sorted(unknown)}")

    dependents: dict[str, set[str]] = defaultdict(set)
    indegrees = {task: 0 for task in tasks}
    for task, required_tasks in dependencies.items():
        indegrees[task] = len(required_tasks)
        for required_task in required_tasks:
            dependents[required_task].add(task)

    ready = deque(task for task in tasks if indegrees[task] == 0)
    ordered: list[str] = []
    while ready:
        task = ready.popleft()
        ordered.append(task)
        for dependent in sorted(dependents[task]):
            indegrees[dependent] -= 1
            if indegrees[dependent] == 0:
                ready.append(dependent)

    if len(ordered) != len(tasks):
        blocked = [task for task, indegree in indegrees.items() if indegree > 0]
        raise ValueError(f"cycle detected involving: {blocked}")
    return ordered


def main() -> None:
    ordered = validate_order(TASKS, DEPENDENCIES)
    for index, task in enumerate(ordered, start=1):
        print(f"{index}. {task}")


if __name__ == "__main__":
    main()
