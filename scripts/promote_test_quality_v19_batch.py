"""Verify a scoped Test Quality v1.9 batch and create candidate promotion evidence."""
import hashlib
import json
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BATCH_ID = "BATCH-20260815T032250.193794Z"
TARGETS = ("EMS-CTRL-027", "EMS-CTRL-028", "EMS-CTRL-029", "EMS-CTRL-031")
RUN = ROOT / "generated/wave2d/batch/runs" / BATCH_ID
SUMMARY = RUN / "hayes_batch_summary.json"
OUT = ROOT / "generated/wave2d/evaluator-expansion"
VERIFY = OUT / "test-quality-v19-verification/verification_manifest.json"
DRAFT = ROOT / "registry/wave2d_evaluator_registry_v1_9_draft.json"
REGISTRY = ROOT / "registry/wave2d_evaluator_registry_v1_9.json"
CERTIFICATION = OUT / "test_quality_registry_v1_9_certification.json"
EMS_REQUIREMENTS = Path("C:/temp/standars/ems/registry/test_quality_control_requirements.json")
EMS_CERTIFICATION = Path("C:/temp/standars/ems/registry/test_quality_publication_certification.json")


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    summary = json.loads(SUMMARY.read_text(encoding="utf-8"))
    rows = [row for row in summary["rows"] if row.get("control_id") in TARGETS]
    controls = []
    for control_id in TARGETS:
        target_rows = [row for row in rows if row["control_id"] == control_id]
        blocked = [row for row in target_rows if row["execution_state"] != "COMPLETE"]
        terminal = Counter(row.get("result_state", "BLOCKED") for row in target_rows)
        if not target_rows or blocked:
            raise SystemExit(f"scoped execution incomplete for {control_id}")
        controls.append({"control_id": control_id, "applicable_target_count": len(target_rows), "complete_target_count": len(target_rows), "blocked_target_count": 0, "terminal_result_counts": dict(terminal), "batch_id": BATCH_ID, "verification_state": "VERIFIED"})
    for control_id in ("EMS-CTRL-029", "EMS-CTRL-031"):
        if any(row.get("result_state") == "PASS" for row in rows if row["control_id"] == control_id):
            raise SystemExit(f"hard evidence-authority invariant failed for {control_id}")
    manifest = {"component": "Hayes Verify", "phase": "Wave 2D Test Quality v1.9 Immutable Verification", "batch_id": BATCH_ID, "controls": controls, "verified_control_count": 4, "pending_control_count": 0, "scoped_result_counts": dict(Counter(row.get("result_state", "BLOCKED") for row in rows)), "hard_invariants": {"ctrl029_repository_only_evidence_never_passes": "PASS", "ctrl031_repository_artifact_only_never_passes": "PASS"}}
    write(VERIFY, manifest)
    registry = json.loads(DRAFT.read_text(encoding="utf-8"))
    registry["registry_version"] = "1.9"
    registry["registry_state"] = "CANDIDATE_FROZEN"
    registry["status"] = "CANDIDATE_FROZEN"
    registry["verification_batch_id"] = BATCH_ID
    for control_id in TARGETS:
        registry["controls"][control_id]["implementation_state"] = "IMPLEMENTED"
        registry["controls"][control_id]["supported"] = True
    registry["implementation_state_counts"] = dict(sorted(Counter(item["implementation_state"] for item in registry["controls"].values()).items()))
    write(REGISTRY, registry)
    certification = {"component": "Hayes Verify", "phase": "Wave 2D Test Quality v1.9 Candidate Registry Promotion", "certified_at_utc": datetime.now(UTC).isoformat(), "status": "PASS", "registry_state": "CANDIDATE_FROZEN", "registry_version": "1.9", "verification_batch_id": BATCH_ID, "promoted_control_count": 4, "promoted_controls": list(TARGETS), "registry_sha256": sha(REGISTRY), "verification_sha256": sha(VERIFY), "implementation_state_counts": registry["implementation_state_counts"], "ems_requirements_sha256": sha(EMS_REQUIREMENTS), "ems_publication_certification_sha256": sha(EMS_CERTIFICATION), "errors": []}
    write(CERTIFICATION, certification)
    print(json.dumps({"status": "PASS", "verified_control_count": 4, "registry": str(REGISTRY), "certification": str(CERTIFICATION)}, indent=2))


if __name__ == "__main__":
    main()