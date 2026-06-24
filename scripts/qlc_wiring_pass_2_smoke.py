from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_BUNDLE = ROOT / "tests" / "fixtures" / "qlc_contract" / "qlc_workflow_image.json"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Second-pass QLC wiring smoke runner.")
    parser.add_argument("--bundle", default=str(DEFAULT_BUNDLE))
    parser.add_argument("--simulator-url", default="http://localhost:8000")
    parser.add_argument("--real-submit", action="store_true")
    args = parser.parse_args(argv)

    bundle = Path(args.bundle)
    inspect_cmd = [sys.executable, "-m", "ffed_qlc.cli", "inspect-workflow", "--bundle", str(bundle)]
    gateway_cmd = [
        "fnpqnn",
        "--json",
        "gateway",
        "qlc-submit",
        "--bundle",
        str(bundle),
        "--simulator-url",
        args.simulator_url,
    ]
    if not args.real_submit:
        gateway_cmd.append("--dry-run")

    inspect_run = subprocess.run(inspect_cmd, check=False, capture_output=True, text=True)
    if inspect_run.returncode != 0:
        print(json.dumps({"success": False, "stage": "inspect", "stderr": inspect_run.stderr[-400:]}, indent=2))
        return inspect_run.returncode

    gateway_run = subprocess.run(gateway_cmd, check=False, capture_output=True, text=True)
    if gateway_run.returncode != 0:
        print(json.dumps({"success": False, "stage": "gateway", "stderr": gateway_run.stderr[-400:]}, indent=2))
        return gateway_run.returncode

    print(
        json.dumps(
            {
                "success": True,
                "bundle": str(bundle),
                "inspect": json.loads(inspect_run.stdout),
                "gateway": json.loads(gateway_run.stdout),
                "raw_payload_embedded": False,
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
