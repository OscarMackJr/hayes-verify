"""Fail-closed validator for the AR3F support registry and runtime bindings."""
from __future__ import annotations

import argparse
import hashlib
import importlib
import json
from pathlib import Path

EXPECTED_REGISTRY_SHA256 = "f29699f3bfca3f994574919f335033777feb884e2985c237fbb4da2bbb2123c2"

def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    args = parser.parse_args()
    root = args.root.resolve()
    registry_path = root / "registry/wave2d_evaluator_registry_v1_11.json"
    binding_path = root / "registry/wave2d_runtime_bindings_v1_0.json"
    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    bindings = json.loads(binding_path.read_text(encoding="utf-8"))
    errors: list[str] = []
    registry_sha = sha256(registry_path)
    if registry_sha != EXPECTED_REGISTRY_SHA256:
        errors.append("frozen v1.11 registry SHA-256 mismatch")
    controls = registry.get("controls", {})
    supported = {control_id for control_id, record in controls.items() if record.get("supported") is True}
    unproven = {control_id for control_id, record in controls.items() if record.get("implementation_state") == "NOT_CURRENTLY_PUBLISHED" and record.get("supported") is False}
    if len(supported) != 26 or len(unproven) != 20:
        errors.append(f"support semantics expected 26/20, found {len(supported)}/{len(unproven)}")
    if bindings.get("source_support_registry_sha256") != registry_sha:
        errors.append("binding authority does not reference frozen v1.11 SHA-256")
    bound = set()
    for binding in bindings.get("bindings", []):
        control_id = binding.get("control_id")
        if not control_id or control_id in bound:
            errors.append(f"duplicate or missing binding control ID: {control_id}")
            continue
        bound.add(control_id)
        if control_id not in supported:
            errors.append(f"binding is not a supported proven control: {control_id}")
        module = importlib.import_module(binding["module"])
        if not callable(getattr(module, binding["evaluator"], None)):
            errors.append(f"binding evaluator is not callable: {control_id}")
        rule = root / binding["rule_registry"]
        if not rule.is_file():
            errors.append(f"missing rule registry: {control_id}")
    if bound != supported:
        errors.append("bindings do not match all and only supported proven controls")
    result = {"status": "PASS" if not errors else "FAIL", "registry_sha256": registry_sha, "proven_supported_count": len(supported), "unproven_not_currently_published_count": len(unproven), "runtime_binding_count": len(bound), "errors": errors}
    print(json.dumps(result, indent=2))
    if errors:
        raise SystemExit(1)

if __name__ == "__main__":
    main()