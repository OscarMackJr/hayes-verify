import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).parents[1]
SCRIPTS = ROOT / "scripts"


def run(script, *args, cwd=None):
    env = {**os.environ, "PYTHONPATH": str(ROOT / "src")}
    return subprocess.run([sys.executable, str(SCRIPTS / script), *args], cwd=cwd or ROOT, env=env, text=True, capture_output=True, check=False)


def test_create_run_identity_is_unique_and_contract_valid(tmp_path):
    spec = tmp_path / "spec.json"
    spec.write_text(json.dumps({"wave": "2D", "run_root": "runs", "latest_pointer": "latest.json", "request_filename": "requests.jsonl", "summary_filename": "summary.json", "results_dirname": "results"}))
    completed = run("create_wave2d_batch_run.py", "--root", str(tmp_path), "--spec", str(spec))
    assert completed.returncode == 0, completed.stderr
    identity = json.loads((tmp_path / "latest.json").read_text())
    assert identity["batch_id"].startswith("BATCH-")
    assert Path(identity["request_path"]).name == "requests.jsonl"


def test_request_builder_requires_local_path_override(tmp_path):
    ems = tmp_path / "ems"
    matrix = ems / "generated/wave2d/evaluation-matrix"
    matrix.mkdir(parents=True)
    (matrix / "evaluation_matrix.csv").write_text("control_id,control_name,target_id,repository_name,applicability_state\nEMS-CTRL-001,Control,REPO-001,repo,APPLICABLE\n")
    request = tmp_path / "requests.jsonl"
    run_identity = tmp_path / "run.json"
    run_identity.write_text(json.dumps({"batch_id": "BATCH-X", "request_path": str(request)}))
    identities = tmp_path / "identities.json"
    identities.write_text(json.dumps({"repositories": {"REPO-001": {"repository_name": "repo", "github_repo": "org/repo"}}}))
    overrides = tmp_path / "overrides.json"
    overrides.write_text("{}")
    completed = run("build_wave2d_batch_requests_scoped.py", "--ems-root", str(ems), "--run-identity", str(run_identity), "--repository-map", str(identities), "--repository-path-overrides", str(overrides))
    assert completed.returncode == 0, completed.stderr
    row = json.loads(request.read_text().strip())
    assert row["status"] == "BLOCKED"
    assert "override" in row["reason"]


def test_scoped_runtime_blocks_unknown_controls(tmp_path):
    request = tmp_path / "requests.jsonl"
    request.write_text(json.dumps({"status": "READY", "control_id": "EMS-CTRL-UNKNOWN", "target_id": "REPO-001"}) + "\n")
    summary = tmp_path / "summary.json"
    run_identity = tmp_path / "run.json"
    run_identity.write_text(json.dumps({"batch_id": "BATCH-X", "request_path": str(request), "results_root": str(tmp_path / "results"), "summary_path": str(summary)}))
    registry = tmp_path / "registry.json"
    registry.write_text(json.dumps({"families": {}}))
    completed = run("run_wave2d_batch_registry_scoped.py", "--root", str(ROOT), "--run-identity", str(run_identity), "--registry", str(registry), "--runner", str(SCRIPTS / "run_registry_evaluator.py"))
    assert completed.returncode == 0, completed.stderr
    row = json.loads(summary.read_text())["rows"][0]
    assert row["execution_state"] == "BLOCKED"


def test_batch_wrapper_has_explicit_python_resolution_and_restoration():
    content = (SCRIPTS / "Run-Wave2DImmutableBatch.ps1").read_text()
    assert "-PythonPath" in content
    assert "Resolve-HayesPython" in content
    assert "finally" in content
    assert "active_runtime_registry.json" in content
    assert "wave2d_evaluator_registry.json" not in content


def test_controlled_repository_map_has_no_local_paths():
    document = json.loads((ROOT / "registry/wave2d_repository_map.json").read_text())
    assert document["local_path_overrides_required"] is True
    assert all("repository_path" not in item for item in document["repositories"].values())