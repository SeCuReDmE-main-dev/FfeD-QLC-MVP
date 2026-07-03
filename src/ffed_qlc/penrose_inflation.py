"""Deterministic Penrose rhombus inflation engine."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import math
from typing import Any, Iterable, Mapping, NamedTuple

from .penrose_geometry import (
    GEOMETRY_TOLERANCE,
    PHI,
    PenroseGeometryError,
    PenrosePatch,
    PenroseTile,
    build_penrose_patch,
    build_penrose_rhombus,
    bounding_box,
    deterministic_sort_tiles,
    deterministic_tile_id,
    edge_signatures,
    expected_area_for_type,
    matching_profile_for_tile,
    tile_metadata,
    validate_penrose_patch,
)
from .source_functions import (
    REQUIRED_SOURCE_IDS,
    SourceFunctionProfile,
    require_source_function_ids,
)


SUBSTITUTION_MATRIX = ((2, 1), (1, 1))
DEFAULT_MAX_INFLATION_DEPTH = 8
DEFAULT_TARGET_TILE_COUNT = 144
INFLATION_ENGINE_ID = "inflation"


class PlannedTile(NamedTuple):
    tile_type: str
    lineage: str
    generation_index: int
    parent_lineage: str | None


@dataclass(frozen=True)
class InflationInput:
    """Input contract for deterministic Penrose substitution growth."""

    depth: int = 1
    target_tile_count: int = DEFAULT_TARGET_TILE_COUNT
    edge_length: float = 1.0
    seed: str = "ffed-qlc-penrose"
    initial_tile_type: str = "thick"
    source_function_ids: tuple[str, ...] = REQUIRED_SOURCE_IDS
    max_depth: int = DEFAULT_MAX_INFLATION_DEPTH


@dataclass(frozen=True)
class InflationOutput:
    """Output contract for an inflated Penrose patch."""

    engine: str
    generation_index: int
    input: InflationInput
    tiles: tuple[PenroseTile, ...]
    patch: PenrosePatch
    source_contributions: tuple[dict[str, Any], ...]
    diagnostics: Mapping[str, Any]


def build_initial_inflation_patch(config: InflationInput | None = None) -> PenrosePatch:
    """Build the minimal one-rhombus seed patch for depth 0."""

    active_config = config or InflationInput(depth=0, target_tile_count=1)
    _validate_inflation_input(active_config)
    orientation = _seed_orientation_degrees(active_config.seed)
    tile = build_penrose_rhombus(
        active_config.initial_tile_type,
        edge_length=active_config.edge_length,
        orientation_degrees=orientation,
        metadata={
            "engine": INFLATION_ENGINE_ID,
            "generation_index": 0,
            "lineage": "root",
            "parent_lineage": None,
            "source_function_ids": list(active_config.source_function_ids),
        },
    )
    return build_penrose_patch([tile], patch_id="inflation-depth-0")


def inflate_penrose_patch(config: InflationInput | None = None) -> InflationOutput:
    """Apply thin/thick substitution and return a validated patch."""

    active_config = config or InflationInput()
    _validate_inflation_input(active_config)
    source_profiles = require_source_function_ids(active_config.source_function_ids)

    planned_tiles, generation_index = _expand_planned_tiles(active_config)
    raw_tiles = _layout_planned_tiles(planned_tiles, active_config)
    normalized_tiles = normalize_inflation_coordinates(raw_tiles)
    fused_tiles = fuse_inflation_vertices(normalized_tiles)
    patch = build_penrose_patch(
        fused_tiles,
        patch_id=f"inflation-depth-{generation_index}",
    )
    diagnostics = _build_inflation_diagnostics(
        config=active_config,
        generation_index=generation_index,
        planned_tiles=planned_tiles,
        patch=patch,
    )
    return InflationOutput(
        engine=INFLATION_ENGINE_ID,
        generation_index=generation_index,
        input=active_config,
        tiles=patch.tiles,
        patch=patch,
        source_contributions=_source_contributions(source_profiles),
        diagnostics=diagnostics,
    )


def substitute_thick(parent: PlannedTile) -> tuple[PlannedTile, PlannedTile, PlannedTile]:
    """Substitute one thick rhombus into two thick and one thin child."""

    next_generation = parent.generation_index + 1
    return (
        PlannedTile("thick", f"{parent.lineage}.T0", next_generation, parent.lineage),
        PlannedTile("thick", f"{parent.lineage}.T1", next_generation, parent.lineage),
        PlannedTile("thin", f"{parent.lineage}.t0", next_generation, parent.lineage),
    )


def substitute_thin(parent: PlannedTile) -> tuple[PlannedTile, PlannedTile]:
    """Substitute one thin rhombus into one thick and one thin child."""

    next_generation = parent.generation_index + 1
    return (
        PlannedTile("thick", f"{parent.lineage}.T0", next_generation, parent.lineage),
        PlannedTile("thin", f"{parent.lineage}.t0", next_generation, parent.lineage),
    )


def normalize_inflation_coordinates(tiles: Iterable[PenroseTile]) -> tuple[PenroseTile, ...]:
    """Translate inflated geometry so the patch minimum corner is at the origin."""

    sorted_tiles = deterministic_sort_tiles(tiles)
    if not sorted_tiles:
        return tuple()
    boxes = [bounding_box(tile.vertices) for tile in sorted_tiles]
    min_x = min(box[0] for box in boxes)
    min_y = min(box[1] for box in boxes)
    return tuple(_translate_tile(tile, -min_x, -min_y) for tile in sorted_tiles)


def fuse_inflation_vertices(
    tiles: Iterable[PenroseTile],
    *,
    tolerance: float = GEOMETRY_TOLERANCE,
) -> tuple[PenroseTile, ...]:
    """Fuse near-identical vertices to shared coordinates for stable adjacency."""

    sorted_tiles = deterministic_sort_tiles(tiles)
    buckets: dict[tuple[int, int], list[tuple[float, float]]] = {}
    for tile in sorted_tiles:
        for x, y in tile.vertices:
            key = (round(x / tolerance), round(y / tolerance))
            buckets.setdefault(key, []).append((x, y))

    fused_points = {
        key: (
            sum(point[0] for point in points) / len(points),
            sum(point[1] for point in points) / len(points),
        )
        for key, points in buckets.items()
    }

    fused_tiles: list[PenroseTile] = []
    for tile in sorted_tiles:
        vertices = tuple(
            fused_points[(round(x / tolerance), round(y / tolerance))]
            for x, y in tile.vertices
        )
        fused_tiles.append(_replace_tile_geometry(tile, vertices))
    return deterministic_sort_tiles(fused_tiles)


def export_inflation_manifest(output: InflationOutput) -> dict[str, Any]:
    """Return deterministic redacted inflation metadata with no raw source URLs."""

    return {
        "schema": "ffed.qlc.penrose_inflation_manifest.v1",
        "engine": output.engine,
        "generation_index": output.generation_index,
        "substitution_matrix": [list(row) for row in SUBSTITUTION_MATRIX],
        "target_tile_count": output.input.target_tile_count,
        "actual_tile_count": len(output.tiles),
        "patch_metadata": output.patch.metadata,
        "diagnostics": dict(output.diagnostics),
        "source_contributions": list(output.source_contributions),
        "tiles": [tile_metadata(tile) for tile in output.tiles],
        "raw_source_urls_included": False,
        "raw_payload_included": False,
        "claim_boundary": "inflation_manifest_not_crypto_or_quantum_proof",
    }


def _validate_inflation_input(config: InflationInput) -> None:
    if config.depth < 0:
        raise PenroseGeometryError("depth must be non-negative")
    if config.max_depth < 0 or config.max_depth > DEFAULT_MAX_INFLATION_DEPTH:
        raise PenroseGeometryError(
            f"max_depth must be between 0 and {DEFAULT_MAX_INFLATION_DEPTH}"
        )
    if config.depth > config.max_depth:
        raise PenroseGeometryError("depth exceeds max_depth")
    if config.target_tile_count < 1:
        raise PenroseGeometryError("target_tile_count must be positive")
    if config.edge_length <= 0:
        raise PenroseGeometryError("edge_length must be positive")
    if config.initial_tile_type not in {"thin", "thick"}:
        raise PenroseGeometryError("initial_tile_type must be thin or thick")
    require_source_function_ids(config.source_function_ids)


def _expand_planned_tiles(config: InflationInput) -> tuple[tuple[PlannedTile, ...], int]:
    planned: tuple[PlannedTile, ...] = (
        PlannedTile(config.initial_tile_type, "root", 0, None),
    )
    generation_index = 0
    for _ in range(config.depth):
        next_tiles: list[PlannedTile] = []
        for parent in planned:
            if parent.tile_type == "thick":
                children = substitute_thick(parent)
            else:
                children = substitute_thin(parent)
            next_tiles.extend(children)
            if len(next_tiles) >= config.target_tile_count:
                break
        planned = tuple(next_tiles[: config.target_tile_count])
        generation_index += 1
        if len(planned) >= config.target_tile_count:
            break
    return planned[: config.target_tile_count], generation_index


def _layout_planned_tiles(
    planned_tiles: tuple[PlannedTile, ...],
    config: InflationInput,
) -> tuple[PenroseTile, ...]:
    if not planned_tiles:
        return tuple()

    first = planned_tiles[0]
    first_tile = build_penrose_rhombus(
        first.tile_type,
        edge_length=config.edge_length,
        orientation_degrees=_seed_orientation_degrees(config.seed),
        metadata=_tile_lineage_metadata(first, config),
    )
    tiles = [first_tile]
    open_edges = _open_edges(first_tile)

    for planned in planned_tiles[1:]:
        candidate, open_edges = _attach_planned_tile(
            planned=planned,
            config=config,
            existing_tiles=tiles,
            open_edges=open_edges,
        )
        tiles.append(candidate)

    return tuple(tiles)


def _attach_planned_tile(
    *,
    planned: PlannedTile,
    config: InflationInput,
    existing_tiles: list[PenroseTile],
    open_edges: list[tuple[tuple[float, float], tuple[float, float], str]],
) -> tuple[PenroseTile, list[tuple[tuple[float, float], tuple[float, float], str]]]:
    if not open_edges:
        return _detached_tile(planned, config, len(existing_tiles)), open_edges

    start, end, shared_signature = _select_frontier_edge(open_edges)
    orientation = math.degrees(math.atan2(start[1] - end[1], start[0] - end[0]))
    candidate = build_penrose_rhombus(
        planned.tile_type,
        origin=end,
        orientation_degrees=orientation,
        edge_length=config.edge_length,
        metadata=_tile_lineage_metadata(planned, config),
    )
    next_edges = [edge for edge in open_edges if edge[2] != shared_signature]
    for edge in _open_edges(candidate):
        edge_signature = edge[2]
        existing_index = next(
            (
                index
                for index, open_edge in enumerate(next_edges)
                if open_edge[2] == edge_signature
            ),
            None,
        )
        if existing_index is None:
            next_edges.append(edge)
        else:
            next_edges.pop(existing_index)
    return candidate, next_edges


def _select_frontier_edge(
    open_edges: list[tuple[tuple[float, float], tuple[float, float], str]]
) -> tuple[tuple[float, float], tuple[float, float], str]:
    return max(
        open_edges,
        key=lambda edge: (
            _edge_radius(edge),
            _edge_angle(edge),
            edge[2],
        ),
    )


def _edge_radius(edge: tuple[tuple[float, float], tuple[float, float], str]) -> float:
    start, end, _signature = edge
    midpoint = ((start[0] + end[0]) / 2.0, (start[1] + end[1]) / 2.0)
    return math.hypot(midpoint[0], midpoint[1])


def _edge_angle(edge: tuple[tuple[float, float], tuple[float, float], str]) -> float:
    start, end, _signature = edge
    midpoint = ((start[0] + end[0]) / 2.0, (start[1] + end[1]) / 2.0)
    return math.atan2(midpoint[1], midpoint[0])


def _detached_tile(planned: PlannedTile, config: InflationInput, index: int) -> PenroseTile:
    spacing = config.edge_length * (3.0 + PHI)
    row_width = max(1, int(math.sqrt(max(1, config.target_tile_count))))
    row = index // row_width
    column = index % row_width
    return build_penrose_rhombus(
        planned.tile_type,
        origin=(column * spacing, row * spacing),
        orientation_degrees=(_seed_orientation_degrees(config.seed) + 36.0 * (index % 10)) % 360.0,
        edge_length=config.edge_length,
        metadata={
            **_tile_lineage_metadata(planned, config),
            "layout_warning": "detached_frontier_fallback",
        },
    )


def _open_edges(tile: PenroseTile) -> list[tuple[tuple[float, float], tuple[float, float], str]]:
    signatures = edge_signatures(tile.vertices)
    return [
        (tile.vertices[index], tile.vertices[(index + 1) % 4], signatures[index])
        for index in range(4)
    ]


def _replace_tile_geometry(
    tile: PenroseTile,
    vertices: Iterable[tuple[float, float]],
) -> PenroseTile:
    vertex_tuple = tuple((float(x), float(y)) for x, y in vertices)
    return PenroseTile(
        tile_id=deterministic_tile_id(tile.tile_type, vertex_tuple, tile.edge_length),
        tile_type=tile.tile_type,
        vertices=vertex_tuple,  # type: ignore[arg-type]
        edge_length=tile.edge_length,
        orientation_degrees=tile.orientation_degrees,
        metadata=dict(tile.metadata),
    )


def _translate_tile(tile: PenroseTile, dx: float, dy: float) -> PenroseTile:
    vertices = tuple((x + dx, y + dy) for x, y in tile.vertices)
    return _replace_tile_geometry(tile, vertices)


def _tile_lineage_metadata(planned: PlannedTile, config: InflationInput) -> dict[str, Any]:
    return {
        "engine": INFLATION_ENGINE_ID,
        "generation_index": planned.generation_index,
        "lineage": planned.lineage,
        "parent_lineage": planned.parent_lineage,
        "source_function_ids": list(config.source_function_ids),
    }


def _build_inflation_diagnostics(
    *,
    config: InflationInput,
    generation_index: int,
    planned_tiles: tuple[PlannedTile, ...],
    patch: PenrosePatch,
) -> dict[str, Any]:
    counts = _tile_type_counts(patch.tiles)
    thin = counts["thin"]
    thick = counts["thick"]
    ratio = None if thin == 0 else thick / thin
    validation = validate_penrose_patch(patch.tiles)
    vertex_signatures = {
        vertex_signature
        for tile in patch.tiles
        for signature in edge_signatures(tile.vertices)
        for vertex_signature in signature.split("|")
    }
    return {
        "schema": "ffed.qlc.penrose_inflation_diagnostics.v1",
        "engine": INFLATION_ENGINE_ID,
        "seed_fingerprint": hashlib.sha256(config.seed.encode("utf-8")).hexdigest()[:16],
        "requested_depth": config.depth,
        "generation_index": generation_index,
        "target_tile_count": config.target_tile_count,
        "actual_tile_count": len(patch.tiles),
        "substitution_matrix": [list(row) for row in SUBSTITUTION_MATRIX],
        "thick_count": thick,
        "thin_count": thin,
        "thick_thin_ratio": ratio,
        "ratio_phi_delta": None if ratio is None else abs(ratio - PHI),
        "adjacency_count": len(patch.adjacency),
        "fused_vertex_count": len(vertex_signatures),
        "geometry_valid": validation.valid,
        "validation_reasons": list(validation.reasons),
        "lineage_count": len({planned.lineage for planned in planned_tiles}),
        "area_by_type": {
            "thin": expected_area_for_type("thin", config.edge_length),
            "thick": expected_area_for_type("thick", config.edge_length),
        },
        "edge_labels_preserved": all(
            matching_profile_for_tile(tile)["edge_labels"] == ["e0", "e1", "e2", "e3"]
            for tile in patch.tiles
        ),
        "claim_boundary": "inflation_diagnostics_not_complete_plane_tiling_or_crypto_proof",
    }


def _tile_type_counts(tiles: Iterable[PenroseTile]) -> dict[str, int]:
    counts = {"thin": 0, "thick": 0}
    for tile in tiles:
        counts[tile.tile_type] += 1
    return counts


def _source_contributions(
    profiles: Iterable[SourceFunctionProfile],
) -> tuple[dict[str, Any], ...]:
    return tuple(
        {
            "source_id": profile.source_id,
            "function_name": profile.function.name,
            "lane": profile.lane,
            "source_role": profile.source_role,
            "source_weight": profile.source_weight,
            "url_fingerprint": profile.source_fingerprint,
        }
        for profile in profiles
    )


def _seed_orientation_degrees(seed: str) -> float:
    digest = hashlib.sha256(seed.encode("utf-8")).digest()
    return float((digest[0] % 10) * 36)

