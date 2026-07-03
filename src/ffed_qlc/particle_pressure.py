"""Particle descriptors, semantic pressure, and bounded Z policy."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from typing import Any, Iterable, Mapping, Sequence

from .mesh_proof import YOLODetection
from .penrose_geometry import PHI, PenroseTile, validate_penrose_tile


PARTICLE_DESCRIPTOR_SCHEMA = "ffed.qlc.particle_descriptor.v1"
SEMANTIC_PRESSURE_SCHEMA = "ffed.qlc.semantic_pressure.v1"
Z_VALUE_SCHEMA = "ffed.qlc.z_value.v1"


@dataclass(frozen=True)
class ParticleDescriptor:
    """Redacted particle descriptor with no raw payload."""

    particle_id: str
    media_type: str
    state_wxyz: tuple[float, float, float, float]
    payload_fingerprint: str
    feature_fingerprints: Mapping[str, str]
    status: str = "accept"
    reason_codes: tuple[str, ...] = tuple()
    raw_payload_embedded: bool = False


@dataclass(frozen=True)
class SemanticPressure:
    """Bounded semantic pressure applied to lattice parameters."""

    value: float
    lattice_density_multiplier: float
    phason_strain_factor: float
    z_modifier: float
    sources: tuple[str, ...]
    claim_boundary: str = "semantic_pressure_metadata_not_crypto_root"


@dataclass(frozen=True)
class ZValueResult:
    """Bounded Z-value receipt."""

    raw_z: float
    normalized_z: float
    inputs_wxyz: tuple[float, float, float, float]
    z_modifier: float
    clamped: bool


def build_image_particle_descriptor(
    rgba_pixels: Sequence[Sequence[int]],
    *,
    particle_id: str = "image-particle",
) -> ParticleDescriptor:
    """Map RGBA pixel tuples into a redacted WXYZ state."""

    normalized_pixels = [_normalize_rgba(pixel) for pixel in rgba_pixels]
    if not normalized_pixels:
        normalized_pixels = [(0, 0, 0, 0)]

    count = float(len(normalized_pixels))
    channels = tuple(
        sum(pixel[channel] for pixel in normalized_pixels) / (255.0 * count)
        for channel in range(4)
    )
    histogram = _rgba_histogram(normalized_pixels)
    return ParticleDescriptor(
        particle_id=particle_id,
        media_type="image",
        state_wxyz=tuple(_clamp01(value) for value in channels),  # type: ignore[arg-type]
        payload_fingerprint=_fingerprint(normalized_pixels),
        feature_fingerprints={
            "rgba_histogram": _fingerprint(histogram),
            "pixel_count": _fingerprint(len(normalized_pixels)),
        },
    )


def build_text_particle_descriptor(
    text: str,
    *,
    particle_id: str = "text-particle",
) -> ParticleDescriptor:
    """Map text to redacted structural features without storing the text."""

    safe_text = text or ""
    length = max(1, len(safe_text))
    vowels = sum(1 for char in safe_text.casefold() if char in "aeiouy")
    digits = sum(1 for char in safe_text if char.isdigit())
    spaces = sum(1 for char in safe_text if char.isspace())
    symbols = sum(1 for char in safe_text if not char.isalnum() and not char.isspace())
    state = (
        _clamp01(vowels / length),
        _clamp01(digits / length),
        _clamp01(spaces / length),
        _clamp01(symbols / length),
    )
    return ParticleDescriptor(
        particle_id=particle_id,
        media_type="text",
        state_wxyz=state,
        payload_fingerprint=hashlib.sha256(safe_text.encode("utf-8")).hexdigest(),
        feature_fingerprints={
            "length_bucket": _fingerprint(_length_bucket(len(safe_text))),
            "character_profile": _fingerprint(state),
        },
    )


def build_audio_particle_descriptor(
    *,
    audio_fingerprint: str,
    duration_seconds: float | None = None,
    sample_rate_hz: int | None = None,
    particle_id: str = "audio-particle",
) -> ParticleDescriptor:
    """Create an audio mapping contract while raw audio extraction is suspended."""

    duration = _clamp01((duration_seconds or 0.0) / 3600.0)
    sample_rate = _clamp01((sample_rate_hz or 0) / 192000.0)
    contract_fingerprint = _fingerprint(
        {
            "audio_fingerprint": audio_fingerprint,
            "duration_seconds": duration_seconds,
            "sample_rate_hz": sample_rate_hz,
        }
    )
    return ParticleDescriptor(
        particle_id=particle_id,
        media_type="audio",
        state_wxyz=(duration, sample_rate, 0.0, 0.0),
        payload_fingerprint=hashlib.sha256(audio_fingerprint.encode("utf-8")).hexdigest(),
        feature_fingerprints={"audio_contract": contract_fingerprint},
        status="suspend",
        reason_codes=("audio_feature_extractor_not_enabled",),
    )


def export_particle_descriptor(descriptor: ParticleDescriptor) -> dict[str, Any]:
    """Export a particle descriptor without raw payload data."""

    return {
        "schema": PARTICLE_DESCRIPTOR_SCHEMA,
        "particle_id": descriptor.particle_id,
        "media_type": descriptor.media_type,
        "state_wxyz": [round(value, 12) for value in descriptor.state_wxyz],
        "payload_fingerprint": descriptor.payload_fingerprint,
        "feature_fingerprints": dict(descriptor.feature_fingerprints),
        "status": descriptor.status,
        "reason_codes": list(descriptor.reason_codes),
        "raw_payload_embedded": False,
        "claim_boundary": "particle_descriptor_fingerprint_only_not_raw_payload",
    }


def semantic_pressure_from_yolo_rois(
    detections: Sequence[Mapping[str, Any] | YOLODetection],
) -> SemanticPressure:
    """Convert YOLO ROI metadata into bounded semantic pressure."""

    normalized = [
        detection if isinstance(detection, YOLODetection) else YOLODetection.from_mapping(detection)
        for detection in detections
    ]
    if not normalized:
        return semantic_pressure_from_value(0.0, sources=("yolo_roi",))

    scores = []
    for detection in normalized:
        sensitivity = 1.0 if detection.label in {"face", "license_plate", "document_text"} else 0.65
        scores.append(_clamp01((detection.confidence * 0.65) + (detection.area * 0.25) + (sensitivity * 0.10)))
    return semantic_pressure_from_value(sum(scores) / len(scores), sources=("yolo_roi",))


def semantic_pressure_from_context_signals(
    context_signals: Sequence[Mapping[str, Any]],
) -> SemanticPressure:
    """Convert bounded context signals into semantic pressure."""

    if not context_signals:
        return semantic_pressure_from_value(0.0, sources=("context_signal",))

    signal_values: list[float] = []
    keys = ("texture_complexity", "entropy_score", "edge_density", "sensitivity_score")
    for signal in context_signals:
        values = [_clamp01(signal.get(key, 0.0)) for key in keys]
        signal_values.append(sum(values) / len(values))
    return semantic_pressure_from_value(sum(signal_values) / len(signal_values), sources=("context_signal",))


def fuse_semantic_pressures(
    pressures: Iterable[SemanticPressure],
) -> SemanticPressure:
    """Fuse semantic pressures into one bounded pressure field."""

    pressure_list = tuple(pressures)
    if not pressure_list:
        return semantic_pressure_from_value(0.0, sources=("empty",))
    fused_value = _clamp01(
        (max(pressure.value for pressure in pressure_list) * 0.55)
        + (sum(pressure.value for pressure in pressure_list) / len(pressure_list) * 0.45)
    )
    sources: list[str] = []
    for pressure in pressure_list:
        sources.extend(pressure.sources)
    return semantic_pressure_from_value(fused_value, sources=tuple(dict.fromkeys(sources)))


def semantic_pressure_from_value(
    value: float,
    *,
    sources: tuple[str, ...],
) -> SemanticPressure:
    """Convert a scalar into bounded lattice pressure parameters."""

    bounded = _clamp01(value)
    return SemanticPressure(
        value=bounded,
        lattice_density_multiplier=1.0 + bounded,
        phason_strain_factor=bounded / PHI,
        z_modifier=bounded * PHI,
        sources=sources,
    )


def calculate_z_value(
    w: float,
    x: float,
    y: float,
    z: float,
    *,
    phi: float = PHI,
    z_modifier: float = 0.0,
) -> ZValueResult:
    """Calculate bounded Z=(y(w+x)-yz)+z^3+phi^5+modifier."""

    inputs = (_clamp01(w), _clamp01(x), _clamp01(y), _clamp01(z))
    bounded_modifier = max(-(phi**5), min(phi**5, float(z_modifier)))
    raw_z = (
        inputs[2] * (inputs[0] + inputs[1])
        - inputs[2] * inputs[3]
        + inputs[3] ** 3
        + phi**5
        + bounded_modifier
    )
    normalizer = (phi**5) + 2.0
    normalized = _clamp01(raw_z / normalizer)
    clamped = (
        inputs != (w, x, y, z)
        or bounded_modifier != z_modifier
        or normalized in {0.0, 1.0}
    )
    return ZValueResult(
        raw_z=raw_z,
        normalized_z=normalized,
        inputs_wxyz=inputs,
        z_modifier=bounded_modifier,
        clamped=clamped,
    )


def apply_pressure_to_tile_params(
    tile: PenroseTile,
    pressure: SemanticPressure,
) -> dict[str, Any]:
    """Apply pressure as metadata without changing Penrose geometry."""

    validation = validate_penrose_tile(tile)
    z_value = calculate_z_value(*_state_from_tile(tile), z_modifier=pressure.z_modifier)
    return {
        "schema": "ffed.qlc.pressurized_tile_params.v1",
        "tile_id": tile.tile_id,
        "tile_type": tile.tile_type,
        "geometry_preserved": validation.valid,
        "edge_length": tile.edge_length,
        "lattice_density_multiplier": pressure.lattice_density_multiplier,
        "phason_strain_factor": pressure.phason_strain_factor,
        "z_modifier": pressure.z_modifier,
        "z_value": {
            "schema": Z_VALUE_SCHEMA,
            "raw_z": z_value.raw_z,
            "normalized_z": z_value.normalized_z,
            "inputs_wxyz": list(z_value.inputs_wxyz),
            "clamped": z_value.clamped,
        },
        "raw_payload_embedded": False,
        "claim_boundary": "pressure_changes_metadata_not_penrose_geometry",
    }


def _state_from_tile(tile: PenroseTile) -> tuple[float, float, float, float]:
    validation = validate_penrose_tile(tile)
    angle_signal = 36.0 if tile.tile_type == "thin" else 72.0
    return (
        _clamp01(validation.area),
        _clamp01(tile.edge_length),
        _clamp01(angle_signal / 144.0),
        _clamp01(len(validation.edge_signatures) / 4.0),
    )


def _normalize_rgba(pixel: Sequence[int]) -> tuple[int, int, int, int]:
    padded = list(pixel[:4]) + [255, 255, 255, 255]
    return tuple(max(0, min(255, int(value))) for value in padded[:4])  # type: ignore[return-value]


def _rgba_histogram(pixels: Sequence[tuple[int, int, int, int]]) -> tuple[int, ...]:
    buckets = [0] * 16
    for pixel in pixels:
        for value in pixel:
            buckets[min(15, value // 16)] += 1
    return tuple(buckets)


def _length_bucket(length: int) -> str:
    if length < 32:
        return "short"
    if length < 256:
        return "medium"
    return "long"


def _fingerprint(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def _clamp01(value: Any) -> float:
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        numeric = 0.0
    return min(1.0, max(0.0, numeric))
