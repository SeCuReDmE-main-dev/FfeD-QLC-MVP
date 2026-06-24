from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_mascotte_manifest_expected_assets_exist() -> None:
    manifest = json.loads((ROOT / "assets" / "Mascotte" / "MANIFEST.json").read_text(encoding="utf-8"))

    for guardian in manifest["guardians"]:
        directory = ROOT / guardian["directory"]
        for asset_name in guardian["expected_assets"]:
            assert (directory / asset_name).exists(), f"{guardian['name']} missing {asset_name}"
