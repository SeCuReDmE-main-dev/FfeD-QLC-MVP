from __future__ import annotations

import os
import textwrap

from ffed_qlc import emit_dogstatsd_counter


def main() -> int:
    if not os.environ.get("E2B_API_KEY"):
        raise SystemExit("E2B_API_KEY is required in the environment.")

    try:
        from e2b import Sandbox
    except ImportError as exc:
        raise SystemExit("Install with: pip install -e .[e2b]") from exc

    commands = [
        "python --version",
        "cat > /tmp/ffed_qlc_gate.py <<'PY'\n"
        "def gate(has_provenance, trust_score, claim_scope='bounded_software'):\n"
        "    if claim_scope in {'biological_proof', 'clinical_claim', 'security_certification'}:\n"
        "        return 'reject'\n"
        "    if not has_provenance:\n"
        "        return 'suspend'\n"
        "    if trust_score >= 0.75:\n"
        "        return 'accept'\n"
        "    if trust_score >= 0.40:\n"
        "        return 'suspend'\n"
        "    return 'reject'\n"
        "print(gate(True, 0.9))\n"
        "print(gate(True, 1.0, 'biological_proof'))\n"
        "PY\n"
        "python /tmp/ffed_qlc_gate.py",
    ]

    exit_code = 0
    with Sandbox.create() as sandbox:
        for command in commands:
            result = sandbox.commands.run(command)
            print(f"$ {command.splitlines()[0]}")
            if result.stdout:
                print(result.stdout.strip())
            if result.stderr:
                print(result.stderr.strip())
            exit_code = getattr(result, "exit_code", 0) or 0
            if exit_code != 0:
                break

    emit_dogstatsd_counter(
        "ffed_qlc.e2b.mvp_run",
        1,
        (
            "service:ffed-qlc-mvp",
            f"result:{'success' if exit_code == 0 else 'failure'}",
            "source:e2b",
        ),
    )

    if exit_code != 0:
        return exit_code

    print(
        textwrap.dedent(
            """
            E2B MVP run completed.
            Datadog sponsor tag suggestion:
            service:ffed-qlc-mvp source:e2b result:success
            """
        ).strip()
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
