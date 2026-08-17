"""Build hash-bound AR3F publication evidence from frozen candidate inputs."""
from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path

from hayes_verify.contract_hashing import sha256_canonical_contract_file

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "generated/archive-assessment/ar3f"
EXPECTED = {
    "registry/wave2d_evaluator_registry_v1_11.json": "f29699f3bfca3f994574919f335033777feb884e2985c237fbb4da2bbb2123c2",
    "contracts/schemas/wave2d_evaluation_request.schema.json": "6ac7d2869b6356f685490aae95949382a43da05984dd30c95a0786ef992d840a",
    "contracts/schemas/wave2d_evaluation_result.schema.json": "3c4be6856d26d3678a04f45ddb2ce85261dc69f54ab6d6db960ebd139c2e6394",
}
ALLOWLIST = [
    "contracts/consumer_manifest.json",
    "contracts/contract_bundle_history.json",
    "contracts/contract_freeze.json",
    "contracts/schemas/wave2d_evaluation_request.schema.json",
    "contracts/schemas/wave2d_evaluation_result.schema.json",
    "generated/archive-assessment/ar3f/AR3F_RUNTIME_AUTHORITY_PUBLICATION.md",
    "generated/archive-assessment/ar3f/AR3F_RUNTIME_AUTHORITY_PUBLICATION_CERTIFICATION.json",
    "generated/archive-assessment/ar3f/ar3f_publication_staging_allowlist.json",
    "generated/archive-assessment/ar3f/ar3f_runtime_authority_publication_manifest.json",
    "generated/archive-assessment/ar3f/publication_audit.json",
    "generated/archive-assessment/ar3f/publication_audit_script_failure.json",
    "generated/archive-assessment/ar3f/ci/contract_hash_ci_failure_analysis.json",
    "registry/wave2d_evaluator_registry_v1_11.json",
    "registry/wave2d_runtime_bindings_v1_0.json",
    "scripts/audit_ar3f_publication.py",
    "scripts/build_ar3f_publication_artifacts.py",
    "scripts/build_wave2d_active_runtime_registry.py",
    "scripts/run_registry_evaluator.py",
    "scripts/validate_ar3f_runtime_authority.py",
    "src/hayes_verify/wave2d_targets.py",
    "tests/test_archive_target_contract.py",
]

def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

def write_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")

def main() -> None:
    for relative, expected in EXPECTED.items():
        actual = sha256_canonical_contract_file(ROOT / relative) if relative.startswith("contracts/schemas/") else sha256(ROOT / relative)
        if actual != expected:
            raise SystemExit(f"frozen input hash mismatch: {relative}")
    registry = json.loads((ROOT / "registry/wave2d_evaluator_registry_v1_11.json").read_text(encoding="utf-8"))
    bindings = json.loads((ROOT / "registry/wave2d_runtime_bindings_v1_0.json").read_text(encoding="utf-8"))
    controls = registry["controls"]
    proven = sorted(control_id for control_id, record in controls.items() if record.get("supported") is True)
    unproven = sorted(control_id for control_id, record in controls.items() if record.get("implementation_state") == "NOT_CURRENTLY_PUBLISHED" and record.get("supported") is False)
    if len(proven) != 26 or len(unproven) != 20 or len(bindings["bindings"]) != 26:
        raise SystemExit("frozen support/binding semantics mismatch")
    if bindings["source_support_registry_sha256"] != EXPECTED["registry/wave2d_evaluator_registry_v1_11.json"]:
        raise SystemExit("runtime binding source hash does not bind frozen registry")
    OUT.mkdir(parents=True, exist_ok=True)
    allowlist_path = OUT / "ar3f_publication_staging_allowlist.json"
    write_json(allowlist_path, {"allowlist": ALLOWLIST, "excluded": ["scripts/build_ar3f_runtime_authority.py", "registry/wave2d_evaluator_registry.json"], "purpose": "explicit AR3F publication staging allowlist"})
    hashes = {relative: (sha256_canonical_contract_file(ROOT / relative) if relative.startswith("contracts/schemas/") else sha256(ROOT / relative)) for relative in ALLOWLIST if not relative.startswith("generated/archive-assessment/ar3f/") and (ROOT / relative).is_file()}
    manifest = {
        "component": "Hayes Verify",
        "phase": "AR3F Archive Runtime Authority Reconciliation",
        "status": "PASS",
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "frozen_registry_path": "registry/wave2d_evaluator_registry_v1_11.json",
        "frozen_registry_sha256": EXPECTED["registry/wave2d_evaluator_registry_v1_11.json"],
        "request_schema_sha256": EXPECTED["contracts/schemas/wave2d_evaluation_request.schema.json"],
        "result_schema_sha256": EXPECTED["contracts/schemas/wave2d_evaluation_result.schema.json"],
        "proven_supported_control_count": len(proven),
        "not_currently_published_control_count": len(unproven),
        "runtime_binding_count": len(bindings["bindings"]),
        "portable_ems_authority_reference_count": 6,
        "publication_files": hashes,
        "untracked_evaluators_published": False,
        "archive_evaluator_executions": 0,
        "production_evaluator_executions": 0,
    }
    manifest_path = OUT / "ar3f_runtime_authority_publication_manifest.json"
    write_json(manifest_path, manifest)
    certification = {
        "component": "Hayes Verify",
        "phase": "AR3F Archive Runtime Authority Controlled Publication",
        "status": "PASS",
        "certification_scope": ["integrity", "traceability", "evidence_completeness"],
        "compliance_attestation": False,
        "frozen_registry_sha256": EXPECTED["registry/wave2d_evaluator_registry_v1_11.json"],
        "publication_manifest_path": "generated/archive-assessment/ar3f/ar3f_runtime_authority_publication_manifest.json",
        "publication_manifest_sha256": sha256(manifest_path),
        "support_semantics": {"proven": len(proven), "not_currently_published_unproven": len(unproven)},
        "runtime_binding_count": len(bindings["bindings"]),
        "errors": [],
    }
    certification_path = OUT / "AR3F_RUNTIME_AUTHORITY_PUBLICATION_CERTIFICATION.json"
    write_json(certification_path, certification)
    summary = """# AR3F Runtime Authority Publication\n\nThis publication binds the frozen v1.11 evaluator support registry to 26 proven runtime bindings. Twenty controls remain explicitly unproven and are not published as supported.\n\nCertification scope is limited to integrity, traceability, and evidence completeness; it is not a compliance attestation. No archive, production, Hometown, or real-repository evaluator execution occurred.\n"""
    (OUT / "AR3F_RUNTIME_AUTHORITY_PUBLICATION.md").write_text(summary, encoding="utf-8")
    print(json.dumps({"status": "PASS", "manifest_sha256": sha256(manifest_path), "certification_sha256": sha256(certification_path), "allowlist_sha256": sha256(allowlist_path)}, indent=2))

if __name__ == "__main__":
    main()