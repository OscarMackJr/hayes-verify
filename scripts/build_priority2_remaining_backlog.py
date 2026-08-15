import argparse
import json
from collections import defaultdict
from pathlib import Path


def load(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


ap = argparse.ArgumentParser()
ap.add_argument("--registry", required=True)
ap.add_argument("--source-plan", required=True)
ap.add_argument("--backlog-output", required=True)
ap.add_argument("--plan-output", required=True)
ap.add_argument("--summary-output", required=True)
args = ap.parse_args()

registry = load(args.registry)
source_plan = load(args.source_plan)

if registry.get("registry_version") not in {"1.6", "1.7", "1.8"}:
    raise SystemExit("expected registry_version=1.6, 1.7, or 1.8")
if registry.get("status") != "CANDIDATE_FROZEN":
    raise SystemExit("expected status=CANDIDATE_FROZEN")
if len(registry.get("controls", {})) != 80:
    raise SystemExit("expected 80 controls")

priority2_ids = []
priority2_family_by_id = {}
priority2_family_sequence = {}

for sequence, family in enumerate(source_plan.get("families", []), start=1):
    for cid in family.get("control_ids", []):
        priority2_ids.append(cid)
        priority2_family_by_id[cid] = family["family"]
        priority2_family_sequence[family["family"]] = sequence

if len(priority2_ids) != 21:
    raise SystemExit(
        f"expected 21 original Priority-2 controls, found {len(priority2_ids)}"
    )

remaining = []
implemented = []

for cid in priority2_ids:
    meta = registry["controls"].get(cid)
    if not meta:
        raise SystemExit(f"Priority-2 control missing from registry: {cid}")

    row = {
        "control_id": cid,
        "control_name": meta.get("control_name", ""),
        "family": priority2_family_by_id[cid],
        "implementation_state": meta.get("implementation_state"),
        "supported": bool(meta.get("supported", False)),
    }

    if meta.get("implementation_state") == "IMPLEMENTED":
        implemented.append(row)
    else:
        remaining.append(row)

remaining.sort(key=lambda r: (r["family"], r["control_id"]))
implemented.sort(key=lambda r: (r["family"], r["control_id"]))

groups = defaultdict(list)
for row in remaining:
    groups[row["family"]].append(row)

backlog = {
    "status": "PASS",
    "wave": "2D",
    "priority": 2,
    "source_registry_version": registry["registry_version"],
    "remaining_control_count": len(remaining),
    "implemented_priority2_control_count": len(implemented),
    "items": remaining,
}

plan = {
    "status": "PASS",
    "wave": "2D",
    "priority": 2,
    "source_registry_version": registry["registry_version"],
    "remaining_family_count": len(groups),
    "families": [
        {
            "sequence": index + 1,
            "family": family,
            "control_count": len(rows),
            "control_ids": [r["control_id"] for r in rows],
            "implementation_gate": (
                "IMPLEMENT_FAMILY -> UNIT_TEST -> COVERAGE_100_PERCENT "
                "-> IMMUTABLE_BATCH_VERIFY -> REGISTRY_PROMOTION"
            ),
        }
        for index, (family, rows) in enumerate(
            sorted(groups.items(), key=lambda kv: priority2_family_sequence[kv[0]])
        )
    ],
}

summary = {
    "status": "PASS",
    "wave": "2D",
    "priority": 2,
    "source_registry_version": registry["registry_version"],
    "original_priority2_control_count": len(priority2_ids),
    "implemented_priority2_control_count": len(implemented),
    "remaining_priority2_control_count": len(remaining),
    "remaining_family_count": len(groups),
    "family_counts": {
        family: len(rows)
        for family, rows in sorted(groups.items())
    },
    "first_family": plan["families"][0]["family"] if plan["families"] else None,
}

expected_implemented = 21 if registry["registry_version"] == "1.8" else 14 if registry["registry_version"] == "1.7" else 8
expected_remaining = 0 if registry["registry_version"] == "1.8" else 7 if registry["registry_version"] == "1.7" else 13

if len(implemented) != expected_implemented:
    raise SystemExit(
        f"expected {expected_implemented} implemented Priority-2 controls, found {len(implemented)}"
    )
if len(remaining) != expected_remaining:
    raise SystemExit(
        f"expected {expected_remaining} remaining Priority-2 controls, found {len(remaining)}"
    )
implemented_families = {"dependency_supply_chain", "test_quality"}
if registry["registry_version"] == "1.7":
    implemented_families.add("release_integrity")
if implemented_families & set(groups):
    raise SystemExit(
        "implemented Priority-2 families still appear in remaining backlog"
    )

for path, payload in (
    (args.backlog_output, backlog),
    (args.plan_output, plan),
    (args.summary_output, summary),
):
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(payload, indent=2), encoding="utf-8")

print(json.dumps(summary, indent=2))
