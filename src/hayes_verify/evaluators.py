from __future__ import annotations

from datetime import UTC, datetime


def evaluate_request(request: dict, evidence: list[dict]) -> dict:
    # Bootstrap evaluator: fail closed until control-specific evaluators are implemented.
    result_state = "WARNING" if evidence else "FAIL"
    evidence_state = "INSUFFICIENT"

    return {
        "contract_version": "1.0",
        "wave": "2D",
        "request_id": request["request_id"],
        "control_id": request["control_id"],
        "target_id": request["target_id"],
        "evaluation_state": "BLOCKED",
        "evidence_state": evidence_state,
        "result_state": result_state,
        "evaluated_at_utc": datetime.now(UTC).isoformat(),
        "evidence_ids": [x["evidence_id"] for x in evidence],
        "rationale": (
            "Bootstrap evaluator does not yet implement control-specific PASS logic; "
            "result is fail-closed."
        ),
        "assertions": [],
        "promotion_state": "NOT_PROMOTED",
    }
