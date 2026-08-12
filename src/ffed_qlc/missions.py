"""Deterministic, allowlisted mission engine for synthetic defensive exercises."""

from __future__ import annotations

import uuid
from typing import Any, Callable

from .contracts import payload_sha256, utc_now
from .curriculum import TENEBRIS_BUDGETS, laboratory_catalog, synthetic_fixture_bytes
from .geometry_trace import build_apollonian_trace
from .storage import AlphaStore
from .structural_transform import (
    MAX_HEADER_BYTES,
    MAX_PLAINTEXT_BYTES,
    QLCTransformError,
    inspect_container,
    pack_bytes,
    quasicrystal_coordinates,
    unpack_bytes,
)


LAB_INDEX = {lab["lab_id"]: lab for lab in laboratory_catalog()}
ActionHandler = Callable[[dict[str, Any], bytes], dict[str, Any]]


class MissionError(ValueError):
    pass


class MissionEngine:
    def __init__(self, store: AlphaStore) -> None:
        self.store = store
        self._actions: dict[str, ActionHandler] = {
            "inspect_primitives": self._inspect_primitives,
            "inspect_fqlc1": self._inspect_fqlc1,
            "classify_metadata": self._classify_metadata,
            "compare_permutation": self._compare_permutation,
            "trace_apollonian": self._trace_apollonian,
            "run_bounded_attack": self._run_bounded_attack,
            "apply_defense": self._apply_defense,
            "request_handoff": self._request_handoff,
            "export_portfolio": self._export_portfolio,
        }

    def start(self, project_id: str, lab_id: str) -> dict[str, Any]:
        if lab_id not in LAB_INDEX:
            raise MissionError("unknown laboratory")
        now = utc_now()
        run = {
            "schema": "ffed.qlc.mission_run.v1",
            "run_id": f"run-{uuid.uuid4().hex[:16]}",
            "project_id": project_id,
            "lab_id": lab_id,
            "state": "active",
            "attempt_count": 0,
            "created_at": now,
            "updated_at": now,
        }
        return self.store.save_run(run)

    def execute(
        self,
        run_id: str,
        action: str,
        fixture_id: str | None = None,
        idempotency_key: str | None = None,
    ) -> dict[str, Any]:
        run = self.store.get_run(run_id)
        lab = LAB_INDEX[run["lab_id"]]
        if run["state"] not in {"active", "suspended"}:
            raise MissionError("mission is not executable")
        if action != lab["allowed_action"]:
            raise MissionError("action is outside the laboratory allowlist")
        budgets = self.store.get_budget_profile(run["project_id"], TENEBRIS_BUDGETS)
        attempts = int(run["attempt_count"]) + 1
        if attempts > budgets["retry_count"]:
            run.update({"state": "suspended", "attempt_count": attempts, "updated_at": utc_now()})
            self.store.save_run(run)
            raise MissionError("Tenebris retry budget exceeded")
        if idempotency_key:
            claimed = self.store.claim_idempotency_key(
                idempotency_key,
                f"mission:{run_id}:{action}",
                payload_sha256({"run_id": run_id, "action": action, "fixture_id": fixture_id}),
            )
            if not claimed:
                return {"run": run, "idempotent_replay": True}
        evidence = self._evidence(run, lab, action, fixture_id, budgets)
        artifact = self.store.save_artifact(evidence)
        run.update({
            "state": "evidence_ready",
            "attempt_count": attempts,
            "evidence_ref": artifact["sha256"],
            "updated_at": utc_now(),
        })
        self.store.save_run(run)
        return {"run": run, "evidence": evidence, "artifact": artifact}

    def _evidence(
        self,
        run: dict[str, Any],
        lab: dict[str, Any],
        action: str,
        fixture_id: str | None,
        budgets: dict[str, int],
    ) -> dict[str, Any]:
        selected_fixture = fixture_id or "synthetic-env-basic"
        fixture = synthetic_fixture_bytes(selected_fixture)
        if len(fixture) > budgets["fixture_bytes"]:
            raise MissionError("fixture exceeds the project Tenebris budget")
        proof = self._execute_action(run, action, fixture)
        payload = {
            "schema": "ffed.qlc.mission_evidence.v1",
            "lab_id": lab["lab_id"],
            "action": action,
            "fixture_id": selected_fixture,
            "observation": proof.pop("observation"),
            "mechanism": proof.pop("mechanism"),
            "attack": proof.pop("attack", "none"),
            "proof": proof,
            "limitation": "No real target, credential, or production security claim was evaluated.",
            "tenebris_budgets": budgets,
            "external_network_used": False,
            "arbitrary_shell_used": False,
            "raw_secret_stored": False,
        }
        payload["sha256"] = payload_sha256(payload)
        return payload

    def _execute_action(self, run: dict[str, Any], action: str, fixture: bytes) -> dict[str, Any]:
        handler = self._actions.get(action)
        if handler is None:
            raise MissionError("action has no deterministic implementation")
        return handler(run, fixture)

    @staticmethod
    def _inspect_primitives(run: dict[str, Any], fixture: bytes) -> dict[str, Any]:
        del run, fixture
        return {
                "observation": "The alpha separates key derivation, authenticated encryption, and structural permutation.",
                "mechanism": "scrypt_then_chacha20poly1305_with_observable_permutation",
                "profiles": {"kdf": "scrypt-16384-8-1", "aead": "ChaCha20-Poly1305", "geometry_key_material": False},
            }

    @staticmethod
    def _inspect_fqlc1(run: dict[str, Any], fixture: bytes) -> dict[str, Any]:
        del run
        manifest = inspect_container(pack_bytes(fixture, "educational-fixture-only"))
        return {
                "observation": "The public FQLC1 header can be inspected without returning fixture bytes.",
                "mechanism": "authenticated_container_public_header",
                "manifest": manifest,
            }

    @staticmethod
    def _classify_metadata(run: dict[str, Any], fixture: bytes) -> dict[str, Any]:
        del run
        manifest = inspect_container(pack_bytes(fixture, "educational-fixture-only"))
        return {
                "observation": "Length and deterministic source fingerprints are visible metadata and must be treated as disclosure.",
                "mechanism": "public_header_leak_surface_review",
                "visible_fields": ["container_size_bytes", "plaintext_length", "container_sha256", "qlc_manifest.source_sha256"],
                "plaintext_exposed": manifest["raw_payload_exposed"],
            }
    @staticmethod
    def _compare_permutation(run: dict[str, Any], fixture: bytes) -> dict[str, Any]:
        del run
        coordinates = quasicrystal_coordinates(min(len(fixture), 64), "educational-fixture-only")
        return {
                "observation": "The geometric ordering changes byte positions but contributes no independent secrecy claim.",
                "mechanism": "phi_cut_project_permutation_v1",
                "coordinate_count": len(coordinates),
                "first_coordinates": [list(item) for item in coordinates[:8]],
                "is_key_material": False,
            }
    @staticmethod
    def _trace_apollonian(run: dict[str, Any], fixture: bytes) -> dict[str, Any]:
        del run, fixture
        return {
                "observation": "Exact integer reflections expose cycles and symmetry-equivalent states reproducibly.",
                "mechanism": "integral_descartes_reflection_bfs_v1",
                "geometry_trace": build_apollonian_trace(depth=2),
            }
    @staticmethod
    def _run_bounded_attack(run: dict[str, Any], fixture: bytes) -> dict[str, Any]:
        del run
        container = bytearray(pack_bytes(fixture, "educational-fixture-only"))
        container[-1] ^= 1
        rejected = False
        try:
            unpack_bytes(bytes(container), "educational-fixture-only")
        except QLCTransformError:
            rejected = True
        return {
                "observation": "A one-byte ciphertext mutation is rejected by authenticated decryption.",
                "mechanism": "chacha20poly1305_authentication_tag",
                "attack": "single_byte_ciphertext_mutation",
                "tampered_container_rejected": rejected,
            }
    @staticmethod
    def _apply_defense(run: dict[str, Any], fixture: bytes) -> dict[str, Any]:
        del run, fixture
        return {
                "observation": "The parser enforces fixed KDF parameters and bounded header, fixture, trace, and retry sizes.",
                "mechanism": "strict_parser_and_tenebris_resource_caps",
                "header_bytes_max": MAX_HEADER_BYTES,
                "plaintext_bytes_max": MAX_PLAINTEXT_BYTES,
                "retry_count_max": TENEBRIS_BUDGETS["retry_count"],
            }
    @staticmethod
    def _request_handoff(run: dict[str, Any], fixture: bytes) -> dict[str, Any]:
        del run, fixture
        return {
                "observation": "The mission requires a Gateway-mediated metric request rather than direct remote history access.",
                "mechanism": "credential_blind_bounded_handoff",
                "requested_metric_budget": 8,
                "full_history_requested": False,
                "handoff_status": "requires_explicit_target",
            }
    def _export_portfolio(self, run: dict[str, Any], fixture: bytes) -> dict[str, Any]:
        del fixture
        bundle = self.store.project_bundle(run["project_id"])
        return {
                "observation": "The capstone project can be represented by evidence references and human decisions.",
                "mechanism": "sha256_addressed_project_bundle",
                "mission_count": len(bundle["runs"]),
                "report_count": len(bundle["reports"]),
                "decision_count": len(bundle["decisions"]),
                "publication_approved": False,
            }
