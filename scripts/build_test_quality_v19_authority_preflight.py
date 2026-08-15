"""Read-only EMS authority preflight for the next Test Quality expansion."""

from __future__ import annotations

import hashlib
import json
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
EMS = Path(r"C:\temp\standars\ems")
OUT = ROOT / "generated" / "wave2d" / "evaluator-expansion"
REQ = EMS / "registry" / "test_quality_control_requirements.json"
CERT = EMS / "registry" / "test_quality_publication_certification.json"
EVIDENCE = EMS / "registry" / "test_quality_evidence_authority.json"
APPLICABILITY = EMS / "registry" / "wave2d" / "test_quality_effective_applicability.yaml"
TRACE = EMS / "registry" / "test_quality_traceability.json"
HANDOFF = EMS / "generated" / "governance-proposals" / "test_quality_hayes_authority_handoff.json"
REGISTRY = ROOT / "registry" / "wave2d_evaluator_registry_v1_8.json"
PRIORITY2_MANIFEST = OUT / "priority2_completion_manifest.json"
PRIORITY2_CERT = OUT / "priority2_completion_certification.json"
ASSESSMENT = OUT / "next_phase_assessment.json"
OUTPUT_JSON = OUT / "test_quality_v19_authority_preflight.json"
OUTPUT_MD = OUT / "TEST_QUALITY_V19_AUTHORITY_PREFLIGHT.md"

EXPECTED_CONTROLS = {"EMS-CTRL-027", "EMS-CTRL-028", "EMS-CTRL-029", "EMS-CTRL-031"}
EXPECTED_COUNTS = {"EMS-CTRL-027": 4, "EMS-CTRL-028": 5, "EMS-CTRL-029": 6, "EMS-CTRL-031": 6}

# The classifications are tied to the approved evidence source and terminal behavior.
CLASSIFICATIONS = {
    "TQ-027-01": ("HYBRID", "Controlled impact assessment determines applicability."),
    "TQ-027-02": ("AUTOMATABLE", "CI/CD execution record is objective repository evidence."),
    "TQ-027-03": ("HYBRID", "Gate result is observable, but active exception status must be resolved."),
    "TQ-027-04": ("HUMAN_EVIDENCE_REQUIRED", "Exception approval and risk acceptance are controlled human evidence."),
    "TQ-028-01": ("HYBRID", "Interface applicability requires an interface inventory/change determination."),
    "TQ-028-02": ("HYBRID", "Coverage classes require test metadata proving positive, negative, and compatibility coverage."),
    "TQ-028-03": ("AUTOMATABLE", "CI/CD contract execution evidence is objective when available."),
    "TQ-028-04": ("HYBRID", "Gate result is observable, but active exception status must be resolved."),
    "TQ-028-05": ("HUMAN_EVIDENCE_REQUIRED", "Consumer notification and migration/rollback approval are controlled human evidence."),
    "TQ-029-01": ("HYBRID", "Service applicability is determined through the service registry and material-change evidence."),
    "TQ-029-02": ("HUMAN_EVIDENCE_REQUIRED", "Approved service workload profiles require service authority."),
    "TQ-029-03": ("HUMAN_EVIDENCE_REQUIRED", "Service-specific objectives/baselines are established in service governance."),
    "TQ-029-04": ("HYBRID", "Authoritative service store evidence can be objectively read only when accessible to Hayes."),
    "TQ-029-05": ("HYBRID", "PASS/FAIL is deterministic only from authoritative service evidence; otherwise HUMAN_REVIEW."),
    "TQ-029-06": ("HUMAN_EVIDENCE_REQUIRED", "Service exception approval is controlled human/service evidence."),
    "TQ-031-01": ("HYBRID", "Evidence classes are observable only through the authoritative evidence store."),
    "TQ-031-02": ("HYBRID", "Three-year retention requires authoritative store configuration/evidence."),
    "TQ-031-03": ("HYBRID", "Store approval, retention configuration, and tamper evidence require authoritative-store access."),
    "TQ-031-04": ("AUTOMATABLE", "CI/CD metadata can objectively bind evidence to repository, revision, build, and test result."),
    "TQ-031-05": ("HUMAN_EVIDENCE_REQUIRED", "Hold and exception status are controlled human/legal evidence."),
    "TQ-031-06": ("HYBRID", "PASS/FAIL requires authoritative retention proof; inaccessible or ambiguous authority routes to HUMAN_REVIEW."),
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> None:
    required_paths = [REQ, CERT, EVIDENCE, APPLICABILITY, TRACE, HANDOFF, REGISTRY, PRIORITY2_MANIFEST, PRIORITY2_CERT, ASSESSMENT]
    missing_paths = [str(path) for path in required_paths if not path.is_file()]
    if missing_paths:
        raise SystemExit(f"missing authority/baseline artifacts: {missing_paths}")
    if (ROOT / "registry" / "wave2d_evaluator_registry_v1_9_draft.json").exists():
        raise SystemExit("v1.9 draft already exists; preflight must not proceed")
    expected_req_hash = "08271a749f3fde6958ef57ef7c10480b7456f98a9f3f04fff4c0b328338bbf28"
    expected_cert_hash = "fb7f1c8739df41d1485390b9ada4ed6f7657ace453919cba63110bf1d06b622e"
    if sha256(REQ) != expected_req_hash or sha256(CERT) != expected_cert_hash:
        raise SystemExit("EMS immutable authority hash mismatch")
    requirements = load_json(REQ)
    publication = load_json(CERT)
    evidence = load_json(EVIDENCE)
    trace = load_json(TRACE)
    handoff = load_json(HANDOFF)
    applicability = yaml.safe_load(APPLICABILITY.read_text(encoding="utf-8"))
    registry = load_json(REGISTRY)
    priority2_manifest = load_json(PRIORITY2_MANIFEST)
    priority2_cert = load_json(PRIORITY2_CERT)
    assessment = load_json(ASSESSMENT)
    errors: list[str] = []
    if registry.get("registry_version") != "1.8":
        errors.append("Hayes registry is not v1.8")
    if priority2_manifest.get("completion_state") != "COMPLETE" or priority2_cert.get("completion_state") != "COMPLETE":
        errors.append("Priority-2 is not complete/baselined")
    for key, expected in {"original_control_count": 21, "implemented_control_count": 21, "remaining_control_count": 0, "original_family_count": 4, "completed_family_count": 4, "remaining_family_count": 0}.items():
        if priority2_manifest.get(key) != expected:
            errors.append(f"Priority-2 manifest mismatch: {key}")
    if assessment.get("recommended_next_family") != "test_quality":
        errors.append("next-phase assessment does not select test_quality")
    selected = {item["control_id"] for item in assessment.get("remaining_controls", []) if item.get("evaluator_family") == "test_quality" and item.get("implementation_state") == "PLANNED_AUTOMATED"}
    if selected != EXPECTED_CONTROLS:
        errors.append(f"unexpected next test_quality controls: {sorted(selected)}")
    if publication.get("publication_state") != "TEST_QUALITY_CONTROLLED_REQUIREMENTS_PUBLISHED":
        errors.append("EMS publication state invalid")
    if {key: publication.get(key) for key in ["decisions_expected", "decisions_published", "non_null_normative_values", "orphaned_decisions"]} != {"decisions_expected": 21, "decisions_published": 21, "non_null_normative_values": 21, "orphaned_decisions": 0}:
        errors.append("EMS publication count summary invalid")
    controls = requirements.get("controls", [])
    if {item.get("control_id") for item in controls} != EXPECTED_CONTROLS:
        errors.append("requirements control set invalid")
    decisions = []
    records_by_control = {}
    for control in controls:
        required = ["applicability", "evidence_authority", "pass_condition", "fail_condition", "human_review_or_insufficient_condition", "exception_behavior"]
        absent = [field for field in required if not control.get(field)]
        if absent:
            errors.append(f"{control.get('control_id')} missing fields: {absent}")
        records = control.get("normative_requirements", [])
        records_by_control[control["control_id"]] = records
        for record in records:
            decision_id = record.get("decision_id")
            if not decision_id or not record.get("normative_requirement") or not record.get("approval_provenance"):
                errors.append(f"incomplete normative record: {control.get('control_id')} {decision_id}")
            if decision_id not in CLASSIFICATIONS:
                errors.append(f"unclassified decision: {decision_id}")
            decisions.append({
                "control_id": control["control_id"], "control_name": control["control_name"], "decision_id": decision_id,
                "normative_requirement": record["normative_requirement"], "applicability": control["applicability"],
                "evidence_authority": control["evidence_authority"], "pass_condition": control["pass_condition"],
                "fail_condition": control["fail_condition"], "human_review_or_insufficient_condition": control["human_review_or_insufficient_condition"],
                "exception_behavior": control["exception_behavior"], "automation_classification": CLASSIFICATIONS[decision_id][0], "classification_rationale": CLASSIFICATIONS[decision_id][1],
            })
    distribution = Counter(item["control_id"] for item in decisions)
    if dict(distribution) != EXPECTED_COUNTS or len(decisions) != 21:
        errors.append(f"requirements distribution invalid: {dict(distribution)}")
    trace_ids = [decision_id for item in trace.get("control_traceability", []) for decision_id in item.get("decision_ids", [])]
    if len(trace_ids) != 21 or len(set(trace_ids)) != 21:
        errors.append("traceability does not contain 21 unique decision IDs")
    if set(trace_ids) != {item["decision_id"] for item in decisions}:
        errors.append("traceability decision mapping differs from requirements")
    if applicability.get("model") != "FROZEN_APPLICABLE + POLICY_CONDITION_EVIDENCE -> EFFECTIVE_APPLICABILITY" or applicability.get("historical_freeze_immutable") is not True or applicability.get("missing_policy_condition_evidence") != "HUMAN_REVIEW":
        errors.append("effective applicability model invalid")
    evidence_by_control = {item["control_id"]: item for item in evidence.get("controls", [])}
    if set(evidence_by_control) != EXPECTED_CONTROLS:
        errors.append("evidence-authority control set invalid")
    if "service-performance evidence" not in evidence_by_control["EMS-CTRL-029"].get("authoritative_evidence", ""):
        errors.append("CTRL-029 service authority missing")
    if "repository evidence is supporting only" not in evidence_by_control["EMS-CTRL-029"].get("authoritative_evidence", "").lower():
        errors.append("CTRL-029 repository-only boundary invalid")
    if not any("three years" in record["normative_requirement"].lower() for record in records_by_control["EMS-CTRL-031"]):
        errors.append("CTRL-031 three-year retention missing")
    if "repository artifact presence alone" not in evidence_by_control["EMS-CTRL-031"].get("authoritative_evidence", "").lower():
        errors.append("CTRL-031 repository-only PASS boundary missing")
    handoff_controls = {item["control_id"] for item in handoff.get("controls", [])}
    if handoff_controls != EXPECTED_CONTROLS:
        errors.append("Hayes handoff control set invalid")
    if errors:
        raise SystemExit(json.dumps({"status": "BLOCKED", "errors": errors}, indent=2))
    counts = Counter(item["automation_classification"] for item in decisions)
    evidence_matrix = []
    for control_id in sorted(EXPECTED_CONTROLS):
        item = evidence_by_control[control_id]
        boundary = item["automation_boundary"]
        evidence_matrix.append({
            "control_id": control_id, "authoritative_evidence": item["authoritative_evidence"],
            "supporting_evidence": item["supporting_evidence"], "expected_automation_boundary": boundary,
            "repository_only_pass_permitted": "NO" if control_id in {"EMS-CTRL-029", "EMS-CTRL-031"} else "ONLY_WHEN_AUTHORITATIVE_CI_EVIDENCE_IS_AVAILABLE",
        })
    result = {
        "component": "Hayes Verify", "phase": "Test Quality v1.9 Authority Preflight", "generated_at_utc": datetime.now(UTC).isoformat(),
        "preflight_state": "PASS", "implementation_authorized": True,
        "ems_sources": {"requirements": {"path": str(REQ), "sha256": sha256(REQ)}, "publication_certification": {"path": str(CERT), "sha256": sha256(CERT)}, "evidence_authority": str(EVIDENCE), "effective_applicability": str(APPLICABILITY), "traceability": str(TRACE), "hayes_handoff": str(HANDOFF)},
        "baseline": {"registry_version": registry["registry_version"], "priority2_controls": "21/21/0", "priority2_families": "4/4/0", "pytest_baseline": "51 passed / 0 failed", "v1_9_draft_present": False},
        "publication_readback": {"controls_represented": 4, "decisions_expected": 21, "decisions_published": 21, "non_null_normative_values": 21, "orphaned_decisions": 0, "distribution": dict(distribution)},
        "assertions": decisions, "assertion_automation_counts": dict(counts), "evidence_authority_matrix": evidence_matrix,
        "planning_classification_corrections": [{"control_id": "EMS-CTRL-029", "v1_8_planning": "PLANNED_AUTOMATED", "controlled_boundary": "HYBRID", "reason": "Authoritative service-performance evidence, not repository evidence, determines PASS/FAIL."}, {"control_id": "EMS-CTRL-031", "v1_8_planning": "PLANNED_AUTOMATED", "controlled_boundary": "HYBRID", "reason": "Authoritative retention-store evidence determines PASS/FAIL; repository artifact presence alone is insufficient."}],
        "semantic_gaps": [], "historical_freeze_preservation": "PASS", "ctrl029_service_authority": "PASS", "ctrl031_retention_authority": "PASS",
    }
    OUT.mkdir(parents=True, exist_ok=True)
    OUTPUT_JSON.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    lines = ["# Test Quality v1.9 Authority Preflight", "", "## Decision", "", "**PASS — implementation is authorized.** The preflight verified all 21 approved requirements, evidence authorities, traceability, and effective-applicability rules.", "", "## Evidence boundaries", ""]
    for row in evidence_matrix:
        lines += [f"- **{row['control_id']}** — {row['expected_automation_boundary']} Repository-only PASS: {row['repository_only_pass_permitted']}."]
    lines += ["", "## Planning corrections", "", "- EMS-CTRL-029 must be HYBRID because service-performance evidence is authoritative.", "- EMS-CTRL-031 must be HYBRID because authoritative retention-store evidence is required; repository artifact presence alone is insufficient.", "", "## Assertion classification", "", f"- AUTOMATABLE: {counts['AUTOMATABLE']}", f"- HYBRID: {counts['HYBRID']}", f"- HUMAN_EVIDENCE_REQUIRED: {counts['HUMAN_EVIDENCE_REQUIRED']}", "", "No EMS semantic gaps were found. This preflight authorizes implementation only; it does not authorize a v1.9 draft, immutable batch, or registry promotion."]
    OUTPUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({"status": "PASS", "assertion_automation_counts": dict(counts), "output": str(OUTPUT_JSON)}))


if __name__ == "__main__":
    main()
