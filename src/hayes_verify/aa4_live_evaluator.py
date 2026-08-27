"""Deterministic AA4 D8 evaluator for the thirteen approved projections."""
from __future__ import annotations

import json
from typing import Any


def evaluate(control_id: str, payloads: list[dict[str, Any]]) -> dict[str, str]:
    """Return PASS/FAIL only for complete approved projections; otherwise UNRESOLVED."""
    if not payloads:
        return {"result_status": "UNRESOLVED", "result_reason": "MISSING_SOURCE_PAYLOAD"}
    first = payloads[0]
    if control_id == "EMS-CTRL-009":
        passed = all(first.get(key) is not None for key in ("required_status_checks", "enforce_admins", "required_pull_request_reviews", "restrictions"))
    elif control_id == "EMS-CTRL-010":
        passed = first.get("required_approving_review_count", 0) >= 1
    elif control_id == "EMS-CTRL-011":
        passed = bool(first) and len(payloads) > 1 and bool(payloads[1].get("required_pull_request_reviews", {}).get("require_code_owner_reviews"))
    elif control_id == "EMS-CTRL-012":
        passed = first.get("enabled") is True
    elif control_id == "EMS-CTRL-013":
        rows = first if isinstance(first, list) else first.get("rulesets", [])
        passed = any(row.get("enforcement") == "active" and "tag" in json.dumps(row, sort_keys=True).lower() for row in rows)
    elif control_id == "EMS-CTRL-014":
        passed = len(payloads) > 1 and any(token in json.dumps(payloads, sort_keys=True).lower() for token in ("issue", "ticket", "jira"))
    elif control_id in {"EMS-CTRL-015", "EMS-CTRL-017"}:
        passed = bool(first)
    elif control_id == "EMS-CTRL-018":
        security = first.get("security_and_analysis", {})
        passed = security.get("secret_scanning", {}).get("status") == "enabled" and security.get("secret_scanning_push_protection", {}).get("status") == "enabled"
    elif control_id == "EMS-CTRL-020":
        passed = bool(first.get("license", {}).get("spdx_id") or first.get("spdx_id")) and len(payloads) > 1 and bool(payloads[1])
    elif control_id == "EMS-CTRL-021":
        passed = first.get("bomFormat") == "CycloneDX" and bool(first.get("components"))
    elif control_id == "EMS-CTRL-033":
        passed = len(payloads) > 1 and bool(first) and bool(payloads[1])
    elif control_id == "EMS-CTRL-039":
        reviewers = first.get("protection_rules", [])
        passed = first.get("id") == 20656884777 and any(rule.get("type") == "required_reviewers" for rule in reviewers)
    else:
        return {"result_status": "EXECUTION_BLOCKED", "result_reason": "CONTROL_OUTSIDE_AUTHORIZED_SCOPE"}
    return {"result_status": "PASS" if passed else "FAIL", "result_reason": "APPROVED_RULE_EVALUATED"}
