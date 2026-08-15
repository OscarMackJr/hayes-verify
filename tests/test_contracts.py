import json
from pathlib import Path

from hayes_verify.contracts import ContractBundle


def test_contract_bundle_loads():
    bundle = ContractBundle.discover()
    assert bundle.freeze["status"] == "PASS"
    assert bundle.freeze["authority"]["applicability"] == "EMS"
    assert bundle.freeze["authority"]["evidence_promotion"] == "EMS"


def test_example_request_validates():
    bundle = ContractBundle.discover()
    root = Path(__file__).resolve().parents[1]
    payload = json.loads((root / "examples" / "evaluation_request.json").read_text())
    bundle.validate_request(payload)


def test_organization_request_and_authority_roles_validate():
    bundle = ContractBundle.discover()
    request = {
        "contract_version": "1.0",
        "wave": "2D",
        "request_id": "TEST-ORG-001",
        "control_id": "EMS-CTRL-900",
        "target_id": "ORG-TEST",
        "target_type": "ORGANIZATION",
        "evaluation_role": "AUTHORITATIVE_EVALUATION",
        "organization_id": "org-test",
        "organization_name": "Test Organization",
        "evidence_provider_type": "FILE",
        "evidence_provider_reference": "tests/fixtures/wave2d/organization_evidence_example.json",
        "applicability_state": "APPLICABLE",
        "requested_at_utc": "2026-08-15T00:00:00+00:00",
    }
    bundle.validate_request(request)
    result = {
        "contract_version": "1.0",
        "wave": "2D",
        "request_id": "TEST-ORG-001",
        "control_id": "EMS-CTRL-900",
        "target_id": "ORG-TEST",
        "target_type": "ORGANIZATION",
        "evaluation_role": "AUTHORITATIVE_EVALUATION",
        "authoritative_compliance": True,
        "evaluation_state": "COMPLETE",
        "evidence_state": "SUFFICIENT",
        "result_state": "PASS",
        "evaluated_at_utc": "2026-08-15T00:00:00+00:00",
        "evidence_ids": ["TEST-EVIDENCE"],
        "rationale": "Generic organization target contract validated.",
        "promotion_state": "NOT_PROMOTED",
    }
    bundle.validate_result(result)
    result.update({"target_type": "REPOSITORY", "target_id": "REPO-TEST", "evaluation_role": "PROJECTION", "authoritative_compliance": False, "result_state": "WARNING", "evidence_state": "INSUFFICIENT"})
    bundle.validate_result(result)
