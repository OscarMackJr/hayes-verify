import argparse
import json
from pathlib import Path

EXPECTED_COUNT = 4


def load(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


ap = argparse.ArgumentParser()
ap.add_argument("--candidate-registry", required=True)
ap.add_argument("--rules", required=True)
ap.add_argument("--output", required=True)
args = ap.parse_args()

planning = load(args.candidate_registry)
rules = load(args.rules).get("rules", {})

enabled = []
runtime_controls = {}

for control_id, meta in planning["controls"].items():
    if (
        meta.get("family") == "test_quality"
        and meta.get("implementation_state")
        == "IMPLEMENTED_PENDING_BATCH_VERIFICATION"
    ):
        rule = rules.get(control_id)
        if not rule or not rule.get("supported"):
            raise SystemExit(
                f"missing supported test_quality rule for {control_id}"
            )

        evidence_type = rule.get("evidence_type")
        if not evidence_type:
            raise SystemExit(f"missing evidence_type for {control_id}")

        runtime_controls[control_id] = {
            "collector": "repository_and_workflow",
            "evaluator": "test_quality",
            "evidence_type": evidence_type,
            "scope": "repository",
            "supported": True,
            "implementation_state": "IMPLEMENTED_PENDING_BATCH_VERIFICATION",
        }
        enabled.append(control_id)

if len(enabled) != EXPECTED_COUNT:
    raise SystemExit(
        f"expected {EXPECTED_COUNT} test_quality controls, found {len(enabled)}"
    )

runtime = {
    "registry_version": "1.6-batch-verification",
    "wave": "2D",
    "default_behavior": "BLOCKED_UNSUPPORTED",
    "verification_scope": {
        "family": "test_quality",
        "control_ids": sorted(enabled),
    },
    "families": {
        "test_quality": {
            "description": "Priority-2 test-quality verification runtime registry.",
            "implementation": "hayes_verify.evaluator_families.test_quality",
            "controls": dict(sorted(runtime_controls.items())),
        }
    },
}

out = Path(args.output)
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps(runtime, indent=2), encoding="utf-8")

print(
    json.dumps(
        {
            "status": "PASS",
            "runtime_registry_shape": "families",
            "family": "test_quality",
            "enabled_control_count": len(enabled),
            "enabled_controls": sorted(enabled),
        },
        indent=2,
    )
)
