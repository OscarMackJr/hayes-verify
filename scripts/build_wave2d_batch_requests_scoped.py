"""Build immutable Wave 2D requests from frozen applicability plus additive runtime targets."""
import argparse
import csv
import json
from pathlib import Path


def load(path: str | None) -> dict:
    if not path:
        return {}
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def organization_targets(document: dict) -> dict[str, dict]:
    return {item["target_id"]: item for item in document.get("organization_targets", [])}


def configured_controls(document: dict) -> dict[str, dict]:
    controls: dict[str, dict] = {}
    for item in document.get("organization_authoritative_controls", []):
        control_id = item["control_id"]
        target_ids = item.get("organization_target_ids", [])
        if len(target_ids) != len(set(target_ids)):
            raise ValueError(f"duplicate organization authoritative target configured for {control_id}")
        expected = item.get("authoritative_target_count")
        if expected is not None and len(target_ids) != expected:
            raise ValueError(f"organization authoritative target count does not match configuration for {control_id}")
        controls[control_id] = {"target_ids": target_ids, "expected_count": expected}
    return controls


def build_requests(ems: Path, run: dict, identities: dict, overrides: dict, targets: dict, applicability: dict, evidence_overrides: dict) -> list[dict]:
    matrix = next((path for path in (ems / "generated/wave2d/evaluation-matrix/evaluation_matrix_adjudicated.csv", ems / "generated/wave2d/evaluation-matrix/evaluation_matrix.csv") if path.exists()), None)
    if matrix is None:
        raise ValueError("Wave 2D applicability matrix not found")
    control_targets = configured_controls(applicability)
    projection_controls = set(applicability.get("repository_projection_controls", []))
    applicable_controls: set[str] = set()
    rows: list[dict] = []
    with matrix.open("r", encoding="utf-8-sig", newline="") as handle:
        for row in csv.DictReader(handle):
            if (row.get("applicability_state") or "").strip().upper() != "APPLICABLE":
                continue
            control_id = row.get("control_id")
            applicable_controls.add(control_id)
            target_id = row.get("target_id")
            identity = identities.get(target_id) or identities.get(row.get("repository_name"))
            override = overrides.get(target_id) or overrides.get(row.get("repository_name"))
            request = {
                "batch_id": run["batch_id"], "wave": "2D", "control_id": control_id,
                "control_name": row.get("control_name"), "target_id": target_id,
                "target_type": "REPOSITORY",
                "evaluation_role": "PROJECTION" if control_id in projection_controls else "AUTHORITATIVE_EVALUATION",
                "repository_name": row.get("repository_name"),
            }
            if not identity or not override or not override.get("repository_path"):
                request.update({"status": "BLOCKED", "reason": "controlled repository identity or local path override missing"})
            else:
                request.update({
                    "status": "READY", "request_id": f"{run['batch_id']}-{control_id}-{target_id}",
                    "repository_path": override["repository_path"], "github_repo": identity["github_repo"],
                })
            rows.append(request)
    for control_id, target_configuration in control_targets.items():
        target_ids = target_configuration["target_ids"]
        if control_id not in applicable_controls:
            continue
        for target_id in target_ids:
            target = targets.get(target_id)
            if not target:
                rows.append({"batch_id": run["batch_id"], "status": "BLOCKED", "control_id": control_id, "target_id": target_id, "target_type": "ORGANIZATION", "evaluation_role": "AUTHORITATIVE_EVALUATION", "reason": "organization target identity missing"})
                continue
            provider = evidence_overrides.get(target_id, {})
            rows.append({
                "batch_id": run["batch_id"], "status": "READY", "wave": "2D",
                "request_id": f"{run['batch_id']}-{control_id}-{target_id}",
                "control_id": control_id, "target_id": target_id, "target_type": "ORGANIZATION",
                "evaluation_role": "AUTHORITATIVE_EVALUATION", "organization_id": target["organization_id"],
                "organization_name": target.get("organization_name", target["organization_id"]),
                "evidence_provider_type": provider.get("evidence_provider_type"),
                "evidence_provider_reference": provider.get("evidence_provider_reference"),
                "evidence_authority": provider.get("evidence_authority", target.get("evidence_authority_type")),
                "evidence_timestamp": provider.get("evidence_timestamp"),
            })
    return rows


parser = argparse.ArgumentParser()
parser.add_argument("--ems-root", required=True)
parser.add_argument("--run-identity", required=True)
parser.add_argument("--repository-map", required=True)
parser.add_argument("--repository-path-overrides", required=True)
parser.add_argument("--organization-targets")
parser.add_argument("--runtime-applicability")
parser.add_argument("--organization-evidence-overrides")
args = parser.parse_args()
ems = Path(args.ems_root).resolve()
run = load(args.run_identity)
identity_document = load(args.repository_map)
identities = identity_document.get("repositories", identity_document)
rows = build_requests(ems, run, identities, load(args.repository_path_overrides), organization_targets(load(args.organization_targets)), load(args.runtime_applicability), load(args.organization_evidence_overrides))
out = Path(run["request_path"])
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")
print(json.dumps({"status": "PASS", "batch_id": run["batch_id"], "request_count": len(rows), "ready_count": sum(row["status"] == "READY" for row in rows), "blocked_count": sum(row["status"] == "BLOCKED" for row in rows)}, indent=2))