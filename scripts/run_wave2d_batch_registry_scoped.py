"""Evaluate immutable batch requests using an explicitly supplied scoped runtime registry."""
import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path


def load(path: str) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def flatten(registry: dict) -> dict:
    return {control_id: {**metadata, "family": family_name} for family_name, family in registry["families"].items() for control_id, metadata in family.get("controls", {}).items()}


def invocation(root: Path, registry: Path, runner: Path, request: dict, result_root: Path) -> list[str]:
    command = [sys.executable, str(runner.resolve()), "--root", str(root), "--registry", str(registry.resolve()), "--control-id", request["control_id"], "--target-id", request["target_id"], "--target-type", request.get("target_type", "REPOSITORY"), "--evaluation-role", request.get("evaluation_role", "AUTHORITATIVE_EVALUATION"), "--output-root", str(result_root)]
    optional = {"repository_path": "--repository-path", "github_repo": "--github-repo", "organization_id": "--organization-id", "organization_name": "--organization-name", "evidence_provider_type": "--evidence-provider-type", "evidence_provider_reference": "--evidence-provider-reference", "evidence_authority": "--evidence-authority", "evidence_timestamp": "--evidence-timestamp"}
    for key, flag in optional.items():
        if request.get(key) not in (None, ""):
            command.extend([flag, str(request[key])])
    return command


parser = argparse.ArgumentParser()
parser.add_argument("--root", required=True)
parser.add_argument("--run-identity", required=True)
parser.add_argument("--registry", required=True)
parser.add_argument("--runner", required=True)
args = parser.parse_args()
root = Path(args.root).resolve()
run = load(args.run_identity)
controls = flatten(load(args.registry))
requests = [json.loads(line) for line in Path(run["request_path"]).read_text(encoding="utf-8-sig").splitlines() if line]
rows = []
result_root = Path(run["results_root"])
result_root.mkdir(parents=True, exist_ok=True)
for request in requests:
    binding = controls.get(request.get("control_id"))
    common = {"batch_id": run["batch_id"], "control_id": request.get("control_id"), "target_id": request.get("target_id"), "target_type": request.get("target_type", "REPOSITORY"), "evaluation_role": request.get("evaluation_role", "AUTHORITATIVE_EVALUATION")}
    if request["status"] != "READY" or binding is None or not binding.get("supported"):
        rows.append({**common, "execution_state": "BLOCKED", "reason": request.get("reason") or "control unsupported by scoped runtime registry"})
        continue
    completed = subprocess.run(invocation(root, Path(args.registry), Path(args.runner), request, result_root), cwd=root, capture_output=True, text=True, check=False)
    destination = result_root / request["control_id"] / request["target_id"]
    evidence, result = destination / "evidence.json", destination / "result.json"
    if completed.returncode or not evidence.exists() or not result.exists():
        rows.append({**common, "execution_state": "BLOCKED", "reason": "registry evaluator failed or incomplete", "return_code": completed.returncode, "stderr_tail": completed.stderr[-2000:]})
        continue
    result_value = load(str(result))
    rows.append({**common, "execution_state": "COMPLETE", "family": binding["family"], "evaluation_state": result_value.get("evaluation_state"), "evidence_state": result_value.get("evidence_state"), "result_state": result_value.get("result_state"), "promotion_state": result_value.get("promotion_state"), "authoritative_compliance": result_value.get("authoritative_compliance"), "evidence_sha256": sha(evidence), "result_sha256": sha(result)})
summary = {"component": "Hayes Verify", "phase": "Wave 2D Immutable Batch Evaluation", "status": "PASS", "batch_id": run["batch_id"], "row_count": len(rows), "complete_count": sum(row["execution_state"] == "COMPLETE" for row in rows), "blocked_count": sum(row["execution_state"] == "BLOCKED" for row in rows), "result_counts": {}, "rows": rows}
for row in rows:
    state = row.get("result_state") or "BLOCKED"
    summary["result_counts"][state] = summary["result_counts"].get(state, 0) + 1
Path(run["summary_path"]).write_text(json.dumps(summary, indent=2), encoding="utf-8")
print(json.dumps({key: summary[key] for key in ("status", "batch_id", "complete_count", "blocked_count", "result_counts")}, indent=2))