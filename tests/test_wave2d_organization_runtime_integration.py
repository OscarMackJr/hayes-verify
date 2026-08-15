import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).parents[1]
SCRIPTS = ROOT / "scripts"
FIXTURES = ROOT / "tests/fixtures/wave2d"


def run(script: str, *args: str, extra_path: Path | None = None):
    paths = [str(ROOT / "src")]
    if extra_path:
        paths.insert(0, str(extra_path))
    environment = {**os.environ, "PYTHONPATH": os.pathsep.join(paths)}
    return subprocess.run([sys.executable, str(SCRIPTS / script), *args], cwd=ROOT, env=environment, text=True, capture_output=True, check=False)


def scope(path: Path, module_name: str) -> Path:
    path.write_text(json.dumps({"families": {"runtime_test": {"implementation": module_name, "controls": {"EMS-CTRL-900": {"supported": True, "collector": "test", "evaluator": "test", "evidence_type": "TEST_ORGANIZATION_EVIDENCE"}}}}}), encoding="utf-8")
    return path


def evaluator_module(tmp_path: Path) -> tuple[Path, str]:
    package = tmp_path / "runtime_test_evaluator.py"
    shutil.copyfile(FIXTURES / "organization_test_evaluator.py", package)
    return tmp_path, "runtime_test_evaluator"


def test_request_builder_creates_generic_organization_authority_and_repository_projections(tmp_path):
    ems = tmp_path / "ems"
    matrix = ems / "generated/wave2d/evaluation-matrix"
    matrix.mkdir(parents=True)
    matrix.joinpath("evaluation_matrix.csv").write_text("control_id,control_name,target_id,repository_name,applicability_state\nEMS-CTRL-900,Generic target,REPO-001,repo,APPLICABLE\nEMS-CTRL-900,Generic target,REPO-002,repo2,APPLICABLE\n")
    request_path = tmp_path / "requests.jsonl"
    run_identity = tmp_path / "run.json"
    run_identity.write_text(json.dumps({"batch_id": "BATCH-X", "request_path": str(request_path)}))
    repository_map = tmp_path / "repositories.json"
    repository_map.write_text(json.dumps({"repositories": {"REPO-001": {"github_repo": "org/repo"}, "REPO-002": {"github_repo": "org/repo2"}}}))
    overrides = tmp_path / "overrides.json"
    overrides.write_text(json.dumps({"REPO-001": {"repository_path": str(tmp_path)}, "REPO-002": {"repository_path": str(tmp_path)}}))
    targets = tmp_path / "targets.json"
    targets.write_text(json.dumps({"organization_targets": [{"target_id": "ORG-TEST", "organization_id": "org-test", "organization_name": "Test Organization"}]}))
    applicability = tmp_path / "applicability.json"
    applicability.write_text(json.dumps({"organization_authoritative_controls": [{"control_id": "EMS-CTRL-900", "organization_target_ids": ["ORG-TEST"], "authoritative_target_count": 1}], "repository_projection_controls": ["EMS-CTRL-900"]}))
    completed = run("build_wave2d_batch_requests_scoped.py", "--ems-root", str(ems), "--run-identity", str(run_identity), "--repository-map", str(repository_map), "--repository-path-overrides", str(overrides), "--organization-targets", str(targets), "--runtime-applicability", str(applicability))
    assert completed.returncode == 0, completed.stderr
    rows = [json.loads(line) for line in request_path.read_text().splitlines()]
    authority = [row for row in rows if row["target_type"] == "ORGANIZATION"]
    projections = [row for row in rows if row["target_type"] == "REPOSITORY"]
    assert len(authority) == 1
    assert authority[0]["evaluation_role"] == "AUTHORITATIVE_EVALUATION"
    assert "repository_path" not in authority[0]
    assert len(projections) == 2
    assert all(row["evaluation_role"] == "PROJECTION" for row in projections)


def test_generic_launcher_receives_file_evidence_and_neutralizes_projection(tmp_path):
    module_path, module_name = evaluator_module(tmp_path)
    registry = scope(tmp_path / "scope.json", module_name)
    result_root = tmp_path / "results"
    authority = run("run_registry_evaluator.py", "--root", str(ROOT), "--registry", str(registry), "--control-id", "EMS-CTRL-900", "--target-id", "ORG-TEST", "--target-type", "ORGANIZATION", "--evaluation-role", "AUTHORITATIVE_EVALUATION", "--organization-id", "org-test", "--evidence-provider-type", "FILE", "--evidence-provider-reference", str(FIXTURES / "organization_evidence_example.json"), "--output-root", str(result_root), extra_path=module_path)
    assert authority.returncode == 0, authority.stderr
    result = json.loads((result_root / "EMS-CTRL-900/ORG-TEST/result.json").read_text())
    evidence = json.loads((result_root / "EMS-CTRL-900/ORG-TEST/evidence.json").read_text())
    assert result["result_state"] == "PASS"
    assert result["authoritative_compliance"] is True
    assert evidence[0]["provenance"]["evidence_provider"]["state"] == "AVAILABLE"
    repository = tmp_path / "repository"
    repository.mkdir()
    projection = run("run_registry_evaluator.py", "--root", str(ROOT), "--registry", str(registry), "--control-id", "EMS-CTRL-900", "--target-id", "REPO-001", "--target-type", "REPOSITORY", "--evaluation-role", "PROJECTION", "--repository-path", str(repository), "--github-repo", "org/repo", "--evidence-provider-type", "FILE", "--evidence-provider-reference", str(FIXTURES / "organization_evidence_example.json"), "--output-root", str(result_root), extra_path=module_path)
    assert projection.returncode == 0, projection.stderr
    projection_result = json.loads((result_root / "EMS-CTRL-900/REPO-001/result.json").read_text())
    assert projection_result["result_state"] == "WARNING"
    assert projection_result["authoritative_compliance"] is False


@pytest.mark.parametrize("content", [None, "not-json"])
def test_file_provider_failure_paths_reach_contract_native_warning(tmp_path, content):
    module_path, module_name = evaluator_module(tmp_path)
    registry = scope(tmp_path / "scope.json", module_name)
    reference = tmp_path / "evidence.json"
    if content is not None:
        reference.write_text(content)
    completed = run("run_registry_evaluator.py", "--root", str(ROOT), "--registry", str(registry), "--control-id", "EMS-CTRL-900", "--target-id", "ORG-TEST", "--target-type", "ORGANIZATION", "--evaluation-role", "AUTHORITATIVE_EVALUATION", "--organization-id", "org-test", "--evidence-provider-type", "FILE", "--evidence-provider-reference", str(reference), "--output-root", str(tmp_path / "results"), extra_path=module_path)
    assert completed.returncode == 0, completed.stderr
    result = json.loads((tmp_path / "results/EMS-CTRL-900/ORG-TEST/result.json").read_text())
    assert result["result_state"] == "WARNING"


def test_duplicate_authoritative_target_and_malformed_target_fail_safely(tmp_path):
    module_path, module_name = evaluator_module(tmp_path)
    del module_path, module_name
    ems = tmp_path / "ems"
    matrix = ems / "generated/wave2d/evaluation-matrix"
    matrix.mkdir(parents=True)
    matrix.joinpath("evaluation_matrix.csv").write_text("control_id,control_name,target_id,repository_name,applicability_state\nEMS-CTRL-900,Generic target,REPO-001,repo,APPLICABLE\n")
    identity = tmp_path / "identity.json"; identity.write_text(json.dumps({"repositories": {"REPO-001": {"github_repo": "org/repo"}}}))
    override = tmp_path / "override.json"; override.write_text(json.dumps({"REPO-001": {"repository_path": str(tmp_path)}}))
    run_identity = tmp_path / "run.json"; run_identity.write_text(json.dumps({"batch_id": "BATCH-X", "request_path": str(tmp_path / "requests.jsonl")}))
    targets = tmp_path / "targets.json"; targets.write_text(json.dumps({"organization_targets": [{"target_id": "ORG-TEST", "organization_id": "org-test"}]}))
    applicability = tmp_path / "applicability.json"; applicability.write_text(json.dumps({"organization_authoritative_controls": [{"control_id": "EMS-CTRL-900", "organization_target_ids": ["ORG-TEST", "ORG-TEST"], "authoritative_target_count": 1}]}))
    completed = run("build_wave2d_batch_requests_scoped.py", "--ems-root", str(ems), "--run-identity", str(run_identity), "--repository-map", str(identity), "--repository-path-overrides", str(override), "--organization-targets", str(targets), "--runtime-applicability", str(applicability))
    assert completed.returncode != 0
    malformed = run("run_registry_evaluator.py", "--root", str(ROOT), "--registry", str(scope(tmp_path / "scope.json", "missing")), "--control-id", "EMS-CTRL-900", "--target-id", "ORG-TEST", "--target-type", "ORGANIZATION", "--evaluation-role", "AUTHORITATIVE_EVALUATION", "--output-root", str(tmp_path / "result"))
    assert malformed.returncode != 0


def test_batch_wrapper_keeps_failure_cleanup_contract():
    content = (SCRIPTS / "Run-Wave2DImmutableBatch.ps1").read_text()
    assert "finally" in content
    assert "active_runtime_registry.json" in content
    assert "Move-Item -LiteralPath $backup -Destination $active -Force" in content