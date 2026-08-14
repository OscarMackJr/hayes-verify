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

if registry.get("status") != "FROZEN":
    raise SystemExit("registry status is not FROZEN")
if registry.get("control_count") != 80:
    raise SystemExit("expected frozen registry control_count=80")

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

    items.append({
        "control_id": control_id,
        "control_name": meta.get("control_name", ""),
        "family": family,
        "implementation_state": state,
        "supported": bool(meta.get("supported", False)),
        "decision_source": meta.get("decision_source"),
        "decision_owner": meta.get("decision_owner"),
        "decision_rationale": meta.get("decision_rationale"),
        "implementation_priority": 1,
    })

items.sort(key=lambda r: (r["family"], r["control_id"]))

backlog = {
    "status": "PASS",
    "source_registry_version": registry["registry_version"],
    "source_registry_state": registry["status"],
    "priority": 1,
    "control_count": len(items),
    "items": items,
}

groups = defaultdict(list)
for item in items:
    groups[item["family"]].append(item)

plan = {
    "status": "PASS",
    "priority": 1,
    "family_count": len(groups),
    "families": [
        {
            "family": family,
            "control_count": len(rows),
            "controls": [r["control_id"] for r in rows],
            "implementation_strategy": "IMPLEMENT_AND_TEST_FAMILY_ADAPTER_THEN_ENABLE_CONTROLS",
        }
        for family, rows in sorted(groups.items())
    ],
}

Path(args.backlog_output).parent.mkdir(parents=True, exist_ok=True)
Path(args.backlog_output).write_text(json.dumps(backlog, indent=2), encoding="utf-8")
Path(args.plan_output).write_text(json.dumps(plan, indent=2), encoding="utf-8")

print(json.dumps({
    "status": "PASS",
    "priority1_control_count": len(items),
    "priority1_family_count": len(groups),
    "families": {k: len(v) for k, v in sorted(groups.items())},
}, indent=2))
