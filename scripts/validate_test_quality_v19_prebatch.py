"""Fail-closed pre-batch validation for Test Quality v1.9."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "generated" / "wave2d" / "evaluator-expansion"
EMS = Path(r"C:\temp\standars\ems")
TARGETS = {"EMS-CTRL-027": 4, "EMS-CTRL-028": 5, "EMS-CTRL-029": 6, "EMS-CTRL-031": 6}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> None:
    requirements = EMS / "registry" / "test_quality_control_requirements.json"
    certification = EMS / "registry" / "test_quality_publication_certification.json"
    rules_path = ROOT / "registry" / "test_quality_rules.json"
    matrix_path = OUT / "test_quality_v19_implementation_matrix.json"
    coverage_path = OUT / "test_quality_v19_family_coverage.json"
    draft_path = ROOT / "registry" / "wave2d_evaluator_registry_v1_9_draft.json"
    expected_hashes = {requirements: "08271a749f3fde6958ef57ef7c10480b7456f98a9f3f04fff4c0b328338bbf28", certification: "fb7f1c8739df41d1485390b9ada4ed6f7657ace453919cba63110bf1d06b622e"}
    errors = [f"hash mismatch: {path}" for path, expected in expected_hashes.items() if sha256(path) != expected]
    matrix = load(matrix_path); rules = load(rules_path); coverage = load(coverage_path); draft = load(draft_path)
    matrix_ids = [item["decision_id"] for item in matrix["assertions"]]
    rule_ids = [item["decision_id"] for control in TARGETS for item in rules["rules"][control]["assertions"]]
    expected = {f"TQ-{control.split('-')[-1]}-{number:02d}" for control, count in TARGETS.items() for number in range(1, count + 1)}
    if set(matrix_ids) != expected or len(matrix_ids) != 21: errors.append("matrix traceability invalid")
    if set(rule_ids) != expected or len(rule_ids) != 21: errors.append("rule traceability invalid")
    if coverage.get("selected_control_count") != 4 or coverage.get("implementable_count") != 4 or coverage.get("blocked_count") != 0: errors.append("coverage invalid")
    if draft.get("registry_version") != "1.9-draft" or draft.get("status") != "DRAFT": errors.append("draft identity invalid")
    for control in TARGETS:
        record = draft["controls"].get(control, {})
        if record.get("implementation_state") != "IMPLEMENTED_PENDING_BATCH_VERIFICATION" or record.get("supported") is not False: errors.append(f"draft target state invalid: {control}")
    if rules["rules"]["EMS-CTRL-029"].get("repository_only_pass_permitted") is not False: errors.append("CTRL-029 repository-only PASS not prohibited")
    if rules["rules"]["EMS-CTRL-031"].get("repository_only_pass_permitted") is not False: errors.append("CTRL-031 repository-only PASS not prohibited")
    result = {"status": "PASS" if not errors else "FAIL", "ems_requirements_sha256": sha256(requirements), "ems_certification_sha256": sha256(certification), "selected_controls": 4, "ems_decisions": 21, "matrix_decisions": len(matrix_ids), "rule_decisions": len(rule_ids), "missing_decision_ids": sorted(expected - set(matrix_ids) - set(rule_ids)), "orphaned_decision_ids": sorted((set(matrix_ids) | set(rule_ids)) - expected), "coverage": {"selected": coverage.get("selected_control_count"), "implementable": coverage.get("implementable_count"), "blocked": coverage.get("blocked_count")}, "draft_implementation_state_counts": draft.get("implementation_state_counts"), "critical_negative_invariants": {"ctrl029_repository_only_evidence_never_passes": "PASS" if not errors or "CTRL-029 repository-only PASS not prohibited" not in errors else "FAIL", "ctrl031_repository_artifact_only_never_passes": "PASS" if not errors or "CTRL-031 repository-only PASS not prohibited" not in errors else "FAIL"}, "errors": errors}
    output = OUT / "test_quality_v19_prebatch_validation.json"; output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    if errors: raise SystemExit(json.dumps(result, indent=2))
    print(json.dumps(result))


if __name__ == "__main__":
    main()