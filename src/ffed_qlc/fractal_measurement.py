"""Fractal path and D_f / dF measurement for Penrose patches."""

from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Any, Iterable, Mapping, Sequence

from .admissibility import AdmDecision
from .penrose_geometry import PenrosePatch, PenroseTile, centroid, validate_penrose_tile


FRACTAL_HIERARCHY = "I -> I_system^S -> D_f -> dF -> i_fractal"
FRACTAL_CARRIERS = (
    "fractal_boundary",
    "fractal_growth",
    "fractal_projection",
    "fractal_cluster",
)
BOX_COUNTING_METHOD = "box_counting"
DEFAULT_SCALE_RANGE = (0.125, 0.25, 0.5, 1.0)
DEFAULT_D_MIN = 1.0
DEFAULT_D_MAX = 2.0

Point2D = tuple[float, float]
Omega = tuple[float, float, float, float]


@dataclass(frozen=True)
class FractalPath:
    """Local carrier used to estimate fractal dimension around a tile."""

    seed_tile_id: str
    carrier_type: str
    points: tuple[Point2D, ...]
    Omega: Omega | None
    scale_range: tuple[float, ...]
    measurement_method: str | None
    source: str = "geometry"


@dataclass(frozen=True)
class BoxCount:
    """Occupied box count for one scale."""

    scale: float
    occupied_boxes: int


@dataclass(frozen=True)
class FractalMeasurement:
    """D_f / D_f_hat / dF measurement receipt."""

    status: AdmDecision
    D_f: float | None
    D_f_hat: float | None
    dF: float | None
    i_fractal: float | None
    D_min: float
    D_max: float
    I_system_source: str | None
    hierarchy: str
    confidence: float
    box_counts: tuple[BoxCount, ...]
    reason_codes: tuple[str, ...]
    method_metadata: Mapping[str, Any]
    scale_metadata: Mapping[str, Any]


def build_fractal_path(
    tile: PenroseTile,
    patch: PenrosePatch,
    *,
    carrier_type: str = "fractal_boundary",
    scale_range: Sequence[float] = DEFAULT_SCALE_RANGE,
    measurement_method: str | None = BOX_COUNTING_METHOD,
) -> FractalPath:
    """Build a geometric carrier path around a Penrose tile."""

    if carrier_type not in FRACTAL_CARRIERS:
        raise ValueError(f"unsupported fractal carrier: {carrier_type}")
    points = _carrier_points(tile, patch, carrier_type)
    return FractalPath(
        seed_tile_id=tile.tile_id,
        carrier_type=carrier_type,
        points=points,
        Omega=_omega(points),
        scale_range=tuple(float(scale) for scale in scale_range),
        measurement_method=measurement_method,
    )


def measure_tile_fractal_path(
    tile: PenroseTile,
    patch: PenrosePatch,
    *,
    carrier_type: str = "fractal_boundary",
    scale_range: Sequence[float] = DEFAULT_SCALE_RANGE,
    measurement_method: str | None = BOX_COUNTING_METHOD,
    D_min: float = DEFAULT_D_MIN,
    D_max: float = DEFAULT_D_MAX,
) -> FractalMeasurement:
    """Measure local D_f(tile) from a fractal carrier."""

    path = build_fractal_path(
        tile,
        patch,
        carrier_type=carrier_type,
        scale_range=scale_range,
        measurement_method=measurement_method,
    )
    return measure_fractal_path(path, D_min=D_min, D_max=D_max)


def measure_patch_fractal_dimension(
    patch: PenrosePatch,
    *,
    carrier_type: str = "fractal_cluster",
    scale_range: Sequence[float] = DEFAULT_SCALE_RANGE,
    measurement_method: str | None = BOX_COUNTING_METHOD,
    D_min: float = DEFAULT_D_MIN,
    D_max: float = DEFAULT_D_MAX,
) -> FractalMeasurement:
    """Measure global D_f(patch) from accepted tile centroids."""

    points = tuple(centroid(tile.vertices) for tile in patch.tiles)
    path = FractalPath(
        seed_tile_id="patch",
        carrier_type=carrier_type,
        points=points,
        Omega=_omega(points),
        scale_range=tuple(float(scale) for scale in scale_range),
        measurement_method=measurement_method,
    )
    return measure_fractal_path(path, D_min=D_min, D_max=D_max)


def measure_fractal_path(
    path: FractalPath,
    *,
    D_min: float = DEFAULT_D_MIN,
    D_max: float = DEFAULT_D_MAX,
) -> FractalMeasurement:
    """Measure D_f and dF while preserving the hierarchy contract."""

    reason_codes = _path_precheck_reasons(path, D_min, D_max)
    if reason_codes:
        return _suspended_measurement(path, D_min, D_max, reason_codes)

    box_counts = box_count(path.points, path.Omega, path.scale_range)
    D_f = estimate_box_counting_dimension(box_counts)
    if D_f is None:
        return _suspended_measurement(
            path,
            D_min,
            D_max,
            ("unstable_measurement",),
            box_counts=box_counts,
        )

    D_f_hat = normalize_d_f(D_f, D_min=D_min, D_max=D_max)
    i_source = resolve_i_system_source(path)
    if i_source is None:
        return _suspended_measurement(
            path,
            D_min,
            D_max,
            ("i_system_source_not_fractal",),
            box_counts=box_counts,
            D_f=D_f,
            D_f_hat=D_f_hat,
        )

    confidence = _confidence_from_box_counts(box_counts)
    return FractalMeasurement(
        status=AdmDecision.ACCEPT,
        D_f=D_f,
        D_f_hat=D_f_hat,
        dF=D_f_hat,
        i_fractal=D_f_hat,
        D_min=D_min,
        D_max=D_max,
        I_system_source=i_source,
        hierarchy=FRACTAL_HIERARCHY,
        confidence=confidence,
        box_counts=box_counts,
        reason_codes=("dF_assigned_from_fractal_source",),
        method_metadata={
            "method": path.measurement_method,
            "carrier_type": path.carrier_type,
            "measurement_is_truth_claim": False,
        },
        scale_metadata=_scale_metadata(path.scale_range),
    )


def box_count(
    points: Sequence[Point2D],
    omega: Omega | None,
    scales: Sequence[float],
) -> tuple[BoxCount, ...]:
    """Count occupied boxes for each scale."""

    if omega is None:
        return tuple()
    min_x, min_y, _max_x, _max_y = omega
    counts: list[BoxCount] = []
    for scale in scales:
        if scale <= 0:
            continue
        occupied = {
            (
                math.floor((point[0] - min_x) / scale),
                math.floor((point[1] - min_y) / scale),
            )
            for point in points
        }
        counts.append(BoxCount(scale=float(scale), occupied_boxes=len(occupied)))
    return tuple(counts)


def estimate_box_counting_dimension(box_counts: Sequence[BoxCount]) -> float | None:
    """Estimate D_f as slope of log(N(scale)) over log(1/scale)."""

    usable = [
        (math.log(1.0 / count.scale), math.log(count.occupied_boxes))
        for count in box_counts
        if count.scale > 0 and count.occupied_boxes > 0
    ]
    if len(usable) < 2:
        return None
    xs, ys = zip(*usable)
    mean_x = sum(xs) / len(xs)
    mean_y = sum(ys) / len(ys)
    denominator = sum((x - mean_x) ** 2 for x in xs)
    if denominator <= 1e-12:
        return None
    slope = sum((x - mean_x) * (y - mean_y) for x, y in usable) / denominator
    if not math.isfinite(slope):
        return None
    return max(0.0, slope)


def normalize_d_f(
    D_f: float,
    *,
    D_min: float = DEFAULT_D_MIN,
    D_max: float = DEFAULT_D_MAX,
) -> float:
    """Normalize D_f into D_f_hat in [0, 1]."""

    if D_max <= D_min:
        raise ValueError("D_max must be greater than D_min")
    return _clamp01((D_f - D_min) / (D_max - D_min))


def resolve_i_system_source(path: FractalPath) -> str | None:
    """Allow dF assignment only from geometric fractal carriers."""

    if path.source != "geometry":
        return None
    if path.carrier_type not in FRACTAL_CARRIERS:
        return None
    if path.measurement_method != BOX_COUNTING_METHOD:
        return None
    return "I_system^S.fractal_geometry"


def export_fractal_measurement(measurement: FractalMeasurement) -> dict[str, Any]:
    """Export measurement metadata without claiming truth or certification."""

    return {
        "schema": "ffed.qlc.fractal_measurement.v1",
        "status": measurement.status.value,
        "D_f": measurement.D_f,
        "D_f_hat": measurement.D_f_hat,
        "dF": measurement.dF,
        "i_fractal": measurement.i_fractal,
        "D_min": measurement.D_min,
        "D_max": measurement.D_max,
        "I_system_source": measurement.I_system_source,
        "hierarchy": measurement.hierarchy,
        "confidence": measurement.confidence,
        "box_counts": [
            {"scale": count.scale, "occupied_boxes": count.occupied_boxes}
            for count in measurement.box_counts
        ],
        "reason_codes": list(measurement.reason_codes),
        "method_metadata": dict(measurement.method_metadata),
        "scale_metadata": dict(measurement.scale_metadata),
        "claim_boundary": "fractal_measurement_not_truth_or_security_certification",
    }


def _path_precheck_reasons(path: FractalPath, D_min: float, D_max: float) -> tuple[str, ...]:
    reasons: list[str] = []
    if path.Omega is None:
        reasons.append("missing_Omega")
    if not path.scale_range:
        reasons.append("missing_scale_range")
    if path.measurement_method is None:
        reasons.append("missing_measurement_method")
    elif path.measurement_method != BOX_COUNTING_METHOD:
        reasons.append("unsupported_measurement_method")
    if D_max <= D_min:
        reasons.append("invalid_D_bounds")
    if path.source != "geometry" or path.carrier_type not in FRACTAL_CARRIERS:
        reasons.append("contradiction_non_geometric")
    return tuple(dict.fromkeys(reasons))


def _suspended_measurement(
    path: FractalPath,
    D_min: float,
    D_max: float,
    reason_codes: tuple[str, ...],
    *,
    box_counts: tuple[BoxCount, ...] = tuple(),
    D_f: float | None = None,
    D_f_hat: float | None = None,
) -> FractalMeasurement:
    return FractalMeasurement(
        status=AdmDecision.SUSPEND,
        D_f=D_f,
        D_f_hat=D_f_hat,
        dF=None,
        i_fractal=None,
        D_min=D_min,
        D_max=D_max,
        I_system_source=resolve_i_system_source(path),
        hierarchy=FRACTAL_HIERARCHY,
        confidence=0.0,
        box_counts=box_counts,
        reason_codes=reason_codes,
        method_metadata={
            "method": path.measurement_method,
            "carrier_type": path.carrier_type,
            "measurement_is_truth_claim": False,
        },
        scale_metadata=_scale_metadata(path.scale_range),
    )


def _carrier_points(
    tile: PenroseTile,
    patch: PenrosePatch,
    carrier_type: str,
) -> tuple[Point2D, ...]:
    tile_validation = validate_penrose_tile(tile)
    if not tile_validation.valid:
        return tuple()
    if carrier_type == "fractal_boundary":
        points: list[Point2D] = []
        for index, point in enumerate(tile.vertices):
            next_point = tile.vertices[(index + 1) % 4]
            points.append(point)
            points.append(((point[0] + next_point[0]) / 2.0, (point[1] + next_point[1]) / 2.0))
        return tuple(points)
    if carrier_type == "fractal_growth":
        return tuple(centroid(candidate.vertices) for candidate in patch.tiles)
    if carrier_type == "fractal_projection":
        center = centroid(tile.vertices)
        return tuple(tile.vertices) + (center,)
    if carrier_type == "fractal_cluster":
        adjacent_ids = {
            edge.tile_a if edge.tile_b == tile.tile_id else edge.tile_b
            for edge in patch.adjacency
            if tile.tile_id in {edge.tile_a, edge.tile_b}
        }
        cluster = [tile]
        cluster.extend(candidate for candidate in patch.tiles if candidate.tile_id in adjacent_ids)
        return tuple(centroid(candidate.vertices) for candidate in cluster)
    return tuple()


def _omega(points: Sequence[Point2D]) -> Omega | None:
    if not points:
        return None
    xs = [point[0] for point in points]
    ys = [point[1] for point in points]
    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)
    if max_x == min_x or max_y == min_y:
        return None
    return (min_x, min_y, max_x, max_y)


def _scale_metadata(scale_range: Sequence[float]) -> dict[str, Any]:
    return {
        "scale_count": len(scale_range),
        "scale_min": min(scale_range) if scale_range else None,
        "scale_max": max(scale_range) if scale_range else None,
    }


def _confidence_from_box_counts(box_counts: Sequence[BoxCount]) -> float:
    if len(box_counts) < 2:
        return 0.0
    occupied = [count.occupied_boxes for count in box_counts]
    if len(set(occupied)) < 2:
        return 0.35
    return _clamp01((len(box_counts) / len(DEFAULT_SCALE_RANGE)) * 0.75 + 0.25)


def _clamp01(value: Any) -> float:
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        numeric = 0.0
    return min(1.0, max(0.0, numeric))
