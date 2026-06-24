from __future__ import annotations

import json
from pathlib import Path

import pytest

from ffed_qlc import inspect_qlc_workflow_bundle
from ffed_qlc.cli import main


FIXTURE_ROOT = Path(__file__).parent / "fixtures" / "qlc_contract"


def test_inspector_accepts_contract_fixtures() -> None:
    for name in ("qlc_workflow_image.json", "qlc_workflow_document.json", "qlc_workflow_video.json"):
        bundle = json.loads((FIXTURE_ROOT / name).read_text(encoding="utf-8"))
        inspection = inspect_qlc_workflow_bundle(bundle)

        assert inspection["success"] is True
        assert inspection["schema"] == "ffed.qlc.workflow_inspection.v1"
        assert inspection["redaction_verdict"] == "metadata_only_pass"
        assert inspection["raw_payload_embedded"] is False
        assert inspection["fingerprints"]["bundle"]


def test_inspector_rejects_forbidden_fixture() -> None:
    bundle = json.loads((FIXTURE_ROOT / "qlc_workflow_forbidden_raw.json").read_text(encoding="utf-8"))

    with pytest.raises(ValueError, match="raw QLC workflow field"):
        inspect_qlc_workflow_bundle(bundle)


def test_inspect_workflow_cli_emits_metadata_only_summary(capsys: pytest.CaptureFixture[str]) -> None:
    code = main(["inspect-workflow", "--bundle", str(FIXTURE_ROOT / "qlc_workflow_image.json")])

    assert code == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["media_type"] == "image"
    assert payload["swop_level"] == "high"
    assert "raw_image" not in json.dumps(payload)
