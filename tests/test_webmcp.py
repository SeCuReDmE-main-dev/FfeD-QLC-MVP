import json
from pathlib import Path

from ffed_qlc.webmcp import COMMON_TOOLS, THEME, manifest, tool
from fastapi.testclient import TestClient
from ffed_qlc.api import create_app


def test_manifest_has_exact_descriptor_shape():
    payload = manifest()
    names = [entry["name"] for entry in payload["tools"]]
    assert payload["schema"] == "securedme.webmcp.v1"
    assert len(payload["tools"]) == 12
    assert len([name for name in names if name.startswith("ffed_")]) == 10
    assert set(COMMON_TOOLS).issubset(names)
    assert len(names) == len(set(names))
    assert all(entry["inputSchema"]["additionalProperties"] is False for entry in payload["tools"])
    assert all(entry["outputSchema"]["type"] == "object" for entry in payload["tools"])
    assert all(entry["handler"]["kind"] for entry in payload["tools"])


def test_static_exports_match_runtime_and_evidence_gate_shape():
    root = Path(__file__).parents[1]
    assert json.loads((root / "webmcp" / "manifest.json").read_text(encoding="utf-8")) == manifest()
    fixtures = json.loads((root / "webmcp" / "fixtures.json").read_text(encoding="utf-8"))
    assert set(fixtures) == {"tools", "journeys"}
    assert set(fixtures["tools"]) == {item["name"] for item in manifest()["tools"]}
    assert len(fixtures["journeys"]) == 6


def test_training_is_only_staged():
    assert tool("ffed_plan_yolo_training")["mode"] == "STAGE"
    assert "starts training" in manifest()["boundaries"]["externalWrites"]


def test_theme_uses_product_specific_stitch_handoff():
    assert "stitch_ffed_qlc_design_system_landing_page" in THEME["source"]
    assert THEME["tokens"]["focus"] == "#36d7ff"


def test_discovery_is_public_and_invocation_fails_closed(tmp_path):
    client = TestClient(create_app())
    assert len(client.get("/api/v1/webmcp/manifest").json()["tools"]) == 12
    rejected = client.post("/api/v1/webmcp/invoke", json={"name": "ffed_list_source_functions", "arguments": {}})
    assert rejected.status_code == 503
    assert rejected.json()["detail"]["code"] == "GATEWAY_SESSION_REQUIRED"
