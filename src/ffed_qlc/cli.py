from __future__ import annotations

import argparse
import json

from .admissibility import Evidence, evaluate_evidence
from .docker_map import DEFAULT_STUDYCASE_BLOCKS


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

    return 2


if __name__ == "__main__":
    raise SystemExit(main())

