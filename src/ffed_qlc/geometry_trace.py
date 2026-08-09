"""Exact integer Apollonian traces for reproducible geometry lessons."""

from __future__ import annotations

from collections import deque
from typing import Any, Iterable

from .contracts import payload_sha256


MAX_TRACE_STEPS = 4096
DEFAULT_ROOT = (-1, 2, 2, 3)


def build_apollonian_trace(depth: int = 3, root: Iterable[int] = DEFAULT_ROOT) -> dict[str, Any]:
    if depth < 0 or depth > 8:
        raise ValueError("depth must be between 0 and 8")
    root_tuple = tuple(int(value) for value in root)
    if len(root_tuple) != 4 or not _is_descartes(root_tuple):
        raise ValueError("root must be a Descartes curvature quadruple")
    queue = deque([(root_tuple, 0)])
    seen = {root_tuple}
    steps: list[dict[str, Any]] = []
    collisions = 0
    cycles = 0
    while queue and len(steps) < MAX_TRACE_STEPS:
        current, current_depth = queue.popleft()
        if current_depth >= depth:
            continue
        for generator in range(4):
            reflected = _reflect(current, generator)
            canonical = tuple(sorted(reflected))
            repeated = reflected in seen
            equivalent = canonical in {tuple(sorted(item)) for item in seen}
            collisions += int(equivalent and not repeated)
            cycles += int(repeated)
            steps.append({
                "index": len(steps),
                "depth": current_depth + 1,
                "generator": generator,
                "before": list(current),
                "after": list(reflected),
                "descartes_valid": _is_descartes(reflected),
                "cycle": repeated,
                "symmetry_collision": equivalent and not repeated,
            })
            if not repeated:
                seen.add(reflected)
                queue.append((reflected, current_depth + 1))
    body = {
        "schema": "ffed.qlc.geometry_trace.v1",
        "trace_id": f"apollonian-{depth}-{len(steps)}",
        "algorithm": "integral_descartes_reflection_bfs_v1",
        "root": list(root_tuple),
        "steps": steps,
        "collisions": collisions,
        "cycles": cycles,
        "integer_arithmetic": True,
        "floating_point_used": False,
        "truncated": bool(queue),
        "claim_boundary": "educational_geometry_trace_not_key_material",
    }
    body["sha256"] = payload_sha256(body)
    return body


def _reflect(values: tuple[int, int, int, int], index: int) -> tuple[int, int, int, int]:
    output = list(values)
    output[index] = 2 * sum(value for position, value in enumerate(values) if position != index) - values[index]
    return tuple(output)


def _is_descartes(values: tuple[int, int, int, int]) -> bool:
    return 2 * sum(value * value for value in values) == sum(values) ** 2

