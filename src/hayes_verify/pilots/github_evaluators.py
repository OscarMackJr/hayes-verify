from __future__ import annotations

import json
from datetime import UTC, datetime


def _obs(evidence: list[dict]) -> dict:
    if not evidence:
        return {}
    raw = evidence[0].get("observation", "")
    if not raw:
        return {}
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        return {}
    return parsed if isinstance(parsed, dict) else {}


def _result(
    request: dict,
    evidence: list[dict],
    result_state: str,
    evaluation_state: str,
    evidence_state: str,
    rationale: str,
    assertions: list[dict],
) -> dict:
    return {
        "contract_version": "1.0",
        "wave": "2D",
        "request_id": request["request_id"],
        "control_id": request["control_id"],
        "target_id": request["target_id"],
        "evaluation_state": evaluation_state,
        "evidence_state": evidence_state,
        "result_state": result_state,
        "evaluated_at_utc": datetime.now(UTC).isoformat(),
        "evidence_ids": [item["evidence_id"] for item in evidence],
        "rationale": rationale,
        "assertions": assertions,
        "promotion_state": "NOT_PROMOTED",
    }


def evaluate_branch_protection(request: dict, evidence: list[dict]) -> dict:
    obs = _obs(evidence)
    if not obs or obs.get("api_success") is not True:
        return _result(
            request,
            evidence,
            "FAIL",
            "BLOCKED",
            "INSUFFICIENT",
            "Branch-protection API evidence was unavailable or invalid; PASS is fail-closed.",
            [{
                "assertion_id": "branch_protection_configured",
                "result": "FAIL",
                "detail": "API evidence missing, malformed, or unsuccessful.",
            }],
        )

    protected = obs.get("protected") is True
    evaluated_branch = obs.get("evaluated_branch")
    if isinstance(evaluated_branch, str) and evaluated_branch.strip():
        branch_label = f"default branch {evaluated_branch.strip()}"
    else:
        branch_label = "evaluated branch"

    return _result(
        request,
        evidence,
        "PASS" if protected else "FAIL",
        "COMPLETE",
        "SUFFICIENT",
        (
            f"GitHub returned a valid branch-protection configuration for {branch_label}."
            if protected
            else f"GitHub response did not prove branch protection for {branch_label}."
        ),
        [{
            "assertion_id": "branch_protection_configured",
            "result": "PASS" if protected else "FAIL",
            "detail": json.dumps(obs, sort_keys=True),
        }],
    )


def evaluate_pr_review(request: dict, evidence: list[dict]) -> dict:
    obs = _obs(evidence)
    if not obs or obs.get("api_success") is not True:
        return _result(
            request,
            evidence,
            "FAIL",
            "BLOCKED",
            "INSUFFICIENT",
            "Pull-request review API evidence was unavailable or invalid; PASS is fail-closed.",
            [{
                "assertion_id": "pr_review_required",
                "result": "FAIL",
                "detail": "API evidence missing, malformed, or unsuccessful.",
            }],
        )

    present = obs.get("required_pull_request_reviews_present") is True
    count = obs.get("required_approving_review_count")
    configured = present and isinstance(count, int) and count >= 1

    return _result(
        request,
        evidence,
        "PASS" if configured else "FAIL",
        "COMPLETE",
        "SUFFICIENT",
        (
            f"GitHub requires {count} approving review(s) before merge."
            if configured
            else "GitHub did not prove at least one required approving review."
        ),
        [{
            "assertion_id": "pr_review_required",
            "result": "PASS" if configured else "FAIL",
            "detail": json.dumps(obs, sort_keys=True),
        }],
    )


def evaluate_secret_scanning(request: dict, evidence: list[dict]) -> dict:
    obs = _obs(evidence)
    if not obs or obs.get("api_success") is not True:
        return _result(
            request,
            evidence,
            "FAIL",
            "BLOCKED",
            "INSUFFICIENT",
            "Secret-scanning API evidence was unavailable or invalid; PASS is fail-closed.",
            [{
                "assertion_id": "secret_scanning_enabled",
                "result": "FAIL",
                "detail": "API evidence missing, malformed, or unsuccessful.",
            }],
        )

    status = obs.get("secret_scanning_status")
    enabled = status == "enabled"
    push_status = obs.get("push_protection_status")

    assertions = [{
        "assertion_id": "secret_scanning_enabled",
        "result": "PASS" if enabled else "FAIL",
        "detail": f"secret_scanning_status={status}",
    }]
    if push_status is not None:
        assertions.append({
            "assertion_id": "secret_scanning_push_protection_observed",
            "result": "PASS" if push_status == "enabled" else "WARNING",
            "detail": f"push_protection_status={push_status}",
        })

    return _result(
        request,
        evidence,
        "PASS" if enabled else "FAIL",
        "COMPLETE",
        "SUFFICIENT",
        (
            "GitHub secret scanning is explicitly enabled."
            if enabled
            else "GitHub secret scanning was not explicitly enabled."
        ),
        assertions,
    )
