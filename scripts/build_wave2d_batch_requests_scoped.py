"""Build immutable requests from EMS applicability and controlled repository identities."""
import argparse
import csv
import json
from pathlib import Path


def load(path: str) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


parser = argparse.ArgumentParser()
parser.add_argument("--ems-root", required=True)
parser.add_argument("--run-identity", required=True)
parser.add_argument("--repository-map", required=True)
parser.add_argument("--repository-path-overrides", required=True)
args = parser.parse_args()
ems = Path(args.ems_root).resolve()
run = load(args.run_identity)
identity_document = load(args.repository_map)
identities = identity_document.get("repositories", identity_document)
overrides = load(args.repository_path_overrides)
matrix = next((path for path in (ems / "generated/wave2d/evaluation-matrix/evaluation_matrix_adjudicated.csv", ems / "generated/wave2d/evaluation-matrix/evaluation_matrix.csv") if path.exists()), None)
if matrix is None:
    raise SystemExit("Wave 2D applicability matrix not found")
rows = []
with matrix.open("r", encoding="utf-8-sig", newline="") as handle:
    for row in csv.DictReader(handle):
        if (row.get("applicability_state") or "").strip().upper() != "APPLICABLE":
            continue
        target_id = row.get("target_id")
        identity = identities.get(target_id) or identities.get(row.get("repository_name"))
        override = overrides.get(target_id) or overrides.get(row.get("repository_name"))
        if not identity or not override or not override.get("repository_path"):
            rows.append({"batch_id": run["batch_id"], "status": "BLOCKED", "reason": "controlled repository identity or local path override missing", "control_id": row.get("control_id"), "target_id": target_id, "repository_name": row.get("repository_name")})
            continue
        rows.append({"batch_id": run["batch_id"], "status": "READY", "wave": "2D", "request_id": f"{run['batch_id']}-{row.get('control_id')}-{target_id}", "control_id": row.get("control_id"), "control_name": row.get("control_name"), "target_id": target_id, "repository_name": row.get("repository_name"), "repository_path": override["repository_path"], "github_repo": identity["github_repo"]})
out = Path(run["request_path"])
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")
print(json.dumps({"status": "PASS", "batch_id": run["batch_id"], "request_count": len(rows), "ready_count": sum(row["status"] == "READY" for row in rows), "blocked_count": sum(row["status"] == "BLOCKED" for row in rows)}, indent=2))