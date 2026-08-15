import json

from hayes_verify.evaluator_families.test_quality import evaluate_rule


def write_rule(tmp_path, check_type):
    path = tmp_path / "rules.json"
    path.write_text(json.dumps({
        "rules": {
            "EMS-CTRL-999": {
                "supported": True,
                "evidence_type": "TEST",
                "checks": [{"type": check_type, "assertion_id": "assertion"}],
                "pass_policy": "ALL",
            }
        }
    }), encoding="utf-8")
    return path

def test_integration_testing_pass(tmp_path):
    repo = tmp_path / "repo"
    tests = repo / "tests"
    tests.mkdir(parents=True)
    (tests / "test_integration_database.py").write_text("def test_ok():\n    assert True\n", encoding="utf-8")
    rules = write_rule(tmp_path, "repository_integration_test_marker_present")
    _, result = evaluate_rule("EMS-CTRL-999", repo, rules)
    assert result["result_state"] == "PASS"

def test_integration_testing_fail(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    rules = write_rule(tmp_path, "repository_integration_test_marker_present")
    _, result = evaluate_rule("EMS-CTRL-999", repo, rules)
    assert result["result_state"] == "FAIL"

def test_environment_isolation_pass_with_test_compose(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "docker-compose.test.yml").write_text("services:\n  db:\n    image: postgres\n", encoding="utf-8")
    rules = write_rule(tmp_path, "test_environment_isolation_marker_present")
    _, result = evaluate_rule("EMS-CTRL-999", repo, rules)
    assert result["result_state"] == "PASS"

def test_environment_isolation_fail_without_marker(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    rules = write_rule(tmp_path, "test_environment_isolation_marker_present")
    _, result = evaluate_rule("EMS-CTRL-999", repo, rules)
    assert result["result_state"] == "FAIL"

def test_zero_trust_integration_testing_pass(tmp_path):
    repo = tmp_path / "repo"
    tests = repo / "tests"
    tests.mkdir(parents=True)
    (tests / "test_zero_trust_authorization.py").write_text("def test_ok():\n    assert True\n", encoding="utf-8")
    rules = write_rule(tmp_path, "zero_trust_integration_test_marker_present")
    _, result = evaluate_rule("EMS-CTRL-999", repo, rules)
    assert result["result_state"] == "PASS"

def test_zero_trust_integration_testing_fail(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    rules = write_rule(tmp_path, "zero_trust_integration_test_marker_present")
    _, result = evaluate_rule("EMS-CTRL-999", repo, rules)
    assert result["result_state"] == "FAIL"
