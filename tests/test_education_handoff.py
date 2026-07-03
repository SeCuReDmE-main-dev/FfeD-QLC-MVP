from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
HIERARCHY = "I -> I_system^S -> D_f -> dF -> i_fractal"


def _read_json(path: str):
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def test_webauth_templates_preserve_security_and_math_contracts() -> None:
    codex = _read_json(".codex/webauth-template.json")
    antigravity = _read_json(".antigravity/webauth-template.json")

    for payload, platform in [(codex, "codex"), (antigravity, "antigravity")]:
        assert payload["schema"] == "securedme.education.webauth-template.v1"
        assert payload["app"]["slug"] == "ffed-qlc"
        assert payload["app"]["canonical_domain"] == "ffed-qlc.securedme.ca"
        assert payload["app"]["status"] == "pre-alpha"
        assert payload["platform"] == platform
        assert payload["auth_policy"]["selected_auth_source"] == "web-auth"
        assert payload["auth_policy"]["fingerprint_acceptance"]["required"] is True
        assert payload["auth_policy"]["student_api_keys_required"] is False
        assert payload["auth_policy"]["raw_secret_stored"] is False
        assert payload["math_contract"]["preserve_hierarchy"] == HIERARCHY
        assert payload["math_contract"]["preserve_penrose_contract"] is True
        assert payload["math_contract"]["raw_tif_export_allowed"] is False
        assert payload["unsupported_routes"]["ollama_school_route"].startswith("rejected")

    assert codex["provider_mapping"] == {"OpenAI": "Codex", "ChatGPT": "Codex"}
    assert antigravity["provider_mapping"] == {"Google": "Antigravity", "Gemini": "Antigravity"}


def test_adapter_maps_route_providers_and_reject_unsupported_school_route() -> None:
    codex = _read_json(".codex/securedme-adapter-map.json")
    antigravity = _read_json(".antigravity/securedme-adapter-map.json")

    for payload in (codex, antigravity):
        assert payload["schema"] == "securedme.education.adapter-map.v1"
        assert payload["provider_mapping"]["OpenAI"] == "Codex"
        assert payload["provider_mapping"]["ChatGPT"] == "Codex"
        assert payload["provider_mapping"]["Google"] == "Antigravity"
        assert payload["provider_mapping"]["Gemini"] == "Antigravity"
        assert payload["math_contract"]["hierarchy"] == HIERARCHY
        assert payload["math_contract"]["source_graph"] == "secondary provenance graph"
        assert payload["math_contract"]["cpai"] == "metadata-only; no copied CodeProject AI server"
        assert payload["unsupported_routes"]["ollama_school_route"] == "rejected_for_official_school_route"
        assert payload["mcp"]["status"] == "planned"


def test_marketplaces_and_skills_are_metadata_only_and_specific_to_qlc() -> None:
    codex_marketplace = _read_json(".codex/marketplace.json")
    antigravity_marketplace = _read_json(".antigravity/marketplace.json")
    codex_skill = (ROOT / ".codex/plugins/securedme-ffed-qlc-codex-adapter/skills/securedme-ffed-qlc-codex-adapter/SKILL.md").read_text(
        encoding="utf-8"
    )
    antigravity_skill = (ROOT / ".antigravity/skills/securedme-ffed-qlc-antigravity-adapter/SKILL.md").read_text(
        encoding="utf-8"
    )

    assert codex_marketplace["plugins"][0]["name"] == "securedme-ffed-qlc-codex-adapter"
    assert antigravity_marketplace["extensions"][0]["name"] == "securedme-ffed-qlc-antigravity-adapter"
    assert "validated thin/thick rhombi" in codex_skill
    assert "metadata-only" in codex_skill
    assert "Reject Ollama" in codex_skill
    assert "validated thin/thick rhombi" in antigravity_skill
    assert "metadata-only" in antigravity_skill
    assert "Reject Ollama" in antigravity_skill
