import json
from pathlib import Path

from hayes_verify.evaluator_families.dependency_supply_chain import evaluate_rule, run


def rules(tmp_path: Path) -> Path:
    path = tmp_path / "rules.json"
    path.write_text(json.dumps({"rules": {"EMS-CTRL-023": {"supported": True, "evidence_type": "VULNERABILITY_REMEDIATION_ORGANIZATIONAL", "assertions": [{"assertion_id": f"DSC-023-{i:02d}-RULE"} for i in range(1, 14)]}}}), encoding="utf-8")
    return path


def authority(**overrides):
    finding = {"finding_id": "F-1", "affected_targets": ["REPO-001"], "severity": "Critical", "first_validated_detection_timestamp": "2026-01-01T00:00:00Z", "remediation_target_date": "2026-01-08T00:00:00Z", "status": "OPEN", "owner": "owner"}
    value = {"authority_type": "vulnerability_management", "source_identity": "vm-1", "accessible": True, "evidence_timestamp": "2026-01-01T12:00:00Z", "reference_timestamp": "2026-01-02T00:00:00Z", "findings": [finding]}
    value.update(overrides)
    return value


def evaluate(tmp_path, evidence):
    repo = tmp_path / "repo"; repo.mkdir(exist_ok=True)
    return evaluate_rule("EMS-CTRL-023", repo, rules(tmp_path), evidence)[1]


def test_authoritative_critical_inside_target_passes(tmp_path):
    assert evaluate(tmp_path, authority())["result_state"] == "PASS"


def test_critical_overdue_fails(tmp_path):
    data = authority(reference_timestamp="2026-01-10T00:00:00Z", evidence_timestamp="2026-01-09T12:00:00Z")
    assert evaluate(tmp_path, data)["result_state"] == "FAIL"


def test_high_overdue_fails(tmp_path):
    data = authority(reference_timestamp="2026-02-02T00:00:00Z", evidence_timestamp="2026-02-01T12:00:00Z")
    data["findings"][0].update({"severity": "High", "remediation_target_date": "2026-01-31T00:00:00Z"})
    assert evaluate(tmp_path, data)["result_state"] == "FAIL"


def test_medium_and_low_inside_target_pass(tmp_path):
    data = authority(); data["findings"] = [dict(data["findings"][0], severity="Medium", remediation_target_date="2026-04-01T00:00:00Z"), dict(data["findings"][0], finding_id="F-2", severity="Low", remediation_target_date="2026-07-01T00:00:00Z")]
    assert evaluate(tmp_path, data)["result_state"] == "PASS"


def test_missing_or_repository_only_evidence_never_passes(tmp_path):
    assert evaluate(tmp_path, None)["result_state"] == "WARNING"
    assert evaluate(tmp_path, {"repository": {"result": "PASS"}})["result_state"] == "WARNING"


def test_stale_authority_never_passes(tmp_path):
    data = authority(reference_timestamp="2026-01-03T13:00:00Z")
    assert evaluate(tmp_path, data)["result_state"] == "WARNING"


def test_missing_owner_or_target_fails_with_authority(tmp_path):
    data = authority(); data["findings"][0]["owner"] = ""
    assert evaluate(tmp_path, data)["result_state"] == "FAIL"
    data = authority(); data["findings"][0].pop("remediation_target_date")
    assert evaluate(tmp_path, data)["result_state"] == "FAIL"


def test_valid_exception_passes_and_expired_exception_fails(tmp_path):
    data = authority(reference_timestamp="2026-01-10T00:00:00Z", evidence_timestamp="2026-01-09T12:00:00Z")
    data["findings"][0]["exception"] = {"approving_authority": "Security Authority", "justification": "risk", "compensating_controls": "control", "owner": "owner", "approval_timestamp": "2026-01-05T00:00:00Z", "expiration_timestamp": "2026-02-01T00:00:00Z"}
    assert evaluate(tmp_path, data)["result_state"] == "PASS"
    data["findings"][0]["exception"]["expiration_timestamp"] = "2026-01-09T00:00:00Z"
    assert evaluate(tmp_path, data)["result_state"] == "FAIL"


def test_false_positive_and_verified_remediation_pass(tmp_path):
    data = authority(); data["findings"][0].update({"status": "APPROVED_FALSE_POSITIVE", "false_positive_approved": True})
    assert evaluate(tmp_path, data)["result_state"] == "PASS"
    data["findings"][0].update({"status": "VERIFIED_REMEDIATED", "closure_timestamp": "2026-01-01T01:00:00Z"})
    assert evaluate(tmp_path, data)["result_state"] == "PASS"


def test_ambiguous_or_conflicting_authority_requires_review(tmp_path):
    assert evaluate(tmp_path, authority(ambiguous=True))["result_state"] == "WARNING"
    assert evaluate(tmp_path, authority(conflicting=True))["result_state"] == "WARNING"

def test_repository_projection_cannot_be_independent_pass(tmp_path):
    class Bundle:
        root = tmp_path

        @staticmethod
        def validate_result(result):
            assert result["contract_version"] == "1.0"

    registry = tmp_path / "registry"; registry.mkdir()
    (registry / "dependency_supply_chain_rules.json").write_text(rules(tmp_path).read_text(encoding="utf-8"), encoding="utf-8")
    request = {"request_id": "R-1", "control_id": "EMS-CTRL-023", "target_id": "REPO-001", "evaluation_role": "PROJECTION", "authoritative_evidence": authority()}
    _, result = run(Bundle(), request, tmp_path, "org/repo")
    assert result["result_state"] == "WARNING"
    assert result["repository_projection_only"] is True