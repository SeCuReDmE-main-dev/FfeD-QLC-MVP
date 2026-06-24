from __future__ import annotations

import argparse
import getpass
import json
import os
from pathlib import Path
from typing import Any

from .admissibility import Evidence, evaluate_evidence
from .audit_orb import build_privacy_safe_audit_orb
from .docker_map import DEFAULT_STUDYCASE_BLOCKS
from .mesh_proof import build_fnpqnn_runtime_payload, build_gateway_command_plan
from .structural_transform import inspect_container, pack_bytes, unpack_bytes, verify_container


def main() -> int:
    parser = argparse.ArgumentParser(description="FfeD-QLC public MVP CLI")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("map", help="Print the default Docker/CPAI study-case map")

    gate = sub.add_parser("gate", help="Evaluate one evidence item")
    gate.add_argument("--source-id", required=True)
    gate.add_argument("--source-type", default="document")
    gate.add_argument("--trust-score", type=float, required=True)
    gate.add_argument("--has-provenance", action="store_true")
    gate.add_argument("--claim-scope", default="bounded_software")

    pack = sub.add_parser("pack", help="Pack a file into an authenticated QLC-style container")
    pack.add_argument("--input", required=True)
    pack.add_argument("--output", required=True)
    pack.add_argument("--passphrase")
    pack.add_argument("--passphrase-env", default="FFED_QLC_PASSPHRASE")

    unpack = sub.add_parser("unpack", help="Unpack an authenticated QLC-style container")
    unpack.add_argument("--input", required=True)
    unpack.add_argument("--output", required=True)
    unpack.add_argument("--passphrase")
    unpack.add_argument("--passphrase-env", default="FFED_QLC_PASSPHRASE")

    verify = sub.add_parser("verify", help="Authenticate a QLC container and print a safe manifest")
    verify.add_argument("--input", required=True)
    verify.add_argument("--passphrase")
    verify.add_argument("--passphrase-env", default="FFED_QLC_PASSPHRASE")
    verify.add_argument("--output")
    verify.add_argument("--no-decrypt", action="store_true", help="Inspect manifest without authenticating plaintext")

    proof = sub.add_parser("mesh-proof", help="Build a FNP-QNN runtime proof payload from a QLC container")
    proof.add_argument("--input", required=True)
    proof.add_argument("--source-id", required=True)
    proof.add_argument("--output", required=True)
    proof.add_argument("--codeproject-url", default="http://localhost:32168")
    proof.add_argument("--known-server", action="append", default=[])
    proof.add_argument("--epochs", type=int, default=4)
    proof.add_argument("--detections-json", help="YOLO detections JSON file; metadata only, no image bytes")
    proof.add_argument(
        "--proof-mode",
        choices=[
            "simulator_supports_qlc_complexity",
            "qlc_protects_simulator_mvp",
        ],
        default="simulator_supports_qlc_complexity",
    )
    proof.add_argument("--plan-output")

    yolo_pack = sub.add_parser("yolo-pack", help="Pack an image/file and create a CeLeBrUm/FNP-QNN proof payload")
    yolo_pack.add_argument("--input", required=True)
    yolo_pack.add_argument("--output", required=True)
    yolo_pack.add_argument("--source-id", required=True)
    yolo_pack.add_argument("--proof-output", required=True)
    yolo_pack.add_argument("--passphrase")
    yolo_pack.add_argument("--passphrase-env", default="FFED_QLC_PASSPHRASE")
    yolo_pack.add_argument("--detections-json", help="YOLO detections JSON file; metadata only, no image bytes")
    yolo_pack.add_argument("--codeproject-url", default="http://localhost:32168")
    yolo_pack.add_argument("--known-server", action="append", default=[])
    yolo_pack.add_argument("--epochs", type=int, default=4)
    yolo_pack.add_argument(
        "--proof-mode",
        choices=[
            "simulator_supports_qlc_complexity",
            "qlc_protects_simulator_mvp",
        ],
        default="qlc_protects_simulator_mvp",
    )
    yolo_pack.add_argument("--plan-output")

    audit_orb = sub.add_parser("audit-orb", help="Build a privacy-safe ProGuarD audit orb from event metadata")
    audit_orb.add_argument("--orb-id", required=True)
    audit_orb.add_argument("--events-json", required=True)
    audit_orb.add_argument("--output", required=True)
    audit_orb.add_argument("--epsilon", type=float, default=1.0)

    args = parser.parse_args()

    if args.command == "map":
        print(json.dumps([block.__dict__ for block in DEFAULT_STUDYCASE_BLOCKS], indent=2))
        return 0

    if args.command == "gate":
        evidence = Evidence(
            source_id=args.source_id,
            source_type=args.source_type,
            trust_score=args.trust_score,
            has_provenance=args.has_provenance,
            claim_scope=args.claim_scope,
        )
        print(evaluate_evidence(evidence).value)
        return 0

    if args.command == "pack":
        passphrase = _resolve_passphrase(args.passphrase, args.passphrase_env)
        plaintext = Path(args.input).read_bytes()
        Path(args.output).write_bytes(pack_bytes(plaintext, passphrase))
        print(args.output)
        return 0

    if args.command == "unpack":
        passphrase = _resolve_passphrase(args.passphrase, args.passphrase_env)
        container = Path(args.input).read_bytes()
        Path(args.output).write_bytes(unpack_bytes(container, passphrase))
        print(args.output)
        return 0

    if args.command == "verify":
        container = Path(args.input).read_bytes()
        if args.no_decrypt:
            record = inspect_container(container)
        else:
            passphrase = _resolve_passphrase(args.passphrase, args.passphrase_env)
            record = verify_container(container, passphrase)
        output = json.dumps(record, indent=2, sort_keys=True)
        if args.output:
            Path(args.output).write_text(output, encoding="utf-8")
            print(args.output)
        else:
            print(output)
        return 0

    if args.command == "mesh-proof":
        container = Path(args.input).read_bytes()
        payload = build_fnpqnn_runtime_payload(
            source_id=args.source_id,
            qlc_container=container,
            yolo_detections=_load_detections(args.detections_json),
            codeproject_url=args.codeproject_url,
            known_mesh_servers=args.known_server,
            epochs=args.epochs,
            proof_mode=args.proof_mode,
        )
        Path(args.output).write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
        if args.plan_output:
            plan = build_gateway_command_plan(qlc_payload_path=args.output, codeproject_url=args.codeproject_url)
            Path(args.plan_output).write_text(json.dumps(plan, indent=2, sort_keys=True), encoding="utf-8")
        print(args.output)
        return 0

    if args.command == "yolo-pack":
        passphrase = _resolve_passphrase(args.passphrase, args.passphrase_env)
        plaintext = Path(args.input).read_bytes()
        container = pack_bytes(plaintext, passphrase)
        Path(args.output).write_bytes(container)
        payload = build_fnpqnn_runtime_payload(
            source_id=args.source_id,
            qlc_container=container,
            yolo_detections=_load_detections(args.detections_json),
            codeproject_url=args.codeproject_url,
            known_mesh_servers=args.known_server,
            epochs=args.epochs,
            proof_mode=args.proof_mode,
        )
        Path(args.proof_output).write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
        if args.plan_output:
            plan = build_gateway_command_plan(qlc_payload_path=args.proof_output, codeproject_url=args.codeproject_url)
            Path(args.plan_output).write_text(json.dumps(plan, indent=2, sort_keys=True), encoding="utf-8")
        print(args.output)
        print(args.proof_output)
        return 0

    if args.command == "audit-orb":
        events = _load_events(args.events_json)
        payload = build_privacy_safe_audit_orb(orb_id=args.orb_id, events=events, epsilon=args.epsilon)
        Path(args.output).write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
        print(args.output)
        return 0

    return 2


def _resolve_passphrase(value: str | None, env_name: str | None) -> str:
    if value:
        return value
    if env_name:
        env_value = os.environ.get(env_name)
        if env_value:
            return env_value
    return getpass.getpass("QLC passphrase: ")


def _load_detections(path: str | None) -> list[dict[str, Any]]:
    if not path:
        return []
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if isinstance(payload, dict):
        if isinstance(payload.get("predictions"), list):
            payload = payload["predictions"]
        elif isinstance(payload.get("detections"), list):
            payload = payload["detections"]
        elif isinstance(payload.get("regions"), list):
            payload = payload["regions"]
        else:
            payload = [payload]
    if not isinstance(payload, list):
        raise ValueError("detections JSON must be a list or an object containing predictions/detections/regions")
    return [item for item in payload if isinstance(item, dict)]


def _load_events(path: str) -> list[dict[str, Any]]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if isinstance(payload, dict) and isinstance(payload.get("events"), list):
        payload = payload["events"]
    if not isinstance(payload, list):
        raise ValueError("events JSON must be a list or an object containing events")
    return [item for item in payload if isinstance(item, dict)]


if __name__ == "__main__":
    raise SystemExit(main())
