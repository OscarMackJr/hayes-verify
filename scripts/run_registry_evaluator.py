"""Invoke one evaluator-registry binding and persist its result contract."""
import argparse
import json
from datetime import UTC, datetime
from pathlib import Path

from hayes_verify.contracts import ContractBundle
from hayes_verify.evaluator_registry import EvaluatorRegistry
from hayes_verify.wave2d_targets import (
    normalize_result_authority,
    resolve_evidence_provider,
    validate_target,
)


def write_json(path: Path, value: dict | list) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2), encoding="utf-8")


parser = argparse.ArgumentParser()
parser.add_argument("--root", required=True)
parser.add_argument("--registry", required=True)
parser.add_argument("--control-id", required=True)
parser.add_argument("--target-id", required=True)
parser.add_argument("--target-type", default="REPOSITORY")
parser.add_argument("--evaluation-role", default="AUTHORITATIVE_EVALUATION")
parser.add_argument("--repository-path")
parser.add_argument("--github-repo")
parser.add_argument("--archive-source-sha256")
parser.add_argument("--organization-id")
parser.add_argument("--organization-name")
parser.add_argument("--evidence-provider-type")
parser.add_argument("--evidence-provider-reference")
parser.add_argument("--evidence-authority")
parser.add_argument("--evidence-timestamp")
parser.add_argument("--output-root", required=True)
args = parser.parse_args()
root = Path(args.root).resolve()
target = {"target_id": args.target_id, "target_type": args.target_type, "evaluation_role": args.evaluation_role, "repository_path": args.repository_path, "organization_id": args.organization_id, "archive_source_sha256": args.archive_source_sha256}
validate_target(target)
bundle = ContractBundle(root)
binding, runner = EvaluatorRegistry(Path(args.registry)).load_callable(args.control_id)
request = {"contract_version": "1.0", "wave": "2D", "request_id": f"BATCH-{args.control_id}-{args.target_id}", "control_id": args.control_id, "target_id": args.target_id, "target_type": args.target_type, "evaluation_role": args.evaluation_role, "applicability_state": "APPLICABLE", "requested_at_utc": datetime.now(UTC).isoformat(), "requested_evidence_types": [binding.evidence_type]}
if args.target_type == "REPOSITORY":
    request["repository_name"] = (args.github_repo or args.target_id).rsplit("/", 1)[-1]
elif args.target_type == "ARCHIVED_REPOSITORY_SNAPSHOT":
    request.update({"archive_source_sha256": args.archive_source_sha256, "archive_evidence_source_class": "ARCHIVE_REPOSITORY_CONTENT"})
else:
    request.update({"organization_id": args.organization_id, "organization_name": args.organization_name or args.organization_id})
request.update({"evidence_provider_type": args.evidence_provider_type, "evidence_provider_reference": args.evidence_provider_reference, "evidence_authority": args.evidence_authority, "evidence_timestamp": args.evidence_timestamp})
payload, provider_provenance = resolve_evidence_provider(request)
request["evidence_payload"] = payload
request["evidence_provider_provenance"] = provider_provenance
evidence, result = runner(bundle, request, Path(args.repository_path) if args.repository_path else None, args.github_repo or "")
result.update({"request_id": request["request_id"], "control_id": request["control_id"], "target_id": request["target_id"]})
normalize_result_authority(request, result)
for item in evidence:
    item.setdefault("provenance", {})["evidence_provider"] = provider_provenance
bundle.validate_result(result)
out = Path(args.output_root) / args.control_id / args.target_id
write_json(out / "evidence.json", evidence)
write_json(out / "result.json", result)
print(json.dumps({"status": "PASS", "control_id": args.control_id, "target_id": args.target_id, "target_type": args.target_type, "evaluation_role": args.evaluation_role, "family": binding.family, "evidence_type": binding.evidence_type, "result_state": result.get("result_state")}, indent=2))
