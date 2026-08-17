"""Derive an immutable run-scoped runtime registry from controlled bindings."""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--authority", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--control-id", action="append", dest="control_ids")
    args = parser.parse_args()
    authority = json.loads(args.authority.read_text(encoding="utf-8"))
    requested = set(args.control_ids or [item["control_id"] for item in authority["bindings"]])
    selected = [item for item in authority["bindings"] if item["control_id"] in requested]
    if {item["control_id"] for item in selected} != requested:
        raise SystemExit("requested control has no controlled runtime binding")
    families: dict[str, dict] = {}
    for item in selected:
        family = families.setdefault(item["family_id"], {"implementation": item["module"], "controls": {}})
        family["controls"][item["control_id"]] = {
            "collector": item["collector"],
            "evaluator": item["evaluator"],
            "evidence_type": item["evidence_type"],
            "supported": True,
            "binding_id": item["binding_id"],
            "supported_target_types": item["supported_target_types"],
        }
    output = {
        "registry_type": "RUN_SCOPED_ACTIVE_RUNTIME_REGISTRY",
        "run_id": args.run_id,
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "derived_from_runtime_authority_version": authority["version"],
        "derived_from_runtime_authority_sha256": sha(args.authority),
        "families": families,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(output, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": "PASS", "binding_count": len(selected), "output": str(args.output)}, indent=2))


if __name__ == "__main__":
    main()
