"""SecuredMe WebMCP v1 discovery contract for FfeD-QLC."""

from __future__ import annotations

from typing import Any

SCHEMA = "securedme.webmcp.v1"
PRODUCT_SLUG = "ffed-qlc"
COMMON_TOOLS = ("securedme_companion_context", "securedme_qbit_plan_handoff")
THEME = {
    "slug": PRODUCT_SLUG,
    "source": "securedme-site/assets/landing/secureme.ca-product/education/FfeD-QLC-MVP/desing/stitch_ffed_qlc_design_system_landing_page/stitch_ffed_qlc_design_system_landing_page/desing.md",
    "sourceStatus": "verified-product-stitch",
    "assets": {"dark": "landing dark.png", "light": "landing light.png"},
    "tokens": {"background": "#070b1b", "surface": "#101936", "primary": "#3976ff", "secondary": "#7b52ff", "accent": "#d8a548", "text": "#f7fbff", "muted": "#9aa8c7", "focus": "#36d7ff"},
    "typography": {"display": "system-ui, sans-serif", "body": "system-ui, sans-serif", "code": "monospace"},
    "fallback": "High-contrast system fonts, visible focus, and textual gate labels.",
}


def _object(properties: dict[str, Any] | None = None, required: list[str] | None = None) -> dict[str, Any]:
    return {"type": "object", "properties": properties or {}, "required": required or [], "additionalProperties": False}


def _tool(name: str, mode: str, description: str, input_schema: dict[str, Any], handler: str) -> dict[str, Any]:
    parts = handler.split(" ", 1)
    mapped = {"kind": "http", "method": parts[0], "path": parts[1]} if len(parts) == 2 and parts[0] in {"GET", "POST", "PUT", "DELETE"} else {"kind": "local", "operation": handler.replace(" ", "_")}
    return {"name": name, "title": name.replace("_", " ").title(), "description": description, "mode": mode, "availability": "available", "inputSchema": input_schema, "outputSchema": {"type": "object", "required": ["status", "tool", "data", "secret_values_exposed"], "properties": {"status": {"const": "success"}, "tool": {"const": name}, "data": {}, "secret_values_exposed": {"const": False}}, "additionalProperties": False}, "handler": mapped}


LATTICE = {"engine": {"type": "string", "enum": ["inflation", "cut_project"]}, "target_tile_count": {"type": "integer", "minimum": 1, "maximum": 200}}
TOOLS = (
    _tool("ffed_list_source_functions", "READ", "List compiled source-function profiles and their redacted graph.", _object(), "GET /api/source-functions"),
    _tool("ffed_build_lattice", "STAGE", "Build a bounded Penrose lattice review candidate.", _object(LATTICE, ["engine", "target_tile_count"]), "POST /api/lattice/build"),
    _tool("ffed_classify_lattice", "READ", "Classify tiles with the existing plithogenic classifier.", _object(LATTICE, ["engine", "target_tile_count"]), "POST /api/lattice/classify"),
    _tool("ffed_validate_lattice", "READ", "Validate tile admissions as accept, suspend, or reject.", _object(LATTICE, ["engine", "target_tile_count"]), "POST /api/lattice/validate"),
    _tool("ffed_build_audit_orb", "STAGE", "Build a metadata-only redacted audit orb.", _object(LATTICE, ["engine", "target_tile_count"]), "POST /api/orbs/build"),
    _tool("ffed_export_lattice_template", "STAGE", "Prepare the VAD reusable lattice template.", _object(), "POST /api/export/lattice-template"),
    _tool("ffed_inspect_fqlc2_container", "READ", "Inspect a bounded FQLC2 container without exposing plaintext or key material.", _object({"container_base64": {"type": "string", "minLength": 8, "maxLength": 4000000}}, ["container_base64"]), "POST /api/v1/fqlc2/inspect"),
    _tool("ffed_preview_synthetic_roundtrip", "STAGE", "Preview a synthetic fixture roundtrip; no private key is returned.", _object({"fixture_id": {"type": "string", "minLength": 1, "maxLength": 80}, "recipient_count": {"type": "integer", "minimum": 1, "maximum": 8}, "signed": {"type": "boolean"}}, ["fixture_id"]), "POST /api/v1/fqlc2/synthetic-roundtrip"),
    _tool("ffed_inspect_cpai_status", "READ", "Inspect the allowlisted local CodeProject.AI node with sanitized output.", _object(), "GET /api/cpai/status"),
    _tool("ffed_plan_yolo_training", "STAGE", "Prepare a metadata-only YOLO training plan; training is never started.", _object({"cpai_url": {"type": "string", "minLength": 8, "maxLength": 200}, "model_name": {"type": "string", "minLength": 1, "maxLength": 80}, "dataset_name": {"type": "string", "minLength": 1, "maxLength": 80}, "epochs": {"type": "integer", "minimum": 1, "maximum": 100}}, ["cpai_url", "model_name", "dataset_name"]), "POST /api/cpai/yolo/training/plan"),
    _tool("securedme_companion_context", "READ", "Read a sanitized Hero Book projection without transferring progression authority.", _object(), "Gateway session projection"),
    _tool("securedme_qbit_plan_handoff", "STAGE", "Prepare a Qbit return proposal; AlgoQuest alone may admit it.", _object({"mission_ref": {"type": "string", "minLength": 1, "maxLength": 120}, "artifact_refs": {"type": "array", "maxItems": 20, "items": {"type": "string", "maxLength": 160}}}, ["mission_ref"]), "local proposal only"),
)


def manifest() -> dict[str, Any]:
    return {"schema": SCHEMA, "manifestVersion": "1.0.0", "product": {"slug": PRODUCT_SLUG, "name": "FfeD-QLC MVP", "status": "public-pre-alpha", "canonicalStateOwner": "algoquest", "applicationStateOwner": "ffed-qlc", "pagePatterns": ["https://ffed-qlc.securedme.ca/", "http://localhost:5173/"], "theme": THEME}, "boundaries": {"authority": "Supervised metadata-only education and research scaffold; no security certification.", "secrets": "Plaintext, private keys, raw T/I/F, raw media and credentials are forbidden.", "externalWrites": "No WebMCP tool starts training, provisions infrastructure, opens a browser or executes a shell.", "heroProgression": "AlgoQuest alone owns Hero Book progression and evidence admission."}, "tools": list(TOOLS)}


def tool(name: str) -> dict[str, Any] | None:
    return next((item for item in TOOLS if item["name"] == name), None)
