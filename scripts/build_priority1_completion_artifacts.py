import argparse
import hashlib
import json
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path

PRIORITY1_FAMILIES = {
    "github_branch_policy",
    "github_security_configuration",
    "github_security_monitoring",
    "github_workflow_ci",
    "repository_filesystem",
}


def load(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def sha(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


ap = argparse.ArgumentParser()
ap.add_argument("--registry", required=True)
ap.add_argument("--source-certification", required=True)
ap.add_argument("--verification", required=True)
ap.add_argument("--backlog-output", required=True)
ap.add_argument("--completion-certification-output", required=True)
ap.add_argument("--completion-manifest-output", required=True)
args = ap.parse_args()

registry_path = Path(args.registry)
cert_path = Path(args.source_certification)
verification_path = Path(args.verification)

registry = load(registry_path)
source_cert = load(cert_path)
verification = load(verification_path)

if registry.get("registry_version") != "1.4":
    raise SystemExit("expected registry_version=1.4")
if registry.get("status") != "CANDIDATE_FROZEN":
    raise SystemExit("expected registry status=CANDIDATE_FROZEN")
if len(registry.get("controls", {})) != 80:
    raise SystemExit("expected 80 controls")

remaining = []
implemented_priority1 = []

for control_id, meta in registry["controls"].items():
    family = meta.get("family")
    if family not in PRIORITY1_FAMILIES:
        continue

    state = meta.get("implementation_state")
    row = {
        "control_id": control_id,
        "control_name": meta.get("control_name", ""),
        "family": family,
        "implementation_state": state,
        "supported": bool(meta.get("supported", False)),
    }

    if state == "IMPLEMENTED":
        implemented_priority1.append(row)
    elif state in {"PLANNED_AUTOMATED", "PLANNED_HYBRID", "IMPLEMENTED_PENDING_BATCH_VERIFICATION"}:
        remaining.append(row)

remaining.sort(key=lambda r: (r["family"], r["control_id"]))
implemented_priority1.sort(key=lambda r: (r["family"], r["control_id"]))

if remaining:
    raise SystemExit(
        "Priority-1 is not complete; remaining controls: "
        + ", ".join(r["control_id"] for r in remaining)
    )

backlog = {
    "status": "PASS",
    "priority": 1,
    "source_registry_version": "1.4",
    "completion_state": "COMPLETE",
    "remaining_control_count": 0,
    "remaining_controls": [],
}

backlog_path = Path(args.backlog_output)
backlog_path.parent.mkdir(parents=True, exist_ok=True)
backlog_path.write_text(json.dumps(backlog, indent=2), encoding="utf-8")

state_counts = Counter(
    meta["implementation_state"]
    for meta in registry["controls"].values()
)

completion_cert = {
    "component": "Hayes Verify",
    "phase": "Wave 2D Priority-1 Evaluator Completion Certification",
    "certified_at_utc": datetime.now(UTC).isoformat(),
    "status": "PASS",
    "wave": "2D",
    "priority": 1,
    "completion_state": "COMPLETE",
    "registry_version": "1.4",
    "verification_batch_id": verification["batch_id"],
    "implemented_priority1_control_count": len(implemented_priority1),
    "remaining_priority1_control_count": 0,
    "registry_sha256": sha(registry_path),
    "verification_sha256": sha(verification_path),
    "source_certification_sha256": sha(cert_path),
    "zero_backlog_sha256": sha(backlog_path),
    "implementation_state_counts": dict(state_counts),
    "errors": [],
}

completion_cert_path = Path(args.completion_certification_output)
completion_cert_path.parent.mkdir(parents=True, exist_ok=True)
completion_cert_path.write_text(
    json.dumps(completion_cert, indent=2),
    encoding="utf-8",
)

manifest = {
    "component": "Hayes Verify",
    "phase": "Wave 2D Priority-1 Completion Manifest",
    "created_at_utc": datetime.now(UTC).isoformat(),
    "status": "PASS",
    "registry_version": "1.4",
    "priority1_completion_state": "COMPLETE",
    "verification_batch_id": verification["batch_id"],
    "artifacts": [
        {"path": str(registry_path), "sha256": sha(registry_path)},
        {"path": str(cert_path), "sha256": sha(cert_path)},
        {"path": str(verification_path), "sha256": sha(verification_path)},
        {"path": str(backlog_path), "sha256": sha(backlog_path)},
        {
            "path": str(completion_cert_path),
            "sha256": sha(completion_cert_path),
        },
    ],
}

manifest_path = Path(args.completion_manifest_output)
manifest_path.parent.mkdir(parents=True, exist_ok=True)
manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

print(json.dumps({
    "status": "PASS",
    "priority1_completion_state": "COMPLETE",
    "remaining_priority1_control_count": 0,
    "implemented_priority1_control_count": len(implemented_priority1),
    "registry_version": "1.4",
}, indent=2))
