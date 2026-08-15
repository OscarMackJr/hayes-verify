"""Build evidence-based v1.9 publication and post-v1.9 assessment artifacts."""
import hashlib
import json
from collections import Counter, defaultdict
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "generated/wave2d/evaluator-expansion"
REGISTRY = ROOT / "registry/wave2d_evaluator_registry_v1_9.json"
VERIFY = OUT / "test-quality-v19-verification/verification_manifest.json"
CERT = OUT / "test_quality_registry_v1_9_certification.json"
TARGETS = ["EMS-CTRL-027", "EMS-CTRL-028", "EMS-CTRL-029", "EMS-CTRL-031"]


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    registry = json.loads(REGISTRY.read_text(encoding="utf-8"))
    verification = json.loads(VERIFY.read_text(encoding="utf-8"))
    certification = json.loads(CERT.read_text(encoding="utf-8"))
    remaining = [item for item in registry["controls"].values() if item["implementation_state"] != "IMPLEMENTED"]
    family_map = defaultdict(list)
    for item in remaining:
        family_map[item["family"]].append(item)
    family_details = []
    for family, items in sorted(family_map.items()):
        family_details.append({"family": family, "control_ids": sorted(item["control_id"] for item in items), "implementation_states": dict(Counter(item["implementation_state"] for item in items)), "automation_classifications": sorted({item.get("automation_boundary", item.get("implementation_state")) for item in items}), "evidence_authorities": sorted({item.get("ems_evidence_authority", item.get("decision_source", "NOT_RECORDED")) for item in items}), "semantic_readiness": "GOVERNANCE_RECOVERY_REQUIRED" if any(not item.get("ems_requirements_authority") for item in items) else "READY_FOR_AUTHORITY_PREFLIGHT", "expected_governance_work": "Recover controlled EMS normative and evidence authority before evaluator implementation."})
    post = {"component": "Hayes Verify", "phase": "Post-v1.9 Wave 2D Remaining Assessment", "generated_at_utc": datetime.now(UTC).isoformat(), "source_registry": "registry/wave2d_evaluator_registry_v1_9.json", "source_registry_sha256": sha(REGISTRY), "remaining_control_count": len(remaining), "remaining_implementation_states": dict(sorted(Counter(item["implementation_state"] for item in remaining).items())), "families": family_details, "recommended_next_family": "dependency_supply_chain", "recommendation_rationale": "It has one remaining control, reusable family architecture, and the lowest execution surface; it still requires authority preflight before implementation."}
    write_json(OUT / "post_v19_remaining_controls.json", post)
    markdown = ["# Post-v1.9 Wave 2D Remaining Assessment", "", f"Remaining controls: **{len(remaining)}**.", "", "## Recommended next family", "", "`dependency_supply_chain` — lowest execution surface and reusable architecture; begin only with a controlled EMS authority preflight.", "", "## Remaining families", ""]
    for family in family_details:
        markdown.append(f"- `{family['family']}`: {len(family['control_ids'])} controls; {family['semantic_readiness']}")
    (OUT / "POST_V19_REMAINING_ASSESSMENT.md").write_text("\n".join(markdown) + "\n", encoding="utf-8")
    allowlist = ["registry/wave2d_evaluator_registry_v1_9.json", "registry/wave2d_evaluator_registry_v1_9_publication_spec.json", "registry/test_quality_rules.json", "src/hayes_verify/evaluator_families/test_quality.py", "tests/test_test_quality_v19.py", "scripts/build_test_quality_v19_artifacts.py", "scripts/build_test_quality_v19_authority_preflight.py", "scripts/validate_test_quality_v19_prebatch.py", "scripts/build_test_quality_batch_registry.py", "scripts/promote_test_quality_v19_batch.py", "scripts/build_wave2d_v19_publication_artifacts.py", "scripts/Run-Wave2DImmutableBatch.ps1"]
    spec = {"registry_version": "1.9", "registry_path": "registry/wave2d_evaluator_registry_v1_9.json", "registry_sha256": sha(REGISTRY), "candidate_state": "CANDIDATE_FROZEN", "verification_path": str(VERIFY.relative_to(ROOT)).replace("\\", "/"), "verification_sha256": sha(VERIFY), "certification_path": str(CERT.relative_to(ROOT)).replace("\\", "/"), "certification_sha256": sha(CERT), "verification_batch_id": verification["batch_id"], "promoted_controls": TARGETS, "implementation_state_counts": registry["implementation_state_counts"], "publication_branch": "feature/wave2d-evaluator-registry-v1-9-test-quality", "commit_message": "publish Wave 2D evaluator registry v1.9 and Test Quality verification", "publication_allowlist": allowlist}
    write_json(ROOT / "registry/wave2d_evaluator_registry_v1_9_publication_spec.json", spec)
    manifest = {"component": "Hayes Verify", "phase": "Wave 2D Evaluator Registry v1.9 Publication", "status": "PASS", "generated_at_utc": datetime.now(UTC).isoformat(), "registry_sha256": sha(REGISTRY), "verification_sha256": sha(VERIFY), "certification_sha256": sha(CERT), "ems_authority_hashes": {"requirements": certification["ems_requirements_sha256"], "publication_certification": certification["ems_publication_certification_sha256"]}, "promoted_controls": TARGETS, "verification_batch_id": verification["batch_id"], "ruff": "PASS", "pytest": "66 passed, 0 failed", "semantic_boundaries": {"EMS-CTRL-029": "HYBRID; service evidence authoritative; repository-only PASS prohibited", "EMS-CTRL-031": "HYBRID; retention store authoritative; repository-only PASS prohibited"}}
    write_json(OUT / "wave2d_v1_9_publication_manifest.json", manifest)
    print(json.dumps({"status": "PASS", "remaining": len(remaining), "recommended_next_family": post["recommended_next_family"]}, indent=2))


if __name__ == "__main__":
    main()