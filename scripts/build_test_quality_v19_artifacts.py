"""Build Test Quality v1.9 pre-batch artifacts from the authority preflight."""
from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "generated" / "wave2d" / "evaluator-expansion"
PREFLIGHT = OUT / "test_quality_v19_authority_preflight.json"
RULES = ROOT / "registry" / "test_quality_rules.json"
V18 = ROOT / "registry" / "wave2d_evaluator_registry_v1_8.json"
DRAFT = ROOT / "registry" / "wave2d_evaluator_registry_v1_9_draft.json"
TARGETS = {"EMS-CTRL-027", "EMS-CTRL-028", "EMS-CTRL-029", "EMS-CTRL-031"}
CHECKS = {"EMS-CTRL-027": "v19_regression", "EMS-CTRL-028": "v19_contract_api", "EMS-CTRL-029": "v19_performance", "EMS-CTRL-031": "v19_retention"}
EVIDENCE_TYPES = {"EMS-CTRL-027": "TEST_REGRESSION_CI", "EMS-CTRL-028": "TEST_CONTRACT_API_CI", "EMS-CTRL-029": "TEST_PERFORMANCE_SERVICE", "EMS-CTRL-031": "TEST_EVIDENCE_RETENTION_STORE"}
BOUNDARIES = {"EMS-CTRL-027": "MIXED_AUTOMATABLE_HYBRID_HUMAN_EVIDENCE_REQUIRED", "EMS-CTRL-028": "HYBRID", "EMS-CTRL-029": "HYBRID", "EMS-CTRL-031": "HYBRID"}


def dump(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    preflight = json.loads(PREFLIGHT.read_text(encoding="utf-8"))
    if preflight.get("preflight_state") != "PASS" or not preflight.get("implementation_authorized"):
        raise SystemExit("authority preflight is not PASS/authorized")
    assertions = preflight["assertions"]
    by_control = {control: [item for item in assertions if item["control_id"] == control] for control in TARGETS}
    if {control: len(items) for control, items in by_control.items()} != {"EMS-CTRL-027": 4, "EMS-CTRL-028": 5, "EMS-CTRL-029": 6, "EMS-CTRL-031": 6}:
        raise SystemExit("unexpected authority assertion distribution")
    rules = json.loads(RULES.read_text(encoding="utf-8"))
    for control, items in by_control.items():
        first = items[0]
        rules["rules"][control] = {
            "name": first["control_name"], "supported": True, "evaluation_mode": "test_quality_v19",
            "evidence_type": EVIDENCE_TYPES[control], "evidence_authority": first["evidence_authority"],
            "effective_applicability_source": "registry/wave2d/test_quality_effective_applicability.yaml",
            "ems_authority": "C:/temp/standars/ems/registry/test_quality_control_requirements.json",
            "decision_ids": [item["decision_id"] for item in items],
            "assertions": [{"decision_id": item["decision_id"], "assertion_id": f"{item['decision_id']}-RULE", "automation_classification": item["automation_classification"], "ems_requirement": item["normative_requirement"]} for item in items],
            "checks": [{"type": CHECKS[control], "assertion_id": f"{control.lower()}_authoritative_evidence"}],
            "pass_policy": "ALL", "automation_boundary": BOUNDARIES[control],
            "repository_only_pass_permitted": control not in {"EMS-CTRL-029", "EMS-CTRL-031"},
        }
    dump(RULES, rules)
    matrix = {"component": "Hayes Verify", "family": "test_quality", "registry_target": "1.9-draft", "source_authority_preflight": str(PREFLIGHT.relative_to(ROOT)).replace("\\", "/"), "assertion_counts": preflight["assertion_automation_counts"], "assertions": [{**item, "ems_authority_path": "C:/temp/standars/ems/registry/test_quality_control_requirements.json", "applicability_source": "C:/temp/standars/ems/registry/wave2d/test_quality_effective_applicability.yaml", "observable_evidence": "Authoritative evidence as stated by EMS; repository evidence is supporting only when the authority says so.", "evaluator_behavior": "PASS/FAIL only from qualifying authoritative evidence; missing or ambiguous authority produces WARNING/INSUFFICIENT with HUMAN_REVIEW.", "implementation_disposition": "IMPLEMENTED_PENDING_BATCH_VERIFICATION"} for item in assertions]}
    dump(OUT / "test_quality_v19_implementation_matrix.json", matrix)
    coverage = {"family": "test_quality", "selected_control_count": 4, "backlog_control_count": 4, "implementable_count": 4, "blocked_count": 0, "controls": [{"control_id": control, "rule_registered": True, "rule_supported": True, "ems_authority_traceability": [item["decision_id"] for item in items], "evidence_authority": items[0]["evidence_authority"], "implementation_state": "IMPLEMENTED_PENDING_BATCH_VERIFICATION"} for control, items in sorted(by_control.items())]}
    dump(OUT / "test_quality_v19_family_coverage.json", coverage)
    draft = json.loads(V18.read_text(encoding="utf-8"))
    draft["registry_version"] = "1.9-draft"; draft["status"] = "DRAFT"; draft["derived_from_registry"] = "wave2d_evaluator_registry_v1_8.json"
    for control, items in by_control.items():
        record = draft["controls"][control]
        record.update({"implementation_state": "IMPLEMENTED_PENDING_BATCH_VERIFICATION", "supported": False, "decision_source": "test_quality_controlled_requirements_publication", "ems_requirements_authority": "C:/temp/standars/ems/registry/test_quality_control_requirements.json", "ems_evidence_authority": "C:/temp/standars/ems/registry/test_quality_evidence_authority.json", "ems_traceability": "C:/temp/standars/ems/registry/test_quality_traceability.json", "ems_decision_ids": [item["decision_id"] for item in items], "automation_boundary": BOUNDARIES[control], "priority2_expansion_state": "IMPLEMENTED_PENDING_BATCH_VERIFICATION"})
    draft["implementation_state_counts"] = dict(sorted(Counter(item["implementation_state"] for item in draft["controls"].values()).items()))
    if sum(draft["implementation_state_counts"].values()) != draft["control_count"]:
        raise SystemExit("draft registry state counts invalid")
    dump(DRAFT, draft)
    print(json.dumps({"rules": 21, "matrix": len(assertions), "coverage": "4/4/0", "draft": str(DRAFT)}))


if __name__ == "__main__":
    main()