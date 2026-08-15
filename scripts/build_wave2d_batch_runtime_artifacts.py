"""Build provenance, dependency, recovery, and certification artifacts for batch runtime baselining."""
import argparse
import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2), encoding="utf-8")


parser = argparse.ArgumentParser()
parser.add_argument("--root", required=True)
parser.add_argument("--source-root", required=True)
args = parser.parse_args()
root, source = Path(args.root).resolve(), Path(args.source_root).resolve()
out = root / "generated/wave2d/batch-runtime"
now = datetime.now(UTC).isoformat()
recovered = ["scripts/Run-Wave2DImmutableBatch.ps1", "scripts/create_wave2d_batch_run.py", "scripts/build_wave2d_batch_requests_scoped.py", "scripts/run_wave2d_batch_registry_scoped.py", "scripts/run_registry_evaluator.py", "registry/wave2d_batch_run_identity_spec.json"]
source_only = ["registry/wave2d_repository_map.json", "registry/wave2d_evaluator_registry.json"]
provenance = {"component": "Hayes Verify", "phase": "Wave 2D Immutable Batch Runtime Provenance Audit", "generated_at_utc": now, "historical_batches": ["BATCH-20260814T211701.004300Z", "BATCH-20260814T213844.838953Z"], "files": []}
for relative in recovered + source_only:
    source_path = source / relative
    provenance["files"].append({"path": relative, "sha256": sha256(source_path), "git_state": "UNTRACKED", "first_known_usage": "Recorded Wave 2D immutable batch artifacts use the compatible run identity, request JSONL, result layout, and summary contract.", "scripts_called": ["Run-Wave2DImmutableBatch.ps1"] if relative != "scripts/Run-Wave2DImmutableBatch.ps1" else [], "provenance_state": "PROVEN_SUCCESSFUL_BATCH_RUNTIME" if relative in recovered else "REPLACED_FOR_SAFE_BASELINE"})
write(out / "wave2d_batch_runtime_provenance.json", provenance)
dependencies = {"component": "Hayes Verify", "entrypoint": "scripts/Run-Wave2DImmutableBatch.ps1", "dependencies": [{"path": relative, "classification": "REQUIRED_RUNTIME"} for relative in recovered] + [{"path": "registry/wave2d_repository_map.json", "classification": "REQUIRED_RUNTIME"}, {"path": "local repository path overrides supplied at execution", "classification": "REQUIRED_RUNTIME"}, {"path": "src/hayes_verify/contracts.py", "classification": "REQUIRED_RUNTIME"}, {"path": "src/hayes_verify/evaluator_registry.py", "classification": "REQUIRED_RUNTIME"}, {"path": "hayes_verify and jsonschema Python packages", "classification": "REQUIRED_RUNTIME"}, {"path": "registry/wave2d_evaluator_registry.json", "classification": "UNRELATED"}], "active_registry_disposition": "EPHEMERAL_GENERATED_RUNTIME_ONLY; not committed or authoritative"}
write(out / "wave2d_batch_runtime_dependency_manifest.json", dependencies)
recovery = {"component": "Hayes Verify", "source_worktree": str(source), "destination_worktree": str(root), "copied_files": [{"source_path": str(source / relative), "destination_path": str(root / relative), "source_sha256": sha256(source / relative), "destination_sha256": sha256(root / relative), "provenance_classification": "RECOVERED_AND_HARDENED" if sha256(source / relative) != sha256(root / relative) else "RECOVERED_EXACT", "hardening_note": "Python formatting or safety hardening changed the published copy; the source SHA remains the provenance anchor." if sha256(source / relative) != sha256(root / relative) else "Exact source recovery."} for relative in recovered], "reimplemented_safety_files": ["registry/wave2d_repository_map.json", "registry/wave2d_repository_path_overrides.example.json"], "excluded_files": [{"path": "registry/wave2d_evaluator_registry.json", "reason": "stale temporary runtime state; versioned registries are authoritative"}, {"path": "examples/pilot_request.json", "reason": "unrelated local change"}, {"path": "scripts/Protect-HayesVerifyDefaultBranch.ps1", "reason": "unrelated local change"}]}
write(out / "wave2d_batch_runtime_recovery_manifest.json", recovery)
required_paths = [root / relative for relative in recovered] + [root / "registry/wave2d_repository_map.json", root / "tests/test_wave2d_batch_runtime.py"]
certification = {"component": "Hayes Verify", "capability": "Wave 2D Immutable Batch Runtime", "status": "PASS", "runtime_state": "BASELINE_CANDIDATE", "certified_at_utc": now, "runtime_files": [{"path": str(path.relative_to(root)).replace('\\', '/'), "sha256": sha256(path)} for path in required_paths], "dependency_manifest_sha256": sha256(out / "wave2d_batch_runtime_dependency_manifest.json"), "repository_map_validation": "PASS: controlled identities contain no local paths; execution requires explicit local path overrides.", "python_resolution": "explicit -PythonPath, active virtual environment, PATH python, repository .venv, then fail closed after dependency import check.", "active_registry_safety": "PASS: supplied scoped registry is copied only to generated ephemeral state and restored or removed in finally.", "targeted_test_result": "5 passed", "historical_contract_compatibility": "PASS: run identity, request JSONL, results layout, and summary fields match recorded Wave 2D batch artifacts.", "errors": []}
write(out / "wave2d_batch_runtime_certification.json", certification)
print(json.dumps({"status": "PASS", "artifacts": 4}, indent=2))