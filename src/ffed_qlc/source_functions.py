"""Source-backed math function registry for the Penrose QLC workbench.

The URLs are provenance metadata. The executable contract is the compiled
function profile: stable source id, math role, symbol contract, and rule map.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from importlib import resources
from typing import Any, Iterable, Mapping
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit


SOURCE_FUNCTION_SCHEMA = "ffed.qlc.source_function_profiles.v1"
SOURCE_FUNCTION_GRAPH_SCHEMA = "ffed.qlc.source_function_graph.v1"
REQUIRED_SOURCE_IDS = tuple(f"S{index:02d}" for index in range(1, 11))

_PROFILE_RESOURCE = "data/source_function_profiles.json"

_REQUIRED_FUNCTION_BY_SOURCE_ID = {
    "S01": "f_plithogenic_admission",
    "S02": "f_row_matrix_edge",
    "S03": "f_connector",
    "S04": "f_prevalence_resolve",
    "S05": "f_inf_sup_gate",
    "S06": "f_graph_state_carrier",
    "S07": "f_walk_dispersion",
    "S08": "f_multihyperedge_operation",
    "S09": "f_fusion_order",
    "S10": "f_cut_project_accept",
}


class SourceFunctionError(ValueError):
    """Raised when source-function provenance cannot compile safely."""


@dataclass(frozen=True)
class FunctionContract:
    """Symbol-level contract compiled from a source profile."""

    name: str
    input_symbols: tuple[str, ...]
    output_symbols: tuple[str, ...]
    operation: str
    rule_map: tuple[str, ...]

    @classmethod
    def from_mapping(cls, raw_contract: Mapping[str, Any]) -> "FunctionContract":
        name = _require_non_empty_string(raw_contract, "name")
        operation = _require_non_empty_string(raw_contract, "operation")
        input_symbols = _require_string_tuple(raw_contract, "input_symbols")
        output_symbols = _require_string_tuple(raw_contract, "output_symbols")
        rule_map = _require_string_tuple(raw_contract, "rule_map")

        if not input_symbols:
            raise SourceFunctionError(f"{name} requires input_symbols")
        if not output_symbols:
            raise SourceFunctionError(f"{name} requires output_symbols")
        if not rule_map:
            raise SourceFunctionError(f"{name} requires rule_map")

        return cls(
            name=name,
            input_symbols=input_symbols,
            output_symbols=output_symbols,
            operation=operation,
            rule_map=rule_map,
        )


@dataclass(frozen=True)
class SourceFunctionProfile:
    """A source compiled into a deterministic math-function profile."""

    source_id: str
    title: str
    url: str
    normalized_url: str
    source_fingerprint: str
    lane: str
    trust_tier: str
    source_role: str
    source_weight: float
    function: FunctionContract
    maps_to: tuple[str, ...]
    raw_body_stored: bool
    ui_visibility: str


def load_source_function_payload() -> dict[str, Any]:
    """Load the canonical ten-source function profile payload."""

    resource = resources.files("ffed_qlc").joinpath(_PROFILE_RESOURCE)
    return json.loads(resource.read_text(encoding="utf-8"))


def compile_source_function_profiles(
    payload: Mapping[str, Any] | None = None,
) -> tuple[SourceFunctionProfile, ...]:
    """Compile and validate the ten source profiles.

    The result is sorted by stable source id and is safe to use as a math
    registry. Raw source bodies are never accepted here.
    """

    raw_payload = load_source_function_payload() if payload is None else payload
    raw_profiles = _validate_payload(raw_payload)

    profiles: list[SourceFunctionProfile] = []
    seen_normalized_urls: dict[str, str] = {}
    seen_ids: set[str] = set()

    for raw_profile in raw_profiles:
        profile = _compile_profile(raw_profile)
        if profile.source_id in seen_ids:
            raise SourceFunctionError(f"duplicate source id: {profile.source_id}")

        previous_source_id = seen_normalized_urls.get(profile.normalized_url)
        if previous_source_id is not None:
            raise SourceFunctionError(
                "duplicate normalized URL: "
                f"{previous_source_id} and {profile.source_id}"
            )

        seen_ids.add(profile.source_id)
        seen_normalized_urls[profile.normalized_url] = profile.source_id
        profiles.append(profile)

    actual_source_ids = tuple(sorted(seen_ids))
    if actual_source_ids != REQUIRED_SOURCE_IDS:
        missing = sorted(set(REQUIRED_SOURCE_IDS) - seen_ids)
        extra = sorted(seen_ids - set(REQUIRED_SOURCE_IDS))
        raise SourceFunctionError(
            f"source profile ids must be S01..S10; missing={missing}; extra={extra}"
        )

    return tuple(sorted(profiles, key=lambda profile: profile.source_id))


def source_function_index(
    profiles: Iterable[SourceFunctionProfile] | None = None,
) -> dict[str, SourceFunctionProfile]:
    """Return source profiles indexed by stable source id."""

    compiled = compile_source_function_profiles() if profiles is None else tuple(profiles)
    return {profile.source_id: profile for profile in compiled}


def require_source_function_ids(
    source_ids: Iterable[str],
    profiles: Iterable[SourceFunctionProfile] | None = None,
) -> tuple[SourceFunctionProfile, ...]:
    """Resolve source ids or fail closed when a required profile is missing."""

    index = source_function_index(profiles)
    requested_ids = tuple(source_ids)
    missing = [source_id for source_id in requested_ids if source_id not in index]
    if missing:
        raise SourceFunctionError(f"missing source function profile: {missing}")
    return tuple(index[source_id] for source_id in requested_ids)


def require_all_source_function_profiles(
    profiles: Iterable[SourceFunctionProfile] | None = None,
) -> tuple[SourceFunctionProfile, ...]:
    """Resolve the mandatory ten-source registry or fail closed."""

    return require_source_function_ids(REQUIRED_SOURCE_IDS, profiles)


def build_source_function_graph(
    profiles: Iterable[SourceFunctionProfile] | None = None,
    *,
    include_urls: bool = False,
) -> dict[str, Any]:
    """Build the secondary provenance graph for the source functions.

    Raw URLs are hidden by default so UI and exports can show provenance
    fingerprints without turning the source graph into the math engine itself.
    """

    compiled = require_all_source_function_profiles(profiles)
    nodes: list[dict[str, Any]] = []
    edges: list[dict[str, Any]] = []
    function_names: set[str] = set()
    target_names: set[str] = set()

    for profile in compiled:
        source_node = {
            "id": f"source:{profile.source_id}",
            "kind": "source_function",
            "source_id": profile.source_id,
            "title": profile.title,
            "lane": profile.lane,
            "trust_tier": profile.trust_tier,
            "source_role": profile.source_role,
            "source_weight": profile.source_weight,
            "function_name": profile.function.name,
            "url_fingerprint": profile.source_fingerprint,
            "raw_body_stored": profile.raw_body_stored,
            "ui_visibility": profile.ui_visibility,
        }
        if include_urls:
            source_node["url"] = profile.url
            source_node["normalized_url"] = profile.normalized_url
        nodes.append(source_node)

        function_node_id = f"function:{profile.function.name}"
        if profile.function.name not in function_names:
            function_names.add(profile.function.name)
            nodes.append(
                {
                    "id": function_node_id,
                    "kind": "math_function",
                    "name": profile.function.name,
                    "input_symbols": list(profile.function.input_symbols),
                    "output_symbols": list(profile.function.output_symbols),
                    "operation": profile.function.operation,
                    "rule_map": list(profile.function.rule_map),
                }
            )

        edges.append(
            {
                "from": source_node["id"],
                "to": function_node_id,
                "relation": "defines_math_function",
                "weight": profile.source_weight,
            }
        )

        for target_name in profile.maps_to:
            target_node_id = f"target:{target_name}"
            if target_name not in target_names:
                target_names.add(target_name)
                nodes.append(
                    {
                        "id": target_node_id,
                        "kind": "math_target",
                        "name": target_name,
                    }
                )
            edges.append(
                {
                    "from": function_node_id,
                    "to": target_node_id,
                    "relation": "maps_to",
                    "source_id": profile.source_id,
                }
            )

    return {
        "schema": SOURCE_FUNCTION_GRAPH_SCHEMA,
        "graph_role": "secondary_provenance_not_lattice_engine",
        "raw_urls_included": include_urls,
        "required_source_ids": list(REQUIRED_SOURCE_IDS),
        "nodes": nodes,
        "edges": edges,
    }


def _validate_payload(payload: Mapping[str, Any]) -> list[Mapping[str, Any]]:
    if not isinstance(payload, Mapping):
        raise SourceFunctionError("source function payload must be a mapping")

    schema = payload.get("schema")
    if schema != SOURCE_FUNCTION_SCHEMA:
        raise SourceFunctionError(
            f"source function schema must be {SOURCE_FUNCTION_SCHEMA}"
        )

    raw_profiles = payload.get("profiles")
    if not isinstance(raw_profiles, list):
        raise SourceFunctionError("source function payload requires profiles list")
    if len(raw_profiles) != len(REQUIRED_SOURCE_IDS):
        raise SourceFunctionError("source function payload requires exactly 10 profiles")
    if not all(isinstance(raw_profile, Mapping) for raw_profile in raw_profiles):
        raise SourceFunctionError("each source function profile must be a mapping")

    return raw_profiles


def _compile_profile(raw_profile: Mapping[str, Any]) -> SourceFunctionProfile:
    source_id = _require_non_empty_string(raw_profile, "source_id")
    title = _require_non_empty_string(raw_profile, "title")
    url = _require_non_empty_string(raw_profile, "url")
    lane = _require_non_empty_string(raw_profile, "lane")
    trust_tier = _require_non_empty_string(raw_profile, "trust_tier")
    source_role = _require_non_empty_string(raw_profile, "source_role")
    maps_to = _require_string_tuple(raw_profile, "maps_to")
    ui_visibility = _require_non_empty_string(raw_profile, "ui_visibility")

    if source_id not in REQUIRED_SOURCE_IDS:
        raise SourceFunctionError(f"unsupported source id: {source_id}")
    if "ui" in source_role.casefold():
        raise SourceFunctionError(f"{source_id} source_role must be math, not UI")
    if not maps_to:
        raise SourceFunctionError(f"{source_id} requires maps_to targets")
    if raw_profile.get("raw_body_stored") is not False:
        raise SourceFunctionError(f"{source_id} cannot store raw source bodies")
    if ui_visibility != "metadata_only":
        raise SourceFunctionError(f"{source_id} UI visibility must be metadata_only")

    source_weight = raw_profile.get("source_weight")
    if not isinstance(source_weight, (int, float)) or isinstance(source_weight, bool):
        raise SourceFunctionError(f"{source_id} source_weight must be numeric")
    if source_weight < 0 or source_weight > 1:
        raise SourceFunctionError(f"{source_id} source_weight must be in [0, 1]")

    raw_contract = raw_profile.get("function")
    if not isinstance(raw_contract, Mapping):
        raise SourceFunctionError(f"{source_id} requires function contract")
    function = FunctionContract.from_mapping(raw_contract)

    required_function = _REQUIRED_FUNCTION_BY_SOURCE_ID[source_id]
    if function.name != required_function:
        raise SourceFunctionError(
            f"{source_id} function must be {required_function}, got {function.name}"
        )

    normalized_url = _normalize_url(url)
    return SourceFunctionProfile(
        source_id=source_id,
        title=title,
        url=url,
        normalized_url=normalized_url,
        source_fingerprint=_fingerprint(normalized_url),
        lane=lane,
        trust_tier=trust_tier,
        source_role=source_role,
        source_weight=float(source_weight),
        function=function,
        maps_to=maps_to,
        raw_body_stored=False,
        ui_visibility=ui_visibility,
    )


def _normalize_url(raw_url: str) -> str:
    parsed = urlsplit(raw_url.strip())
    scheme = parsed.scheme.casefold()
    netloc = parsed.netloc.casefold()
    if scheme not in {"http", "https"} or not netloc:
        raise SourceFunctionError(f"unsupported source URL: {raw_url!r}")

    path = parsed.path or "/"
    if path != "/":
        path = path.rstrip("/")

    query_pairs = parse_qsl(parsed.query, keep_blank_values=True)
    query = urlencode(sorted(query_pairs), doseq=True)
    return urlunsplit((scheme, netloc, path, query, ""))


def _fingerprint(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _require_non_empty_string(raw_mapping: Mapping[str, Any], key: str) -> str:
    value = raw_mapping.get(key)
    if not isinstance(value, str) or not value.strip():
        raise SourceFunctionError(f"{key} must be a non-empty string")
    return value.strip()


def _require_string_tuple(raw_mapping: Mapping[str, Any], key: str) -> tuple[str, ...]:
    value = raw_mapping.get(key)
    if not isinstance(value, list):
        raise SourceFunctionError(f"{key} must be a list")
    if not all(isinstance(item, str) and item.strip() for item in value):
        raise SourceFunctionError(f"{key} must contain non-empty strings")
    return tuple(item.strip() for item in value)
