import json
from pathlib import Path

from hayes_verify.evaluator_families.test_quality import evaluate_rule


def _rules(tmp_path: Path, control_id: str, check_type: str) -> Path:
    path = tmp_path / "rules.json"
    path.write_text(json.dumps({"rules": {control_id: {"supported": True, "evaluation_mode": "test_quality_v19", "evidence_type": "TEST_QUALITY", "decision_ids": ["TQ-TEST"], "evidence_authority": "authoritative evidence", "checks": [{"type": check_type, "assertion_id": "v19"}], "pass_policy": "ALL"}}}), encoding="utf-8")
    return path


def _repository_evidence(repo: Path, payload: dict) -> None:
    path = repo / ".hayes" / "test-quality"
    path.mkdir(parents=True)
    (path / "ci-evidence.json").write_text(json.dumps(payload), encoding="utf-8")


def test_regression_qualifying_ci_evidence_passes(tmp_path):
    repo = tmp_path / "repo"; repo.mkdir()
    _repository_evidence(repo, {"regression": {"applicable": True, "impact_assessment": {"affects_supported_behavior": True}, "ci_execution": {"repository": "r", "revision": "a", "suite": "regression", "result": "PASS", "timestamp": "2026-01-01", "workflow_identity": "ci"}}})
    _, result = evaluate_rule("EMS-CTRL-027", repo, _rules(tmp_path, "EMS-CTRL-027", "v19_regression"))
    assert result["result_state"] == "PASS"


def test_regression_missing_evidence_requires_review(tmp_path):
    repo = tmp_path / "repo"; repo.mkdir()
    _, result = evaluate_rule("EMS-CTRL-027", repo, _rules(tmp_path, "EMS-CTRL-027", "v19_regression"))
    assert (result["result_state"], result["evidence_state"]) == ("WARNING", "INSUFFICIENT")


def test_regression_failure_with_exception_passes(tmp_path):
    repo = tmp_path / "repo"; repo.mkdir()
    exception = {"affected_change": "c", "risk_rationale": "r", "compensating_controls": "c", "accountable_owner": "o", "approving_authority": "a", "expiry": "2026", "remediation_plan": "p"}
    _repository_evidence(repo, {"regression": {"applicable": True, "impact_assessment": {"affects_supported_behavior": True}, "ci_execution": {"repository": "r", "revision": "a", "suite": "regression", "result": "FAIL", "timestamp": "2026", "workflow_identity": "ci"}, "exception": exception}})
    _, result = evaluate_rule("EMS-CTRL-027", repo, _rules(tmp_path, "EMS-CTRL-027", "v19_regression"))
    assert result["result_state"] == "PASS"


def test_contract_api_qualifying_evidence_passes(tmp_path):
    repo = tmp_path / "repo"; repo.mkdir()
    _repository_evidence(repo, {"contract_api": {"applicable": True, "coverage": {"positive": True, "negative_error": True, "compatibility_breaking_change": True}, "ci_execution": {"repository": "r", "revision": "a", "interface_version": "v1", "result": "PASS", "timestamp": "2026", "workflow_identity": "ci"}}})
    _, result = evaluate_rule("EMS-CTRL-028", repo, _rules(tmp_path, "EMS-CTRL-028", "v19_contract_api"))
    assert result["result_state"] == "PASS"


def test_contract_api_ambiguous_applicability_requires_review(tmp_path):
    repo = tmp_path / "repo"; repo.mkdir()
    _repository_evidence(repo, {"contract_api": {"applicable": False}})
    _, result = evaluate_rule("EMS-CTRL-028", repo, _rules(tmp_path, "EMS-CTRL-028", "v19_contract_api"))
    assert result["result_state"] == "WARNING"


def _performance_evidence(result="PASS"):
    return {"authority_type": "service_performance", "service_registry_reference": "svc-1", "workload_profile": "normal", "objective": "approved", "environment": "prod-like", "revision": "a", "result": result, "timestamp": "2026", "validating_identity": "service-ci"}


def test_performance_authoritative_service_evidence_passes(tmp_path):
    repo = tmp_path / "repo"; repo.mkdir()
    _, result = evaluate_rule("EMS-CTRL-029", repo, _rules(tmp_path, "EMS-CTRL-029", "v19_performance"), _performance_evidence())
    assert result["result_state"] == "PASS"


def test_performance_repository_only_evidence_never_passes(tmp_path):
    repo = tmp_path / "repo"; repo.mkdir()
    _repository_evidence(repo, {"performance": {"result": "PASS"}})
    _, result = evaluate_rule("EMS-CTRL-029", repo, _rules(tmp_path, "EMS-CTRL-029", "v19_performance"))
    assert result["result_state"] == "WARNING"


def _retention_evidence(years=3):
    return {"authority_type": "retention_store", "store_reference": "store-1", "retention_years": years, "access_control": True, "retention_configured": True, "tamper_evident": True, "required_evidence": ["run"], "result": "PASS"}


def test_retention_authoritative_three_year_evidence_passes(tmp_path):
    repo = tmp_path / "repo"; repo.mkdir()
    _, result = evaluate_rule("EMS-CTRL-031", repo, _rules(tmp_path, "EMS-CTRL-031", "v19_retention"), _retention_evidence())
    assert result["result_state"] == "PASS"


def test_repository_artifact_presence_never_proves_retention(tmp_path):
    repo = tmp_path / "repo"; repo.mkdir(); (repo / "test-report.xml").write_text("report", encoding="utf-8")
    _, result = evaluate_rule("EMS-CTRL-031", repo, _rules(tmp_path, "EMS-CTRL-031", "v19_retention"))
    assert result["result_state"] == "WARNING"


def test_insufficient_retention_duration_fails(tmp_path):
    repo = tmp_path / "repo"; repo.mkdir()
    _, result = evaluate_rule("EMS-CTRL-031", repo, _rules(tmp_path, "EMS-CTRL-031", "v19_retention"), _retention_evidence(2))
    assert result["result_state"] == "FAIL"