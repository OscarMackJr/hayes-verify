"""Invoke one evaluator-registry binding and persist its result contract."""
import argparse
import json
from datetime import UTC, datetime
from pathlib import Path

from hayes_verify.contracts import ContractBundle
from hayes_verify.evaluator_registry import EvaluatorRegistry


def write_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2), encoding="utf-8")


parser = argparse.ArgumentParser()
parser.add_argument("--root", required=True)
parser.add_argument("--registry", required=True)
parser.add_argument("--control-id", required=True)
parser.add_argument("--target-id", required=True)
parser.add_argument("--repository-path", required=True)
parser.add_argument("--github-repo", required=True)
parser.add_argument("--output-root", required=True)
args = parser.parse_args()
root = Path(args.root).resolve()
bundle = ContractBundle(root)
binding, runner = EvaluatorRegistry(Path(args.registry)).load_callable(args.control_id)
request = {"contract_version": "1.0", "wave": "2D", "request_id": f"BATCH-{args.control_id}-{args.target_id}", "control_id": args.control_id, "target_id": args.target_id, "repository_name": args.github_repo.rsplit("/", 1)[-1], "applicability_state": "APPLICABLE", "requested_at_utc": datetime.now(UTC).isoformat(), "requested_evidence_types": [binding.evidence_type]}
evidence, result = runner(bundle, request, Path(args.repository_path), args.github_repo)
out = Path(args.output_root) / args.control_id / args.target_id
write_json(out / "evidence.json", evidence)
write_json(out / "result.json", result)
print(json.dumps({"status": "PASS", "control_id": args.control_id, "target_id": args.target_id, "family": binding.family, "evidence_type": binding.evidence_type, "result_state": result.get("result_state")}, indent=2))