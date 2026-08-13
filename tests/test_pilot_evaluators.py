import pytest

from hayes_verify.contracts import ContractBundle
from hayes_verify.pilots.orchestration import CONTROL_MAP


def test_pilot_controls_registered():
    assert set(CONTROL_MAP) == {
        "EMS-CTRL-009",
        "EMS-CTRL-010",
        "EMS-CTRL-018",
    }


@pytest.mark.parametrize("control_id", sorted(CONTROL_MAP))
def test_pilot_result_never_promotes(control_id, tmp_path):
    bundle = ContractBundle.discover()

    request = {
        "contract_version": "1.0",
        "wave": "2D",
        "request_id": f"REQ-{control_id}",
        "control_id": control_id,
        "target_id": "REPO-001",
        "repository_name": str(tmp_path),
        "applicability_state": "APPLICABLE",
        "requested_at_utc": "2026-08-13T00:00:00+00:00",
        "control_definition_sha256": "0" * 64,
        "applicability_matrix_sha256": "0" * 64,
        "requested_evidence_types": ["GITHUB_CONFIGURATION"],
    }

    _collector, evaluator = CONTROL_MAP[control_id]

    fake_evidence = [
        {
            "contract_version": "1.0",
            "wave": "2D",
            "evidence_id": "E1",
            "request_id": request["request_id"],
            "control_id": control_id,
            "target_id": "REPO-001",
            "evidence_type": "TEST",
            "source": "test",
            "collected_at_utc": "2026-08-13T00:00:00+00:00",
            "sha256": "0" * 64,
            "observation": "enabled configuration present",
            "provenance": {
                "collector": "test",
                "collector_version": "1",
                "repository_path_or_url": str(tmp_path),
                "repository_commit_sha": "abcdef0",
                "collected_at_utc": "2026-08-13T00:00:00+00:00",
            },
            "sensitive": False,
        }
    ]

    result = evaluator(request, fake_evidence)
    bundle.validate_result(result)

    assert result["promotion_state"] == "NOT_PROMOTED"
