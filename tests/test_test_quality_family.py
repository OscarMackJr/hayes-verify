import json
from pathlib import Path

from hayes_verify.evaluator_families.test_quality import evaluate_rule


def write_rule(tmp_path: Path, checks):
    path = tmp_path / "rules.json"
    path.write_text(
        json.dumps(
            {
                "rules": {
                    "EMS-CTRL-999": {
                        "supported": True,
                        "evidence_type": "TEST",
                        "checks": checks,
                        "pass_policy": "ALL",
                    }
                }
            }
        ),
        encoding="utf-8",
    )
    return path


def test_test_files_present_pass(tmp_path):
    repo = tmp_path / "repo"
    tests = repo / "tests"
    tests.mkdir(parents=True)
    (tests / "test_example.py").write_text(
        "def test_ok():\n    assert True\n",
        encoding="utf-8",
    )

    rules = write_rule(
        tmp_path,
        [
            {
                "type": "repository_test_files_present",
                "assertion_id": "tests",
            }
        ],
    )

    _, result = evaluate_rule("EMS-CTRL-999", repo, rules)
    assert result["result_state"] == "PASS"


def test_contract_marker_pass(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "openapi.yaml").write_text("openapi: 3.0.0", encoding="utf-8")

    rules = write_rule(
        tmp_path,
        [
            {
                "type": "repository_contract_test_marker_present",
                "assertion_id": "contract",
            }
        ],
    )

    _, result = evaluate_rule("EMS-CTRL-999", repo, rules)
    assert result["result_state"] == "PASS"


def test_performance_marker_pass(tmp_path):
    repo = tmp_path / "repo"
    perf = repo / "performance"
    perf.mkdir(parents=True)
    (perf / "load_test.js").write_text("", encoding="utf-8")

    rules = write_rule(
        tmp_path,
        [
            {
                "type": "repository_performance_test_marker_present",
                "assertion_id": "performance",
            }
        ],
    )

    _, result = evaluate_rule("EMS-CTRL-999", repo, rules)
    assert result["result_state"] == "PASS"


def test_workflow_regex_pass(tmp_path):
    repo = tmp_path / "repo"
    workflows = repo / ".github" / "workflows"
    workflows.mkdir(parents=True)
    (workflows / "tests.yml").write_text(
        "steps:\n  - run: pytest\n",
        encoding="utf-8",
    )

    rules = write_rule(
        tmp_path,
        [
            {
                "type": "workflow_regex_any",
                "regex": r"(?is)(pytest|jest)",
                "assertion_id": "workflow",
            }
        ],
    )

    _, result = evaluate_rule("EMS-CTRL-999", repo, rules)
    assert result["result_state"] == "PASS"
