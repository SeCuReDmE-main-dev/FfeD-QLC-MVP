import json
import sys

from ffed_qlc.cli import main


CONTEXT_DIGEST = "a" * 64
ARTIFACT_DIGEST = "b" * 64
SIGNATURE_DIGEST = "c" * 64


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
    context = tmp_path / "context.json"
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
    context.write_text(
        json.dumps(
            {
                "context_signals": [
                    {
                        "texture_complexity": 0.35,
                        "entropy_score": 0.42,
                        "edge_density": 0.25,
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
            "--context-json",
            str(context),
            "--media-type",
            "image",
            "--plan-output",
            str(plan),
        ],
    )

    assert main() == 0
    payload = json.loads(proof.read_text(encoding="utf-8"))
    assert payload["plugin_context"]["orchestrator"] == "CeLeBrUm"
    assert payload["plugin_context"]["proof_mode"] == "qlc_protects_simulator_mvp"
    assert payload["plugin_context"]["celebrum_roi_map"]["detection_count"] == 1
    assert payload["plugin_context"]["context_consistency_guard"]["verdict"] == "pass"
    assert payload["plugin_context"]["sensitivity_weighted_obfuscation_policy"]["media_type"] == "image"
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


def test_cli_ecn_handoff_writes_filtered_packet(tmp_path, monkeypatch) -> None:
    orb = tmp_path / "audit-orb.json"
    output = tmp_path / "ecn.json"
    orb.write_text(
        json.dumps(
            {
                "schema": "ffed.qlc.privacy_safe_audit_orb.v1",
                "orb_id": "orb-001",
                "audit_nonce": "nonce-001",
                "event_count": 1,
                "fibonacci_tag": "F8",
                "label_fingerprints": ["label-fp"],
                "events": [
                    {
                        "label": "runtime-export",
                        "fingerprint": "event-fp",
                        "raw_payload_embedded": False,
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    monkeypatch.setattr(
        sys,
        "argv",
        [
            "ffed-qlc",
            "ecn-handoff",
            "--audit-orb-json",
            str(orb),
            "--output",
            str(output),
            "--urgency",
            "high",
            "--destination",
            "ecn://celebrum",
        ],
    )

    assert main() == 0
    payload = json.loads(output.read_text(encoding="utf-8"))
    assert payload["schema"] == "ffed.qlc.ecn_handoff_packet.v1"
    assert payload["urgency"] == "high"
    assert payload["destination"] == "ecn://celebrum"
    assert payload["event_fingerprints"] == ["event-fp"]
    assert payload["raw_payload_embedded"] is False


def test_cli_protect_workflow_writes_gateway_submission(tmp_path, monkeypatch) -> None:
    plain = tmp_path / "plain.bin"
    container = tmp_path / "plain.fqlc"
    detections = tmp_path / "detections.json"
    context = tmp_path / "context.json"
    workflow = tmp_path / "workflow.json"
    plain.write_bytes(b"workflow-cli")
    detections.write_text(
        json.dumps({"detections": [{"class_name": "face", "confidence_score": 0.91}]}),
        encoding="utf-8",
    )
    context.write_text(
        json.dumps({"context_signals": [{"texture_complexity": 0.2, "entropy_score": 0.2, "edge_density": 0.2}]}),
        encoding="utf-8",
    )
    monkeypatch.setenv("FFED_QLC_PASSPHRASE", "passphrase")

    monkeypatch.setattr(sys, "argv", ["ffed-qlc", "pack", "--input", str(plain), "--output", str(container)])
    assert main() == 0

    monkeypatch.setattr(
        sys,
        "argv",
        [
            "ffed-qlc",
            "protect-workflow",
            "--input",
            str(container),
            "--source-id",
            "asset-cli",
            "--output",
            str(workflow),
            "--detections-json",
            str(detections),
            "--context-json",
            str(context),
            "--ecn-destination",
            "",
        ],
    )
    assert main() == 0

    payload = json.loads(workflow.read_text(encoding="utf-8"))
    assert payload["schema"] == "ffed.qlc.protection_workflow_bundle.v1"
    assert payload["gateway_submission"]["schema"] == "ffed.qlc.gateway_submission.v1"
    assert payload["gateway_submission"]["mesh_payload"]["plugin_context"]["orchestrator"] == "CeLeBrUm"


def test_cli_bouncy_castle_status_sign_and_verify_use_provider(tmp_path, monkeypatch) -> None:
    class FakeProvider:
        def __init__(self) -> None:
            self.sign_calls: list[dict[str, str]] = []
            self.verify_calls: list[dict[str, str]] = []

        def status(self) -> dict[str, object]:
            return {
                "provider_available": True,
                "provider": "BouncyCastle",
                "tool": "bcctl",
                "tool_path_source": "FFED_BCCTL_PATH",
                "algorithms": ["Ed25519"],
            }

        def sign_digest(self, *, key_id: str, context_digest: str, artifact_digest: str) -> dict[str, object]:
            self.sign_calls.append(
                {
                    "key_id": key_id,
                    "context_digest": context_digest,
                    "artifact_digest": artifact_digest,
                }
            )
            return {
                "status": "ok",
                "operation": "sign",
                "provider": "BouncyCastle",
                "tool": "bcctl",
                "key_id": key_id,
                "algorithm": "Ed25519",
                "context_digest": context_digest,
                "message_digest": artifact_digest,
                "signature_digest": SIGNATURE_DIGEST,
                "signature_b64": "signature",
                "raw_payload_embedded": False,
            }

        def verify_digest(
            self,
            *,
            key_id: str,
            context_digest: str,
            message_digest: str,
            signature_digest: str,
        ) -> dict[str, object]:
            self.verify_calls.append(
                {
                    "key_id": key_id,
                    "context_digest": context_digest,
                    "message_digest": message_digest,
                    "signature_digest": signature_digest,
                }
            )
            return {
                "status": "ok",
                "operation": "verify",
                "provider": "BouncyCastle",
                "tool": "bcctl",
                "key_id": key_id,
                "verified": True,
                "context_digest": context_digest,
                "message_digest": message_digest,
                "signature_digest": signature_digest,
                "raw_payload_embedded": False,
            }

    provider = FakeProvider()
    monkeypatch.setattr("ffed_qlc.cli.BcctlProvider.from_environment", lambda: provider)

    status_output = tmp_path / "bc-status.json"
    monkeypatch.setattr(sys, "argv", ["ffed-qlc", "bc-status", "--output", str(status_output)])
    assert main() == 0
    assert json.loads(status_output.read_text(encoding="utf-8"))["provider_available"] is True

    sign_output = tmp_path / "bc-sign.json"
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "ffed-qlc",
            "bc-sign",
            "--key-id",
            "perimeter-key",
            "--context-digest",
            CONTEXT_DIGEST,
            "--artifact-digest",
            ARTIFACT_DIGEST,
            "--output",
            str(sign_output),
        ],
    )
    assert main() == 0
    assert json.loads(sign_output.read_text(encoding="utf-8"))["signature_digest"] == SIGNATURE_DIGEST

    verify_output = tmp_path / "bc-verify.json"
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "ffed-qlc",
            "bc-verify",
            "--key-id",
            "perimeter-key",
            "--context-digest",
            CONTEXT_DIGEST,
            "--message-digest",
            ARTIFACT_DIGEST,
            "--signature-digest",
            SIGNATURE_DIGEST,
            "--output",
            str(verify_output),
        ],
    )
    assert main() == 0
    assert json.loads(verify_output.read_text(encoding="utf-8"))["verified"] is True
    assert provider.sign_calls[0]["artifact_digest"] == ARTIFACT_DIGEST
    assert provider.verify_calls[0]["signature_digest"] == SIGNATURE_DIGEST


def test_cli_protect_workflow_can_add_bouncy_castle_perimeter_receipt(tmp_path, monkeypatch) -> None:
    class FakeProvider:
        def sign_digest(self, *, key_id: str, context_digest: str, artifact_digest: str) -> dict[str, object]:
            return {
                "status": "ok",
                "operation": "sign",
                "provider": "BouncyCastle",
                "tool": "bcctl",
                "key_id": key_id,
                "algorithm": "Ed25519",
                "context_digest": context_digest,
                "message_digest": artifact_digest,
                "signature_digest": SIGNATURE_DIGEST,
                "signature_b64": "signature",
                "raw_payload_embedded": False,
            }

    plain = tmp_path / "plain.bin"
    container = tmp_path / "plain.fqlc"
    workflow = tmp_path / "workflow.json"
    plain.write_bytes(b"workflow-cli-bc")
    monkeypatch.setenv("FFED_QLC_PASSPHRASE", "passphrase")
    monkeypatch.setattr("ffed_qlc.bc_perimeter.BcctlProvider.from_environment", lambda: FakeProvider())

    monkeypatch.setattr(sys, "argv", ["ffed-qlc", "pack", "--input", str(plain), "--output", str(container)])
    assert main() == 0

    monkeypatch.setattr(
        sys,
        "argv",
        [
            "ffed-qlc",
            "protect-workflow",
            "--input",
            str(container),
            "--source-id",
            "asset-cli-bc",
            "--output",
            str(workflow),
            "--bcctl-sign",
            "--bcctl-key-id",
            "perimeter-key",
        ],
    )
    assert main() == 0

    payload = json.loads(workflow.read_text(encoding="utf-8"))
    assert payload["perimeter_receipt"]["schema"] == "ffed.qlc.bouncy_castle_perimeter_receipt.v1"
    assert payload["perimeter_receipt"]["signature_digest"] == SIGNATURE_DIGEST
    assert payload["perimeter_receipt"]["raw_payload_embedded"] is False
