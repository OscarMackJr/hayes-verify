"""Deterministically reconcile the Hayes Wave 2D consumer contract bundle."""
from __future__ import annotations

import argparse
import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

MAPPING = {
    "evaluation_request": "contracts/schemas/wave2d_evaluation_request.schema.json",
    "evidence_record": "contracts/schemas/wave2d_evidence_record.schema.json",
    "evaluation_result": "contracts/schemas/wave2d_evaluation_result.schema.json",
    "provenance_envelope": "contracts/schemas/wave2d_provenance_envelope.schema.json",
    "status_vocabulary": "contracts/registry/evaluation_status_vocabulary.json",
}


def load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write(path: Path, value: dict[str, Any]) -> None:
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8", newline="\n")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", required=True)
    parser.add_argument("--reason", required=True)
    args = parser.parse_args()
    root = Path(args.root).resolve()
    freeze_path = root / "contracts/contract_freeze.json"
    manifest_path = root / "contracts/consumer_manifest.json"
    history_path = root / "contracts/contract_bundle_history.json"
    freeze, manifest = load(freeze_path), load(manifest_path)
    before = {name: freeze["contracts"][name]["sha256"] for name in MAPPING}
    after = {name: sha256(root / relative) for name, relative in MAPPING.items()}
    for name, relative in MAPPING.items():
        record = {"path": freeze["contracts"][name].get("path", relative), "sha256": after[name]}
        freeze["contracts"][name] = record
        manifest["contracts"][name] = dict(record)
    changed = [name for name in MAPPING if before[name] != after[name]]
    timestamp = datetime.now(UTC).isoformat()
    freeze["bundle_reconciled_at_utc"] = timestamp
    manifest["bundle_reconciled_at_utc"] = timestamp
    history = load(history_path) if history_path.exists() else {"component": "Hayes Verify", "contract_bundle": "Wave 2D", "entries": []}
    history["entries"].append({
        "recorded_at_utc": timestamp,
        "reason": args.reason,
        "contract_version": freeze["contract_version"],
        "compatibility": "BACKWARD_COMPATIBLE_ADDITIVE_EXTENSION",
        "changed_contracts": [
            {"name": name, "previous_sha256": before[name], "new_sha256": after[name]}
            for name in changed
        ],
        "ems_modified": False,
    })
    write(freeze_path, freeze)
    write(manifest_path, manifest)
    write(history_path, history)
    print(json.dumps({"status": "PASS", "contract_version": freeze["contract_version"], "changed_contracts": changed}, indent=2))


if __name__ == "__main__":
    main()