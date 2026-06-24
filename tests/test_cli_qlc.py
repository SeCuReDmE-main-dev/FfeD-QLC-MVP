import json
import sys

from ffed_qlc.cli import main


def test_cli_verify_writes_manifest(tmp_path, monkeypatch) -> None:
    plain = tmp_path / "plain.bin"
    container = tmp_path / "plain.fqlc"
    manifest = tmp_path / "manifest.json"
    plain.write_bytes(b"qlc-cli")
    monkeypatch.setenv("FFED_QLC_PASSPHRASE", "passphrase")

    monkeypatch.setattr(sys, "argv", ["ffed-qlc", "pack", "--input", str(plain), "--output", str(container)])
    assert main() == 0

    monkeypatch.setattr(sys, "argv", ["ffed-qlc", "verify", "--input", str(container), "--output", str(manifest)])
    assert main() == 0

    payload = json.loads(manifest.read_text(encoding="utf-8"))
    assert payload["valid"] is True
    assert payload["plaintext_bytes_revealed"] is False


def test_cli_yolo_pack_writes_container_and_proof(tmp_path, monkeypatch) -> None:
    image = tmp_path / "image.bin"
    detections = tmp_path / "detections.json"
    container = tmp_path / "image.fqlc"
    proof = tmp_path / "proof.json"
    plan = tmp_path / "plan.json"
    image.write_bytes(b"fake-image-bytes")
    detections.write_text(
        json.dumps(
            {
                "predictions": [
                    {
                        "class_name": "screen",
                        "confidence_score": 0.88,
                        "bounding_box_normalized": [0.2, 0.2, 0.5, 0.5],
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv("FFED_QLC_PASSPHRASE", "passphrase")

    monkeypatch.setattr(
        sys,
        "argv",
        [
            "ffed-qlc",
            "yolo-pack",
            "--input",
            str(image),
            "--output",
            str(container),
            "--source-id",
            "image-001",
            "--proof-output",
            str(proof),
            "--detections-json",
            str(detections),
            "--plan-output",
            str(plan),
        ],
    )

    assert main() == 0
    payload = json.loads(proof.read_text(encoding="utf-8"))
    assert payload["plugin_context"]["orchestrator"] == "CeLeBrUm"
    assert payload["plugin_context"]["proof_mode"] == "qlc_protects_simulator_mvp"
    assert payload["plugin_context"]["celebrum_roi_map"]["detection_count"] == 1
    assert payload["plugin_context"]["simulator_protection_case"]["qlc_role"] == "protection_layer_for_simulator_artifacts"
    assert payload["memories"][1]["provenance"]["privacy_note"].startswith("detection metadata only")
    assert container.exists()
    assert plan.exists()


def test_cli_audit_orb_writes_privacy_safe_record(tmp_path, monkeypatch) -> None:
    events = tmp_path / "events.json"
    output = tmp_path / "audit-orb.json"
    events.write_text(
        json.dumps(
            {
                "events": [
                    {
                        "label": "runtime-export",
                        "source": "fnp-qnn",
                        "secret_manager_ref": "vault://simulator/runtime",
                    }
                ]
            }
        ),
        encoding="utf-8",
    )

    monkeypatch.setattr(
        sys,
        "argv",
        [
            "ffed-qlc",
            "audit-orb",
            "--orb-id",
            "orb-001",
            "--events-json",
            str(events),
            "--output",
            str(output),
        ],
    )

    assert main() == 0
    payload = json.loads(output.read_text(encoding="utf-8"))
    assert payload["secret_policy"]["raw_secrets_allowed"] is False
    assert payload["events"][0]["raw_payload_embedded"] is False
