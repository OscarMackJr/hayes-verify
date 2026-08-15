from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


def _sha(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


def evaluate_rule(control_id: str, repository_path: Path, rules_path: Path):
    rule = json.loads(rules_path.read_text(encoding="utf-8-sig"))["rules"].get(control_id)
    if not rule or not rule.get("supported"):
        raise ValueError(f"documentation_governance rule not implemented for {control_id}")
    now = datetime.now(UTC).isoformat()
    observation = {
        "control_id": control_id,
        "repository_path": str(repository_path),
        "evidence_authority": rule["evidence_authority"],
        "ems_requirement_source": rule["ems_requirement_source"],
        "assertions": rule["assertions"],
        "reason": "Authoritative EMS/organizational evidence is not deterministically available through repository inspection.",
    }
    text = json.dumps(observation, sort_keys=True)
    evidence_id = f"DOC-{control_id}-{_sha(text)[:16]}"
    evidence = [{
        "contract_version": "1.0", "wave": "2D", "evidence_id": evidence_id,
        "control_id": control_id, "evidence_type": rule["evidence_type"],
        "source": f"repository:{repository_path}", "collected_at_utc": now,
        "sha256": _sha(text), "observation": text, "sensitive": False,
        "provenance": {"collector": "hayes-verify", "collector_version": "0.1.0", "repository_path_or_url": str(repository_path), "collected_at_utc": now, "command_or_method": "documentation-governance authority boundary inspection", "tool_versions": {}},
    }]
    result = {
        "contract_version": "1.0", "wave": "2D", "evaluation_state": "COMPLETE",
        "evidence_state": "INSUFFICIENT", "result_state": "WARNING", "evaluated_at_utc": now,
        "evidence_ids": [evidence_id],
        "rationale": "HUMAN_REVIEW required: repository evidence cannot establish EMS/organizational documentation-governance compliance.",
        "assertions": [{"assertion_id": "authoritative_ems_evidence_requires_human_review", "result": "WARNING", "detail": text}],
        "promotion_state": "NOT_PROMOTED",
    }
    return evidence, result


def run(bundle, request: dict[str, Any], repository_path: Path, github_repo: str):
    del github_repo
    root = getattr(bundle, "root", None) or Path.cwd()
    evidence, result = evaluate_rule(request["control_id"], repository_path, Path(root) / "registry" / "documentation_governance_rules.json")
    for item in evidence:
        item.update({"request_id": request["request_id"], "target_id": request["target_id"]})
    result.update({"request_id": request["request_id"], "control_id": request["control_id"], "target_id": request["target_id"]})
    bundle.validate_result(result)
    return evidence, result
