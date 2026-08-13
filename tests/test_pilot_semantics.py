import json

import pytest

from hayes_verify.contracts import ContractBundle
from hayes_verify.pilots.github_evaluators import (
    evaluate_branch_protection,
    evaluate_pr_review,
    evaluate_secret_scanning,
)


def _request(control_id: str) -> dict:
    return {
        "contract_version": "1.0",
        "wave": "2D",
        "request_id": f"REQ-{control_id}",
        "control_id": control_id,
        "target_id": "REPO-001",
        "repository_name": "C:/repo",
        "applicability_state": "APPLICABLE",
        "requested_at_utc": "2026-08-13T00:00:00+00:00",
        "control_definition_sha256": "0" * 64,
        "applicability_matrix_sha256": "0" * 64,
        "requested_evidence_types": ["GITHUB_CONFIGURATION"],
    }


def _evidence(control_id: str, obs: dict) -> list[dict]:
    return [{
        "contract_version": "1.0",
        "wave": "2D",
        "evidence_id": "E1",
        "request_id": f"REQ-{control_id}",
        "control_id": control_id,
        "target_id": "REPO-001",
        "evidence_type": "TEST",
        "source": "test",
        "collected_at_utc": "2026-08-13T00:00:00+00:00",
        "sha256": "0" * 64,
        "observation": json.dumps(obs, sort_keys=True),
        "provenance": {
            "collector": "test",
            "collector_version": "1",
            "repository_path_or_url": "C:/repo",
            "repository_commit_sha": "abcdef0",
            "collected_at_utc": "2026-08-13T00:00:00+00:00",
        },
        "sensitive": False,
    }]


@pytest.mark.parametrize(
    ("control_id", "evaluator"),
    [
        ("EMS-CTRL-009", evaluate_branch_protection),
        ("EMS-CTRL-010", evaluate_pr_review),
        ("EMS-CTRL-018", evaluate_secret_scanning),
    ],
)
def test_api_error_never_passes(control_id, evaluator):
    bundle = ContractBundle.discover()
    result = evaluator(
        _request(control_id),
        _evidence(control_id, {
            "api_success": False,
            "api_status": "ERROR",
            "raw_summary": {},
        }),
    )
    bundle.validate_result(result)
    assert result["result_state"] != "PASS"
    assert result["promotion_state"] == "NOT_PROMOTED"


def test_branch_protection_pass_requires_structured_proof():
    result = evaluate_branch_protection(
        _request("EMS-CTRL-009"),
        _evidence("EMS-CTRL-009", {
            "api_success": True,
            "api_status": "SUCCESS",
            "protected": True,
            "raw_summary": {"keys": ["required_pull_request_reviews"]},
        }),
    )
    assert result["result_state"] == "PASS"


@pytest.mark.parametrize("count", [None, 0])
def test_pr_review_without_required_approval_fails(count):
    result = evaluate_pr_review(
        _request("EMS-CTRL-010"),
        _evidence("EMS-CTRL-010", {
            "api_success": True,
            "api_status": "SUCCESS",
            "required_pull_request_reviews_present": True,
            "required_approving_review_count": count,
            "raw_summary": {},
        }),
    )
    assert result["result_state"] == "FAIL"


def test_pr_review_with_required_approval_passes():
    result = evaluate_pr_review(
        _request("EMS-CTRL-010"),
        _evidence("EMS-CTRL-010", {
            "api_success": True,
            "api_status": "SUCCESS",
            "required_pull_request_reviews_present": True,
            "required_approving_review_count": 1,
            "raw_summary": {},
        }),
    )
    assert result["result_state"] == "PASS"


@pytest.mark.parametrize(
    ("status", "expected"),
    [("enabled", "PASS"), ("disabled", "FAIL"), (None, "FAIL")],
)
def test_secret_scanning_semantics(status, expected):
    result = evaluate_secret_scanning(
        _request("EMS-CTRL-018"),
        _evidence("EMS-CTRL-018", {
            "api_success": True,
            "api_status": "SUCCESS",
            "secret_scanning_status": status,
            "push_protection_status": "enabled",
            "raw_summary": {"security_and_analysis_present": True},
        }),
    )
    assert result["result_state"] == expected
    assert result["promotion_state"] == "NOT_PROMOTED"
