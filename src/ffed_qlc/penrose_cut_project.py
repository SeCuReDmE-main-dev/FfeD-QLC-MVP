"""Bounded cut-and-project candidate engine for Penrose rhombi."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import itertools
import json
import math
from typing import Any, Iterable, Mapping

from .penrose_geometry import (
    PHI,
    PenroseGeometryError,
    PenrosePatch,
    PenroseTile,
    build_penrose_patch,
    build_penrose_rhombus,
    deterministic_sort_tiles,
    edge_signatures,
    validate_penrose_patch,
)
from .penrose_inflation import InflationInput, InflationOutput, inflate_penrose_patch
from .source_functions import REQUIRED_SOURCE_IDS, require_source_function_ids


CUT_PROJECT_ENGINE_ID = "cut_project"
PHI_BASIS_PROFILE = "pentagrid_phi_v1"
DEFAULT_ACCEPTANCE_WINDOW_RADIUS = 1.75
DEFAULT_CANDIDATE_CAP = 5000
DEFAULT_GRID_RADIUS = 3

Point5D = tuple[int, int, int, int, int]
Point2D = tuple[float, float]


class CutProjectError(ValueError):
    """Raised when cut-and-project input cannot be evaluated."""


@dataclass(frozen=True)
class PhiBasisVector:
    """One 5D basis vector projected into physical and internal planes."""

    index: int
    physical: Point2D
    internal: Point2D


@dataclass(frozen=True)
class CutProjectCandidate:
    """One bounded 5D grid point and its projection metadata."""

    lattice_point: Point5D
    projected_2d: Point2D
    internal_projection: Point2D
    window_distance: float
    accepted: bool
    tile_type: str
    orientation_degrees: float
    candidate_fingerprint: str


@dataclass(frozen=True)
class CutProjectInput:
    """Input contract for bounded cut-and-project generation."""

    target_tile_count: int = 55
    grid_radius: int = DEFAULT_GRID_RADIUS
    candidate_cap: int = DEFAULT_CANDIDATE_CAP
    edge_length: float = 1.0
    seed: str = "ffed-qlc-cut-project"
    basis_profile: str = PHI_BASIS_PROFILE
    acceptance_window_radius: float | None = DEFAULT_ACCEPTANCE_WINDOW_RADIUS
    seed_shift: Point5D | None = None
    source_function_ids: tuple[str, ...] = REQUIRED_SOURCE_IDS
    allow_inflation_fallback: bool = True


@dataclass(frozen=True)
class CutProjectOutput:
    """Output contract for cut-and-project patch generation."""

    engine: str
    status: str
    input: CutProjectInput
    patch: PenrosePatch
    candidates: tuple[CutProjectCandidate, ...]
    accepted_candidates: tuple[CutProjectCandidate, ...]
    diagnostics: Mapping[str, Any]
    fallback: InflationOutput | None = None


def build_phi_basis(profile: str = PHI_BASIS_PROFILE) -> tuple[PhiBasisVector, ...]:
    """Build the 5-vector physical/internal projection basis."""

    if profile != PHI_BASIS_PROFILE:
        raise CutProjectError(f"unsupported phi basis profile: {profile}")
    basis: list[PhiBasisVector] = []
    for index in range(5):
        angle = 2.0 * math.pi * index / 5.0
        internal_angle = 2.0 * angle
        basis.append(
            PhiBasisVector(
                index=index,
                physical=(math.cos(angle), math.sin(angle)),
                internal=(math.cos(internal_angle), math.sin(internal_angle)),
            )
        )
    return tuple(basis)


def cut_project_penrose_patch(config: CutProjectInput | None = None) -> CutProjectOutput:
    """Generate a validated Penrose patch from bounded 5D candidates."""

    active_config = config or CutProjectInput()
    precheck_reasons = _precheck_cut_project_input(active_config)
    if precheck_reasons:
        return _suspended_with_fallback(active_config, precheck_reasons)

    source_profiles = require_source_function_ids(active_config.source_function_ids)
    basis = build_phi_basis(active_config.basis_profile)
    seed_shift = active_config.seed_shift or derive_seed_shift(active_config.seed)
    candidates = generate_cut_project_candidates(active_config, basis, seed_shift)
    accepted = tuple(candidate for candidate in candidates if candidate.accepted)
    if len(accepted) < active_config.target_tile_count:
        return _suspended_with_fallback(
            active_config,
            ("insufficient_accepted_candidates",),
            candidates=candidates,
            accepted_candidates=accepted,
        )

    selected = accepted[: active_config.target_tile_count]
    tiles = _layout_projected_candidates(selected, active_config)
    patch = build_penrose_patch(tiles, patch_id="cut-project-patch")
    inflation_reference = _inflation_reference(active_config)
    diagnostics = _build_cut_project_diagnostics(
        config=active_config,
        basis=basis,
        seed_shift=seed_shift,
        candidates=candidates,
        accepted_candidates=selected,
        patch=patch,
        status="accept",
        suspend_reasons=(),
        inflation_reference=inflation_reference,
        source_count=len(source_profiles),
    )
    return CutProjectOutput(
        engine=CUT_PROJECT_ENGINE_ID,
        status="accept",
        input=active_config,
        patch=patch,
        candidates=candidates,
        accepted_candidates=selected,
        diagnostics=diagnostics,
        fallback=None,
    )


def derive_seed_shift(seed: str) -> Point5D:
    """Derive a small deterministic 5D shift from the seed."""

    digest = hashlib.sha256(seed.encode("utf-8")).digest()
    return tuple((digest[index] % 3) - 1 for index in range(5))  # type: ignore[return-value]


def project_5d_to_2d(point: Point5D, basis: Iterable[PhiBasisVector]) -> Point2D:
    """Project one 5D integer point into the physical plane."""

    vectors = tuple(basis)
    if len(vectors) != 5:
        raise CutProjectError("phi basis requires five vectors")
    return (
        sum(point[index] * vectors[index].physical[0] for index in range(5)),
        sum(point[index] * vectors[index].physical[1] for index in range(5)),
    )


def project_5d_to_internal(point: Point5D, basis: Iterable[PhiBasisVector]) -> Point2D:
    """Project one 5D integer point into the internal acceptance plane."""

    vectors = tuple(basis)
    if len(vectors) != 5:
        raise CutProjectError("phi basis requires five vectors")
    return (
        sum(point[index] * vectors[index].internal[0] for index in range(5)),
        sum(point[index] * vectors[index].internal[1] for index in range(5)),
    )


def generate_cut_project_candidates(
    config: CutProjectInput,
    basis: Iterable[PhiBasisVector] | None = None,
    seed_shift: Point5D | None = None,
) -> tuple[CutProjectCandidate, ...]:
    """Generate bounded 5D candidates and filter by acceptance window."""

    _raise_for_invalid_bounds(config)
    active_basis = tuple(basis or build_phi_basis(config.basis_profile))
    active_shift = seed_shift or config.seed_shift or derive_seed_shift(config.seed)
    if config.acceptance_window_radius is None:
        raise CutProjectError("missing acceptance window")

    candidates: list[CutProjectCandidate] = []
    values = range(-config.grid_radius, config.grid_radius + 1)
    for raw_point in itertools.product(values, repeat=5):
        shifted = tuple(raw_point[index] + active_shift[index] for index in range(5))
        if shifted == (0, 0, 0, 0, 0):
            continue
        projected = project_5d_to_2d(shifted, active_basis)
        internal = project_5d_to_internal(shifted, active_basis)
        window_distance = math.hypot(internal[0], internal[1])
        accepted = window_distance <= config.acceptance_window_radius
        orientation_index = _orientation_index(shifted)
        tile_type = _tile_type_from_candidate(
            shifted,
            window_distance,
            config.acceptance_window_radius,
        )
        candidates.append(
            CutProjectCandidate(
                lattice_point=shifted,  # type: ignore[arg-type]
                projected_2d=projected,
                internal_projection=internal,
                window_distance=window_distance,
                accepted=accepted,
                tile_type=tile_type,
                orientation_degrees=float((orientation_index * 36) % 360),
                candidate_fingerprint=_candidate_fingerprint(shifted),
            )
        )

    candidates.sort(
        key=lambda candidate: (
            not candidate.accepted,
            candidate.window_distance,
            _radius(candidate.projected_2d),
            candidate.candidate_fingerprint,
        )
    )
    return tuple(candidates[: config.candidate_cap])


def _precheck_cut_project_input(config: CutProjectInput) -> tuple[str, ...]:
    reasons: list[str] = []
    try:
        _raise_for_invalid_bounds(config)
    except CutProjectError as exc:
        reasons.append(str(exc))
    if config.acceptance_window_radius is None:
        reasons.append("missing_acceptance_window")
    elif config.acceptance_window_radius <= 0:
        reasons.append("invalid_acceptance_window")
    if config.basis_profile != PHI_BASIS_PROFILE:
        reasons.append("invalid_phi_basis")
    try:
        require_source_function_ids(config.source_function_ids)
    except ValueError:
        reasons.append("missing_source_function_profile")
    return tuple(dict.fromkeys(reasons))


def _raise_for_invalid_bounds(config: CutProjectInput) -> None:
    if config.target_tile_count < 1:
        raise CutProjectError("target_tile_count must be positive")
    if config.grid_radius < 1 or config.grid_radius > 4:
        raise CutProjectError("grid_radius must be between 1 and 4")
    if config.candidate_cap < config.target_tile_count:
        raise CutProjectError("candidate_cap must be >= target_tile_count")
    if config.edge_length <= 0:
        raise CutProjectError("edge_length must be positive")
    if config.seed_shift is not None and len(config.seed_shift) != 5:
        raise CutProjectError("seed_shift must contain five integers")


def _suspended_with_fallback(
    config: CutProjectInput,
    reasons: tuple[str, ...],
    *,
    candidates: tuple[CutProjectCandidate, ...] = tuple(),
    accepted_candidates: tuple[CutProjectCandidate, ...] = tuple(),
) -> CutProjectOutput:
    if not config.allow_inflation_fallback:
        raise CutProjectError(f"cut-project suspended: {', '.join(reasons)}")

    fallback = _inflation_reference(config)
    diagnostics = {
        "schema": "ffed.qlc.cut_project_diagnostics.v1",
        "engine": CUT_PROJECT_ENGINE_ID,
        "status": "suspend",
        "suspend_reasons": list(reasons),
        "fallback_engine": fallback.engine,
        "target_tile_count": config.target_tile_count,
        "actual_tile_count": len(fallback.tiles),
        "raw_source_urls_included": False,
        "raw_payload_included": False,
        "claim_boundary": "cut_project_suspended_not_security_or_quantum_proof",
    }
    return CutProjectOutput(
        engine=CUT_PROJECT_ENGINE_ID,
        status="suspend",
        input=config,
        patch=fallback.patch,
        candidates=candidates,
        accepted_candidates=accepted_candidates,
        diagnostics=diagnostics,
        fallback=fallback,
    )


def _layout_projected_candidates(
    candidates: tuple[CutProjectCandidate, ...],
    config: CutProjectInput,
) -> tuple[PenroseTile, ...]:
    tiles: list[PenroseTile] = []
    open_edges: list[tuple[tuple[float, float], tuple[float, float], str]] = []

    for index, candidate in enumerate(candidates):
        metadata = _candidate_tile_metadata(candidate)
        if index == 0:
            tile = build_penrose_rhombus(
                candidate.tile_type,
                edge_length=config.edge_length,
                orientation_degrees=candidate.orientation_degrees,
                metadata=metadata,
            )
            tiles.append(tile)
            open_edges.extend(_open_edges(tile))
            continue

        start, end, shared_signature = _select_frontier_edge(open_edges)
        orientation = math.degrees(math.atan2(start[1] - end[1], start[0] - end[0]))
        tile = build_penrose_rhombus(
            candidate.tile_type,
            origin=end,
            orientation_degrees=orientation,
            edge_length=config.edge_length,
            metadata=metadata,
        )
        tiles.append(tile)
        open_edges = [edge for edge in open_edges if edge[2] != shared_signature]
        for edge in _open_edges(tile):
            match_index = next(
                (
                    edge_index
                    for edge_index, open_edge in enumerate(open_edges)
                    if open_edge[2] == edge[2]
                ),
                None,
            )
            if match_index is None:
                open_edges.append(edge)
            else:
                open_edges.pop(match_index)

    sorted_tiles = deterministic_sort_tiles(tiles)
    validation = validate_penrose_patch(sorted_tiles)
    if not validation.valid:
        raise PenroseGeometryError(
            f"cut-project candidate layout invalid: {', '.join(validation.reasons)}"
        )
    return sorted_tiles


def _candidate_tile_metadata(candidate: CutProjectCandidate) -> dict[str, Any]:
    return {
        "engine": CUT_PROJECT_ENGINE_ID,
        "candidate_fingerprint": candidate.candidate_fingerprint,
        "lattice_point_fingerprint": _candidate_fingerprint(candidate.lattice_point),
        "projected_2d": [round(value, 9) for value in candidate.projected_2d],
        "internal_projection": [round(value, 9) for value in candidate.internal_projection],
        "window_distance": round(candidate.window_distance, 12),
        "accepted": candidate.accepted,
    }


def _build_cut_project_diagnostics(
    *,
    config: CutProjectInput,
    basis: tuple[PhiBasisVector, ...],
    seed_shift: Point5D,
    candidates: tuple[CutProjectCandidate, ...],
    accepted_candidates: tuple[CutProjectCandidate, ...],
    patch: PenrosePatch,
    status: str,
    suspend_reasons: tuple[str, ...],
    inflation_reference: InflationOutput,
    source_count: int,
) -> dict[str, Any]:
    patch_counts = patch.metadata["tile_type_counts"]
    inflation_counts = inflation_reference.patch.metadata["tile_type_counts"]
    return {
        "schema": "ffed.qlc.cut_project_diagnostics.v1",
        "engine": CUT_PROJECT_ENGINE_ID,
        "status": status,
        "suspend_reasons": list(suspend_reasons),
        "basis_profile": config.basis_profile,
        "basis_vector_count": len(basis),
        "seed_shift": list(seed_shift),
        "grid_radius": config.grid_radius,
        "candidate_cap": config.candidate_cap,
        "candidate_count": len(candidates),
        "accepted_candidate_count": len(accepted_candidates),
        "acceptance_window_radius": config.acceptance_window_radius,
        "target_tile_count": config.target_tile_count,
        "actual_tile_count": patch.metadata["tile_count"],
        "patch_fingerprint": patch.metadata["patch_fingerprint"],
        "tile_type_counts": patch_counts,
        "inflation_reference": {
            "engine": inflation_reference.engine,
            "patch_fingerprint": inflation_reference.patch.metadata["patch_fingerprint"],
            "tile_type_counts": inflation_counts,
            "tile_count_delta": patch.metadata["tile_count"] - len(inflation_reference.tiles),
        },
        "source_profile_count": source_count,
        "raw_source_urls_included": False,
        "raw_payload_included": False,
        "claim_boundary": "bounded_cut_project_metadata_not_complete_plane_tiling_or_crypto_proof",
    }


def _inflation_reference(config: CutProjectInput) -> InflationOutput:
    return inflate_penrose_patch(
        InflationInput(
            depth=_depth_for_target(config.target_tile_count),
            target_tile_count=config.target_tile_count,
            edge_length=config.edge_length,
            seed=f"{config.seed}:fallback",
            source_function_ids=config.source_function_ids,
        )
    )


def _depth_for_target(target_tile_count: int) -> int:
    thick = 1
    thin = 0
    for depth in range(0, 9):
        if thick + thin >= target_tile_count:
            return depth
        thick, thin = (2 * thick + thin, thick + thin)
    return 8


def _tile_type_from_candidate(
    point: Point5D,
    window_distance: float,
    acceptance_window_radius: float,
) -> str:
    score = sum(abs(value) for value in point) + int(window_distance * 1000)
    if window_distance <= acceptance_window_radius / PHI:
        return "thick"
    return "thick" if score % 3 else "thin"


def _orientation_index(point: Point5D) -> int:
    return max(range(5), key=lambda index: (abs(point[index]), -index))


def _candidate_fingerprint(point: Point5D) -> str:
    return hashlib.sha256(
        json.dumps(list(point), separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def _radius(point: Point2D) -> float:
    return math.hypot(point[0], point[1])


def _open_edges(tile: PenroseTile) -> list[tuple[tuple[float, float], tuple[float, float], str]]:
    signatures = edge_signatures(tile.vertices)
    return [
        (tile.vertices[index], tile.vertices[(index + 1) % 4], signatures[index])
        for index in range(4)
    ]


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
