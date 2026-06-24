from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_mascotte_manifest_expected_assets_exist() -> None:
    manifest = json.loads((ROOT / "assets" / "Mascotte" / "MANIFEST.json").read_text(encoding="utf-8"))

    assert manifest["schema"] == "ffed.qlc.design_asset_manifest.v1"
    for guardian in manifest["guardians"]:
        directory = ROOT / guardian["directory"]
        for asset_name in guardian["expected_assets"]:
            assert (directory / asset_name).exists(), f"{guardian['name']} missing {asset_name}"

    for group in manifest["design_assets"]:
        directory = ROOT / group["directory"]
        for asset_name in group["expected_assets"]:
            assert (directory / asset_name).exists(), f"{group['group']} missing {asset_name}"
