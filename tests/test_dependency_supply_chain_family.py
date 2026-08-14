import json
from pathlib import Path

from hayes_verify.evaluator_families.dependency_supply_chain import evaluate_rule


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


def test_manifest_and_lockfile_pass(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "package.json").write_text("{}", encoding="utf-8")
    (repo / "package-lock.json").write_text("{}", encoding="utf-8")

    rules = write_rule(
        tmp_path,
        [
            {
                "type": "repository_dependency_manifest_present",
                "assertion_id": "manifest",
            },
            {
                "type": "repository_lockfile_present",
                "assertion_id": "lock",
            },
        ],
    )

    _, result = evaluate_rule("EMS-CTRL-999", repo, rules)
    assert result["result_state"] == "PASS"


def test_manifest_and_lockfile_fail_without_lock(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "package.json").write_text("{}", encoding="utf-8")

    rules = write_rule(
        tmp_path,
        [
            {
                "type": "repository_dependency_manifest_present",
                "assertion_id": "manifest",
            },
            {
                "type": "repository_lockfile_present",
                "assertion_id": "lock",
            },
        ],
    )

    _, result = evaluate_rule("EMS-CTRL-999", repo, rules)
    assert result["result_state"] == "FAIL"


def test_workflow_scan_pass(tmp_path):
    repo = tmp_path / "repo"
    wf = repo / ".github" / "workflows"
    wf.mkdir(parents=True)
    (wf / "security.yml").write_text(
        "steps:\n  - run: pip-audit\n",
        encoding="utf-8",
    )

    rules = write_rule(
        tmp_path,
        [
            {
                "type": "workflow_regex_any",
                "regex": r"(?is)(pip-audit|snyk)",
                "assertion_id": "scan",
            }
        ],
    )

    _, result = evaluate_rule("EMS-CTRL-999", repo, rules)
    assert result["result_state"] == "PASS"


def test_integrity_marker_pass(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "Cargo.lock").write_text("", encoding="utf-8")

    rules = write_rule(
        tmp_path,
        [
            {
                "type": "repository_integrity_marker_present",
                "assertion_id": "integrity",
            }
        ],
    )

    _, result = evaluate_rule("EMS-CTRL-999", repo, rules)
    assert result["result_state"] == "PASS"
