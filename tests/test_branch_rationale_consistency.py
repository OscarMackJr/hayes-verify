import json

from hayes_verify.pilots.github_evaluators import evaluate_branch_protection


def _request() -> dict:
    return {
        "contract_version": "1.0",
        "wave": "2D",
        "request_id": "REQ-009",
        "control_id": "EMS-CTRL-009",
        "target_id": "REPO-001",
        "repository_name": "C:/repo",
        "applicability_state": "APPLICABLE",
        "requested_at_utc": "2026-08-13T00:00:00+00:00",
        "control_definition_sha256": "0" * 64,
        "applicability_matrix_sha256": "0" * 64,
        "requested_evidence_types": ["GITHUB_CONFIGURATION"],
    }


def _evidence(obs: dict) -> list[dict]:
    return [{
        "contract_version": "1.0",
        "wave": "2D",
        "evidence_id": "E1",
        "request_id": "REQ-009",
        "control_id": "EMS-CTRL-009",
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


def test_branch_protection_rationale_names_evaluated_branch():
    result = evaluate_branch_protection(
        _request(),
        _evidence({
            "api_success": True,
            "api_status": "SUCCESS",
            "protected": True,
            "evaluated_branch": "implementation/bootstrap",
            "raw_summary": {},
        }),
    )

    assert result["result_state"] == "PASS"
    assert "implementation/bootstrap" in result["rationale"]
    assert "for main" not in result["rationale"]
    assert result["promotion_state"] == "NOT_PROMOTED"


def test_branch_protection_failure_rationale_names_evaluated_branch():
    result = evaluate_branch_protection(
        _request(),
        _evidence({
            "api_success": True,
            "api_status": "SUCCESS",
            "protected": False,
            "evaluated_branch": "release/current",
            "raw_summary": {},
        }),
    )

    assert result["result_state"] == "FAIL"
    assert "release/current" in result["rationale"]
    assert "for main" not in result["rationale"]


def test_branch_protection_missing_branch_uses_generic_label():
    result = evaluate_branch_protection(
        _request(),
        _evidence({
            "api_success": True,
            "api_status": "SUCCESS",
            "protected": True,
            "evaluated_branch": None,
            "raw_summary": {},
        }),
    )

    assert result["result_state"] == "PASS"
    assert "evaluated branch" in result["rationale"]
    assert "for main" not in result["rationale"]
