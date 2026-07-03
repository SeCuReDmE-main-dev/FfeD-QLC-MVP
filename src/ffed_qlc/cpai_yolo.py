"""CodeProject.AI / YOLO metadata-only integration helpers."""

from __future__ import annotations

from dataclasses import dataclass
import json
from typing import Any, Mapping, Sequence
from urllib.error import URLError
from urllib.request import Request, urlopen

from .mesh_proof import build_celebrum_roi_map
from .particle_pressure import semantic_pressure_from_yolo_rois


DEFAULT_CPAI_URL = "http://localhost:32168"
TRAINING_MODULE = "TrainingObjectDetectionYOLOv5"
DETECTION_ROUTE = "/v1/vision/detection"
CUSTOM_MODEL_LIST_ROUTE = "/v1/vision/custom/list"


@dataclass(frozen=True)
class CpaiProbeResult:
    """Metadata-only CPAI probe result."""

    cpai_url: str
    available: bool
    status: str
    dry_run: bool
    routes_checked: tuple[str, ...]
    error_type: str | None = None


@dataclass(frozen=True)
class YoloTrainingPlan:
    """Dry-run training plan; it never starts a long job."""

    cpai_url: str
    module: str
    model_name: str
    dataset_name: str
    epochs: int
    steps: tuple[str, ...]
    requires_ui_confirmation: bool
    training_started: bool = False
    raw_image_embedded: bool = False


def probe_cpai_status(
    cpai_url: str = DEFAULT_CPAI_URL,
    *,
    dry_run: bool = True,
    timeout_seconds: float = 0.25,
) -> dict[str, Any]:
    """Probe CPAI root status or return dry-run metadata."""

    if dry_run:
        result = CpaiProbeResult(
            cpai_url=cpai_url,
            available=False,
            status="not_contacted",
            dry_run=True,
            routes_checked=("/",),
        )
        return _probe_to_mapping(result)
    try:
        request = Request(cpai_url.rstrip("/") + "/", method="GET")
        with urlopen(request, timeout=timeout_seconds) as response:  # nosec - local dev probe
            available = 200 <= int(response.status) < 500
        result = CpaiProbeResult(
            cpai_url=cpai_url,
            available=available,
            status="available" if available else "unavailable",
            dry_run=False,
            routes_checked=("/",),
        )
    except (URLError, TimeoutError, OSError, ValueError) as exc:
        result = CpaiProbeResult(
            cpai_url=cpai_url,
            available=False,
            status="unavailable",
            dry_run=False,
            routes_checked=("/",),
            error_type=type(exc).__name__,
        )
    return _probe_to_mapping(result)


def probe_yolo_detection_routes(
    cpai_url: str = DEFAULT_CPAI_URL,
    *,
    dry_run: bool = True,
) -> dict[str, Any]:
    """Return metadata for YOLO detection and custom model routes."""

    return {
        "schema": "ffed.qlc.cpai_yolo_probe.v1",
        "cpai_url": cpai_url,
        "routes": [DETECTION_ROUTE, CUSTOM_MODEL_LIST_ROUTE],
        "dry_run": dry_run,
        "raw_image_embedded": False,
        "server_copied": False,
    }


def probe_yolo_training_module(
    cpai_url: str = DEFAULT_CPAI_URL,
    *,
    dry_run: bool = True,
) -> dict[str, Any]:
    """Return metadata for the YOLOv5 training module."""

    return {
        "schema": "ffed.qlc.cpai_yolo_training_probe.v1",
        "cpai_url": cpai_url,
        "module": TRAINING_MODULE,
        "model_info_route": "/v1/vision/custom/model/info",
        "dataset_info_route": "/v1/vision/custom/dataset/info",
        "dry_run": dry_run,
        "training_started": False,
        "raw_image_embedded": False,
    }


def plan_yolo_training(
    *,
    cpai_url: str = DEFAULT_CPAI_URL,
    model_name: str = "ffed-qlc-yolo",
    dataset_name: str = "ffed-qlc-metadata-only",
    epochs: int = 10,
    requires_ui_confirmation: bool = True,
) -> dict[str, Any]:
    """Plan YOLO training without executing it."""

    bounded_epochs = max(1, min(1000, int(epochs)))
    plan = YoloTrainingPlan(
        cpai_url=cpai_url,
        module=TRAINING_MODULE,
        model_name=model_name,
        dataset_name=dataset_name,
        epochs=bounded_epochs,
        steps=("create_dataset", "train_model", "resume_training"),
        requires_ui_confirmation=requires_ui_confirmation,
    )
    return {
        "schema": "ffed.qlc.cpai_yolo_training_plan.v1",
        "cpai_url": plan.cpai_url,
        "module": plan.module,
        "model_name": plan.model_name,
        "dataset_name": plan.dataset_name,
        "epochs": plan.epochs,
        "steps": list(plan.steps),
        "requires_ui_confirmation": plan.requires_ui_confirmation,
        "training_started": plan.training_started,
        "raw_image_embedded": plan.raw_image_embedded,
        "metadata_only": True,
    }


def yolo_detections_to_roi_pressure(
    detections: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    """Convert detections to ROI map and semantic pressure hints."""

    roi_map = build_celebrum_roi_map(detections)
    pressure = semantic_pressure_from_yolo_rois(detections)
    return {
        "schema": "ffed.qlc.yolo_roi_pressure.v1",
        "roi_map": roi_map,
        "semantic_pressure": {
            "value": pressure.value,
            "lattice_density_multiplier": pressure.lattice_density_multiplier,
            "phason_strain_factor": pressure.phason_strain_factor,
            "z_modifier": pressure.z_modifier,
            "sources": list(pressure.sources),
        },
        "friction_hints": {
            "semantic_pressure_to_friction": pressure.value,
            "bounded": True,
        },
        "raw_image_embedded": False,
    }


def _probe_to_mapping(result: CpaiProbeResult) -> dict[str, Any]:
    return {
        "schema": "ffed.qlc.cpai_status.v1",
        "cpai_url": result.cpai_url,
        "available": result.available,
        "status": result.status,
        "dry_run": result.dry_run,
        "routes_checked": list(result.routes_checked),
        "error_type": result.error_type,
        "raw_payload_embedded": False,
    }
