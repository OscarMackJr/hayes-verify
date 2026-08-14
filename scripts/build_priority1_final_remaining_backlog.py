import argparse
import json
from collections import defaultdict
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


ap = argparse.ArgumentParser()
ap.add_argument("--registry", required=True)
ap.add_argument("--backlog-output", required=True)
ap.add_argument("--plan-output", required=True)
args = ap.parse_args()

registry = load(args.registry)

if registry.get("registry_version") != "1.2":
    raise SystemExit("expected registry_version=1.2")
if registry.get("status") != "CANDIDATE_FROZEN":
    raise SystemExit("expected status=CANDIDATE_FROZEN")
if len(registry.get("controls", {})) != 80:
    raise SystemExit("expected 80 controls")

items = []

for control_id, meta in registry["controls"].items():
    family = meta.get("family")
    state = meta.get("implementation_state")

    if family not in PRIORITY1_FAMILIES:
        continue
    if state == "IMPLEMENTED":
        continue
    if state not in {"PLANNED_AUTOMATED", "PLANNED_HYBRID"}:
        continue

    items.append(
        {
            "control_id": control_id,
            "control_name": meta.get("control_name", ""),
            "family": family,
            "implementation_state": state,
            "supported": bool(meta.get("supported", False)),
            "decision_source": meta.get("decision_source"),
            "implementation_priority": 1,
        }
    )

items.sort(key=lambda row: (row["family"], row["control_id"]))

groups = defaultdict(list)
for item in items:
    groups[item["family"]].append(item)

backlog = {
    "status": "PASS",
    "source_registry_version": "1.2",
    "source_registry_state": registry["status"],
    "priority": 1,
    "remaining_control_count": len(items),
    "items": items,
}

plan = {
    "status": "PASS",
    "priority": 1,
    "remaining_family_count": len(groups),
    "families": [
        {
            "family": family,
            "control_count": len(rows),
            "controls": [row["control_id"] for row in rows],
            "implementation_strategy": "IMPLEMENT_TEST_BATCH_VERIFY",
        }
        for family, rows in sorted(groups.items())
    ],
}

Path(args.backlog_output).parent.mkdir(parents=True, exist_ok=True)
Path(args.backlog_output).write_text(json.dumps(backlog, indent=2), encoding="utf-8")
Path(args.plan_output).write_text(json.dumps(plan, indent=2), encoding="utf-8")

print(
    json.dumps(
        {
            "status": "PASS",
            "remaining_control_count": len(items),
            "remaining_family_count": len(groups),
            "families": {k: len(v) for k, v in sorted(groups.items())},
        },
        indent=2,
    )
)
