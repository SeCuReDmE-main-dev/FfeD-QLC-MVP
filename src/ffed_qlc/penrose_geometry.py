"""Penrose thin/thick rhombus geometry primitives."""

from __future__ import annotations

from dataclasses import dataclass, field
import hashlib
import json
import math
from typing import Any, Iterable, Mapping


PHI = (1.0 + math.sqrt(5.0)) / 2.0
DEFAULT_EDGE_LENGTH = 1.0
GEOMETRY_TOLERANCE = 1.0e-7
ANGLE_TOLERANCE_DEGREES = 1.0e-5
THIN_ANGLES_DEGREES = (36.0, 144.0, 36.0, 144.0)
THICK_ANGLES_DEGREES = (72.0, 108.0, 72.0, 108.0)
PENROSE_TILE_TYPES = ("thin", "thick")

Point2D = tuple[float, float]


class PenroseGeometryError(ValueError):
    """Raised when Penrose geometry is invalid."""


@dataclass(frozen=True)
class PenroseTile:
    """Ordered four-vertex Penrose rhombus."""

    tile_id: str
    tile_type: str
    vertices: tuple[Point2D, Point2D, Point2D, Point2D]
    edge_length: float = DEFAULT_EDGE_LENGTH
    orientation_degrees: float = 0.0
    metadata: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class GeometryValidation:
    """Validation receipt for one Penrose tile."""

    valid: bool
    reasons: tuple[str, ...]
    tile_id: str
    tile_type: str
    edge_lengths: tuple[float, float, float, float]
    angles_degrees: tuple[float, float, float, float]
    centroid: Point2D
    area: float
    bounding_box: tuple[float, float, float, float]
    edge_signatures: tuple[str, str, str, str]


@dataclass(frozen=True)
class TileAdjacency:
    """Shared-edge relation between two Penrose tiles."""

    tile_a: str
    tile_b: str
    edge_a: int
    edge_b: int
    edge_signature: str
    relation: str = "shared_edge"


@dataclass(frozen=True)
class PatchValidation:
    """Validation receipt for a Penrose patch."""

    valid: bool
    reasons: tuple[str, ...]
    tile_count: int
    adjacency: tuple[TileAdjacency, ...]
    duplicate_tile_ids: tuple[str, ...]
    overlap_pairs: tuple[tuple[str, str], ...]
    bounding_box: tuple[float, float, float, float] | None
    patch_fingerprint: str | None


@dataclass(frozen=True)
class PenrosePatch:
    """Deterministically sorted Penrose patch with secondary metadata."""

    tiles: tuple[PenroseTile, ...]
    adjacency: tuple[TileAdjacency, ...]
    metadata: Mapping[str, Any]


def build_penrose_rhombus(
    tile_type: str,
    *,
    origin: Point2D = (0.0, 0.0),
    orientation_degrees: float = 0.0,
    edge_length: float = DEFAULT_EDGE_LENGTH,
    tile_id: str | None = None,
    metadata: Mapping[str, Any] | None = None,
) -> PenroseTile:
    """Build a valid ordered Penrose rhombus from type and orientation."""

    _require_tile_type(tile_type)
    if edge_length <= 0:
        raise PenroseGeometryError("edge_length must be positive")

    theta_degrees = _minimum_angle_for_type(tile_type)
    theta = math.radians(theta_degrees)
    orientation = math.radians(orientation_degrees)
    x0, y0 = _coerce_point(origin)
    edge_1 = (
        edge_length * math.cos(orientation),
        edge_length * math.sin(orientation),
    )
    edge_2 = (
        edge_length * math.cos(orientation + theta),
        edge_length * math.sin(orientation + theta),
    )
    vertices = (
        (x0, y0),
        (x0 + edge_1[0], y0 + edge_1[1]),
        (x0 + edge_1[0] + edge_2[0], y0 + edge_1[1] + edge_2[1]),
        (x0 + edge_2[0], y0 + edge_2[1]),
    )
    final_tile_id = tile_id or deterministic_tile_id(tile_type, vertices, edge_length)
    tile = PenroseTile(
        tile_id=final_tile_id,
        tile_type=tile_type,
        vertices=vertices,
        edge_length=edge_length,
        orientation_degrees=orientation_degrees,
        metadata=dict(metadata or {}),
    )
    validation = validate_penrose_tile(tile)
    if not validation.valid:
        raise PenroseGeometryError(
            f"invalid generated Penrose rhombus: {', '.join(validation.reasons)}"
        )
    return tile


def deterministic_tile_id(
    tile_type: str,
    vertices: Iterable[Point2D],
    edge_length: float = DEFAULT_EDGE_LENGTH,
) -> str:
    """Return a deterministic id from type and quantized geometry."""

    _require_tile_type(tile_type)
    normalized_vertices = [
        [round(point[0], 9), round(point[1], 9)] for point in map(_coerce_point, vertices)
    ]
    payload = {
        "edge_length": round(float(edge_length), 9),
        "tile_type": tile_type,
        "vertices": normalized_vertices,
    }
    digest = hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    return f"{tile_type[0]}-{digest[:16]}"


def edge_vectors(vertices: Iterable[Point2D]) -> tuple[Point2D, ...]:
    """Return ordered edge vectors for a four-point polygon."""

    points = _coerce_vertices(vertices)
    return tuple(_sub(points[(index + 1) % 4], points[index]) for index in range(4))


def edge_lengths(vertices: Iterable[Point2D]) -> tuple[float, float, float, float]:
    """Return ordered edge lengths."""

    return tuple(_length(vector) for vector in edge_vectors(vertices))  # type: ignore[return-value]


def edge_signatures(
    vertices: Iterable[Point2D],
    *,
    tolerance: float = GEOMETRY_TOLERANCE,
) -> tuple[str, str, str, str]:
    """Return orientation-independent signatures for ordered edges."""

    points = _coerce_vertices(vertices)
    signatures: list[str] = []
    for index, start in enumerate(points):
        end = points[(index + 1) % 4]
        start_key = _point_key(start, tolerance)
        end_key = _point_key(end, tolerance)
        left, right = sorted((start_key, end_key))
        signatures.append(f"{left[0]}:{left[1]}|{right[0]}:{right[1]}")
    return tuple(signatures)  # type: ignore[return-value]


def centroid(vertices: Iterable[Point2D]) -> Point2D:
    """Return the centroid of the ordered rhombus vertices."""

    points = _coerce_vertices(vertices)
    return (
        sum(point[0] for point in points) / 4.0,
        sum(point[1] for point in points) / 4.0,
    )


def polygon_area(vertices: Iterable[Point2D]) -> float:
    """Return absolute polygon area by shoelace formula."""

    return abs(signed_polygon_area(vertices))


def signed_polygon_area(vertices: Iterable[Point2D]) -> float:
    """Return signed polygon area; positive means counter-clockwise order."""

    points = _coerce_vertices(vertices)
    total = 0.0
    for index, point in enumerate(points):
        next_point = points[(index + 1) % 4]
        total += point[0] * next_point[1] - next_point[0] * point[1]
    return total / 2.0


def interior_angles_degrees(vertices: Iterable[Point2D]) -> tuple[float, float, float, float]:
    """Return ordered interior angles in degrees."""

    points = _coerce_vertices(vertices)
    angles: list[float] = []
    for index, point in enumerate(points):
        previous_point = points[(index - 1) % 4]
        next_point = points[(index + 1) % 4]
        a = _sub(previous_point, point)
        b = _sub(next_point, point)
        denominator = _length(a) * _length(b)
        if denominator <= 0:
            angles.append(float("nan"))
            continue
        cosine = max(-1.0, min(1.0, _dot(a, b) / denominator))
        angles.append(math.degrees(math.acos(cosine)))
    return tuple(angles)  # type: ignore[return-value]


def orientation_degrees(vertices: Iterable[Point2D]) -> float:
    """Return first-edge orientation in degrees in [0, 360)."""

    first_edge = edge_vectors(vertices)[0]
    return math.degrees(math.atan2(first_edge[1], first_edge[0])) % 360.0


def bounding_box(vertices: Iterable[Point2D]) -> tuple[float, float, float, float]:
    """Return min_x, min_y, max_x, max_y."""

    points = _coerce_vertices(vertices)
    xs = [point[0] for point in points]
    ys = [point[1] for point in points]
    return (min(xs), min(ys), max(xs), max(ys))


def validate_penrose_tile(
    tile: PenroseTile,
    *,
    tolerance: float = GEOMETRY_TOLERANCE,
    angle_tolerance_degrees: float = ANGLE_TOLERANCE_DEGREES,
) -> GeometryValidation:
    """Validate Penrose type, equal edges, angle profile, and polygon order."""

    reasons: list[str] = []
    if tile.tile_type not in PENROSE_TILE_TYPES:
        reasons.append("unsupported_tile_type")

    try:
        vertices = _coerce_vertices(tile.vertices)
    except PenroseGeometryError:
        vertices = ((0.0, 0.0), (0.0, 0.0), (0.0, 0.0), (0.0, 0.0))
        reasons.append("invalid_vertex_count")

    lengths = edge_lengths(vertices)
    angles = interior_angles_degrees(vertices)
    area = polygon_area(vertices)
    signed_area = signed_polygon_area(vertices)
    box = bounding_box(vertices)
    signatures = edge_signatures(vertices, tolerance=tolerance)

    if signed_area <= tolerance:
        reasons.append("polygon_order_not_counter_clockwise")
    if area <= tolerance:
        reasons.append("degenerate_area")
    if len(set(_point_key(point, tolerance) for point in vertices)) != 4:
        reasons.append("duplicate_vertices")
    if _has_self_crossing(vertices, tolerance=tolerance):
        reasons.append("self_crossing_polygon")

    if max(lengths) - min(lengths) > tolerance:
        reasons.append("unequal_edges")
    if any(length <= tolerance for length in lengths):
        reasons.append("zero_length_edge")

    if tile.tile_type in PENROSE_TILE_TYPES:
        expected_angles = angle_profile_for_type(tile.tile_type)
        for angle, expected in zip(angles, expected_angles):
            if not math.isfinite(angle) or abs(angle - expected) > angle_tolerance_degrees:
                reasons.append("invalid_angle_profile")
                break

    min_x, min_y, max_x, max_y = box
    if max_x - min_x <= tolerance or max_y - min_y <= tolerance:
        reasons.append("invalid_bounding_box")

    return GeometryValidation(
        valid=not reasons,
        reasons=tuple(dict.fromkeys(reasons)),
        tile_id=tile.tile_id,
        tile_type=tile.tile_type,
        edge_lengths=lengths,
        angles_degrees=angles,
        centroid=centroid(vertices),
        area=area,
        bounding_box=box,
        edge_signatures=signatures,
    )


def angle_profile_for_type(tile_type: str) -> tuple[float, float, float, float]:
    """Return the ordered Penrose angle profile for a tile type."""

    _require_tile_type(tile_type)
    return THIN_ANGLES_DEGREES if tile_type == "thin" else THICK_ANGLES_DEGREES


def expected_area_for_type(
    tile_type: str,
    edge_length: float = DEFAULT_EDGE_LENGTH,
) -> float:
    """Return the theoretical area for a thin or thick rhombus."""

    _require_tile_type(tile_type)
    if edge_length <= 0:
        raise PenroseGeometryError("edge_length must be positive")
    return edge_length * edge_length * math.sin(math.radians(_minimum_angle_for_type(tile_type)))


def matching_profile_for_tile(tile: PenroseTile) -> dict[str, Any]:
    """Return deterministic geometry metadata for future matching rules."""

    validation = validate_penrose_tile(tile)
    if not validation.valid:
        raise PenroseGeometryError(f"invalid tile: {', '.join(validation.reasons)}")
    return {
        "schema": "ffed.qlc.penrose_matching_profile.v1",
        "tile_id": tile.tile_id,
        "tile_type": tile.tile_type,
        "edge_labels": ["e0", "e1", "e2", "e3"],
        "edge_signatures": list(validation.edge_signatures),
        "angles_degrees": [round(angle, 9) for angle in validation.angles_degrees],
        "orientation_degrees": round(orientation_degrees(tile.vertices), 9),
        "claim_boundary": "geometry_matching_profile_not_crypto_certification",
    }


def tile_metadata(tile: PenroseTile) -> dict[str, Any]:
    """Return redacted public metadata for a Penrose tile."""

    validation = validate_penrose_tile(tile)
    if not validation.valid:
        raise PenroseGeometryError(f"invalid tile: {', '.join(validation.reasons)}")
    return {
        "schema": "ffed.qlc.penrose_tile_metadata.v1",
        "tile_id": tile.tile_id,
        "tile_type": tile.tile_type,
        "vertices": [[round(x, 9), round(y, 9)] for x, y in tile.vertices],
        "centroid": [round(value, 9) for value in validation.centroid],
        "area": round(validation.area, 12),
        "bounding_box": [round(value, 9) for value in validation.bounding_box],
        "edge_length": round(tile.edge_length, 9),
        "orientation_degrees": round(orientation_degrees(tile.vertices), 9),
        "matching_profile": matching_profile_for_tile(tile),
    }


def compute_adjacency(
    tiles: Iterable[PenroseTile],
    *,
    tolerance: float = GEOMETRY_TOLERANCE,
) -> tuple[TileAdjacency, ...]:
    """Return shared-edge adjacency between sorted tiles."""

    sorted_tiles = deterministic_sort_tiles(tiles)
    edge_index: dict[str, tuple[str, int]] = {}
    adjacency: list[TileAdjacency] = []
    for tile in sorted_tiles:
        signatures = edge_signatures(tile.vertices, tolerance=tolerance)
        for edge_number, signature in enumerate(signatures):
            previous = edge_index.get(signature)
            if previous is None:
                edge_index[signature] = (tile.tile_id, edge_number)
                continue
            tile_a, edge_a = previous
            tile_b = tile.tile_id
            adjacency.append(
                TileAdjacency(
                    tile_a=min(tile_a, tile_b),
                    tile_b=max(tile_a, tile_b),
                    edge_a=edge_a if tile_a <= tile_b else edge_number,
                    edge_b=edge_number if tile_a <= tile_b else edge_a,
                    edge_signature=signature,
                )
            )
    return tuple(sorted(adjacency, key=lambda item: (item.tile_a, item.tile_b, item.edge_signature)))


def validate_penrose_patch(
    tiles: Iterable[PenroseTile],
    *,
    tolerance: float = GEOMETRY_TOLERANCE,
) -> PatchValidation:
    """Validate duplicate, overlap, tile geometry, and adjacency guards."""

    sorted_tiles = deterministic_sort_tiles(tiles)
    reasons: list[str] = []
    duplicate_ids = _duplicate_tile_ids(sorted_tiles)
    if duplicate_ids:
        reasons.append("duplicate_tile_id")

    duplicate_geometry = _duplicate_geometry_ids(sorted_tiles, tolerance=tolerance)
    if duplicate_geometry:
        reasons.append("duplicate_tile_geometry")

    invalid_tiles = [
        validation.tile_id
        for validation in (validate_penrose_tile(tile, tolerance=tolerance) for tile in sorted_tiles)
        if not validation.valid
    ]
    if invalid_tiles:
        reasons.append("invalid_tile_geometry")

    overlap_pairs = _overlap_pairs(sorted_tiles, tolerance=tolerance)
    if overlap_pairs:
        reasons.append("overlapping_tiles")

    patch_box = _patch_bounding_box(sorted_tiles)
    fingerprint = _patch_fingerprint(sorted_tiles) if sorted_tiles else None
    return PatchValidation(
        valid=not reasons,
        reasons=tuple(dict.fromkeys(reasons)),
        tile_count=len(sorted_tiles),
        adjacency=compute_adjacency(sorted_tiles, tolerance=tolerance),
        duplicate_tile_ids=tuple(sorted(set(duplicate_ids + duplicate_geometry))),
        overlap_pairs=tuple(overlap_pairs),
        bounding_box=patch_box,
        patch_fingerprint=fingerprint,
    )


def build_penrose_patch(
    tiles: Iterable[PenroseTile],
    *,
    patch_id: str = "penrose-patch",
    tolerance: float = GEOMETRY_TOLERANCE,
) -> PenrosePatch:
    """Build a deterministic patch or fail closed on invalid geometry."""

    sorted_tiles = deterministic_sort_tiles(tiles)
    validation = validate_penrose_patch(sorted_tiles, tolerance=tolerance)
    if not validation.valid:
        raise PenroseGeometryError(f"invalid Penrose patch: {', '.join(validation.reasons)}")
    return PenrosePatch(
        tiles=sorted_tiles,
        adjacency=validation.adjacency,
        metadata=patch_metadata(sorted_tiles, patch_id=patch_id, validation=validation),
    )


def patch_metadata(
    tiles: Iterable[PenroseTile],
    *,
    patch_id: str = "penrose-patch",
    validation: PatchValidation | None = None,
) -> dict[str, Any]:
    """Return deterministic patch metadata."""

    sorted_tiles = deterministic_sort_tiles(tiles)
    active_validation = validation or validate_penrose_patch(sorted_tiles)
    counts = {
        "thin": sum(1 for tile in sorted_tiles if tile.tile_type == "thin"),
        "thick": sum(1 for tile in sorted_tiles if tile.tile_type == "thick"),
    }
    return {
        "schema": "ffed.qlc.penrose_patch_metadata.v1",
        "patch_id": patch_id,
        "tile_count": len(sorted_tiles),
        "tile_type_counts": counts,
        "adjacency_count": len(active_validation.adjacency),
        "bounding_box": None
        if active_validation.bounding_box is None
        else [round(value, 9) for value in active_validation.bounding_box],
        "patch_fingerprint": active_validation.patch_fingerprint,
        "phi": PHI,
        "geometry_tolerance": GEOMETRY_TOLERANCE,
        "valid": active_validation.valid,
        "claim_boundary": "penrose_geometry_metadata_not_security_or_quantum_proof",
    }


def deterministic_sort_tiles(tiles: Iterable[PenroseTile]) -> tuple[PenroseTile, ...]:
    """Sort tiles by id, type, and geometry fingerprint."""

    return tuple(
        sorted(
            tiles,
            key=lambda tile: (
                tile.tile_id,
                tile.tile_type,
                deterministic_tile_id(tile.tile_type, tile.vertices, tile.edge_length),
            ),
        )
    )


def _require_tile_type(tile_type: str) -> None:
    if tile_type not in PENROSE_TILE_TYPES:
        raise PenroseGeometryError(f"tile_type must be one of {PENROSE_TILE_TYPES}")


def _minimum_angle_for_type(tile_type: str) -> float:
    _require_tile_type(tile_type)
    return 36.0 if tile_type == "thin" else 72.0


def _coerce_point(point: Point2D) -> Point2D:
    if not isinstance(point, tuple) or len(point) != 2:
        raise PenroseGeometryError("point must be a two-value tuple")
    return (float(point[0]), float(point[1]))


def _coerce_vertices(vertices: Iterable[Point2D]) -> tuple[Point2D, Point2D, Point2D, Point2D]:
    points = tuple(_coerce_point(point) for point in vertices)
    if len(points) != 4:
        raise PenroseGeometryError("Penrose rhombus requires exactly four vertices")
    return points  # type: ignore[return-value]


def _point_key(point: Point2D, tolerance: float) -> tuple[int, int]:
    return (round(point[0] / tolerance), round(point[1] / tolerance))


def _sub(a: Point2D, b: Point2D) -> Point2D:
    return (a[0] - b[0], a[1] - b[1])


def _dot(a: Point2D, b: Point2D) -> float:
    return a[0] * b[0] + a[1] * b[1]


def _cross(a: Point2D, b: Point2D) -> float:
    return a[0] * b[1] - a[1] * b[0]


def _length(vector: Point2D) -> float:
    return math.hypot(vector[0], vector[1])


def _has_self_crossing(
    vertices: tuple[Point2D, Point2D, Point2D, Point2D],
    *,
    tolerance: float,
) -> bool:
    edges = [
        (vertices[0], vertices[1]),
        (vertices[1], vertices[2]),
        (vertices[2], vertices[3]),
        (vertices[3], vertices[0]),
    ]
    return _segments_intersect_strict(*edges[0], *edges[2], tolerance=tolerance) or _segments_intersect_strict(
        *edges[1], *edges[3], tolerance=tolerance
    )


def _segments_intersect_strict(
    a: Point2D,
    b: Point2D,
    c: Point2D,
    d: Point2D,
    *,
    tolerance: float,
) -> bool:
    ab = _sub(b, a)
    ac = _sub(c, a)
    ad = _sub(d, a)
    cd = _sub(d, c)
    ca = _sub(a, c)
    cb = _sub(b, c)
    cross_1 = _cross(ab, ac)
    cross_2 = _cross(ab, ad)
    cross_3 = _cross(cd, ca)
    cross_4 = _cross(cd, cb)
    return (
        cross_1 * cross_2 < -tolerance
        and cross_3 * cross_4 < -tolerance
    )


def _duplicate_tile_ids(tiles: tuple[PenroseTile, ...]) -> list[str]:
    seen: set[str] = set()
    duplicates: list[str] = []
    for tile in tiles:
        if tile.tile_id in seen:
            duplicates.append(tile.tile_id)
        seen.add(tile.tile_id)
    return duplicates


def _duplicate_geometry_ids(
    tiles: tuple[PenroseTile, ...],
    *,
    tolerance: float,
) -> list[str]:
    seen: dict[tuple[str, tuple[str, ...]], str] = {}
    duplicates: list[str] = []
    for tile in tiles:
        signature = (tile.tile_type, tuple(sorted(edge_signatures(tile.vertices, tolerance=tolerance))))
        previous_id = seen.get(signature)
        if previous_id is not None:
            duplicates.extend([previous_id, tile.tile_id])
        seen[signature] = tile.tile_id
    return duplicates


def _overlap_pairs(
    tiles: tuple[PenroseTile, ...],
    *,
    tolerance: float,
) -> list[tuple[str, str]]:
    overlaps: list[tuple[str, str]] = []
    for left_index, left in enumerate(tiles):
        for right in tiles[left_index + 1 :]:
            if _tiles_overlap(left, right, tolerance=tolerance):
                overlaps.append((left.tile_id, right.tile_id))
    return overlaps


def _tiles_overlap(
    left: PenroseTile,
    right: PenroseTile,
    *,
    tolerance: float,
) -> bool:
    left_signatures = set(edge_signatures(left.vertices, tolerance=tolerance))
    right_signatures = set(edge_signatures(right.vertices, tolerance=tolerance))
    shared_edges = left_signatures.intersection(right_signatures)
    if len(shared_edges) >= 2 and left.tile_type == right.tile_type:
        return True

    left_vertices = _coerce_vertices(left.vertices)
    right_vertices = _coerce_vertices(right.vertices)
    for point in left_vertices:
        if _point_inside_convex_polygon_strict(point, right_vertices, tolerance=tolerance):
            return True
    for point in right_vertices:
        if _point_inside_convex_polygon_strict(point, left_vertices, tolerance=tolerance):
            return True
    return _non_boundary_edge_intersection(left_vertices, right_vertices, tolerance=tolerance)


def _point_inside_convex_polygon_strict(
    point: Point2D,
    polygon: tuple[Point2D, Point2D, Point2D, Point2D],
    *,
    tolerance: float,
) -> bool:
    signs: list[float] = []
    for index, start in enumerate(polygon):
        end = polygon[(index + 1) % 4]
        signs.append(_cross(_sub(end, start), _sub(point, start)))
    return all(sign > tolerance for sign in signs) or all(sign < -tolerance for sign in signs)


def _non_boundary_edge_intersection(
    left: tuple[Point2D, Point2D, Point2D, Point2D],
    right: tuple[Point2D, Point2D, Point2D, Point2D],
    *,
    tolerance: float,
) -> bool:
    for left_index, left_start in enumerate(left):
        left_end = left[(left_index + 1) % 4]
        for right_index, right_start in enumerate(right):
            right_end = right[(right_index + 1) % 4]
            if _segments_intersect_strict(
                left_start,
                left_end,
                right_start,
                right_end,
                tolerance=tolerance,
            ):
                return True
    return False


def _patch_bounding_box(tiles: tuple[PenroseTile, ...]) -> tuple[float, float, float, float] | None:
    if not tiles:
        return None
    boxes = [bounding_box(tile.vertices) for tile in tiles]
    return (
        min(box[0] for box in boxes),
        min(box[1] for box in boxes),
        max(box[2] for box in boxes),
        max(box[3] for box in boxes),
    )


def _patch_fingerprint(tiles: tuple[PenroseTile, ...]) -> str:
    payload = [
        {
            "tile_id": tile.tile_id,
            "tile_type": tile.tile_type,
            "vertices": [[round(x, 9), round(y, 9)] for x, y in tile.vertices],
        }
        for tile in tiles
    ]
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
