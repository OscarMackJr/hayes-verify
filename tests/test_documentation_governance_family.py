import json
from pathlib import Path

from hayes_verify.evaluator_families.documentation_governance import evaluate_rule


def test_ems_authority_boundary_requires_human_review(tmp_path: Path):
    rules = tmp_path / "rules.json"
    rules.write_text(json.dumps({"rules": {"EMS-CTRL-067": {"supported": True, "evidence_type": "X", "evidence_authority": "EMS evidence", "ems_requirement_source": "x", "assertions": ["metadata_status_detected"]}}}))
    _, result = evaluate_rule("EMS-CTRL-067", tmp_path, rules)
    assert result["result_state"] == "WARNING"
    assert result["evidence_state"] == "INSUFFICIENT"
