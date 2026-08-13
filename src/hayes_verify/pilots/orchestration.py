from __future__ import annotations

from pathlib import Path

from hayes_verify.pilots.github_collectors import (
    collect_branch_protection,
    collect_pr_review,
    collect_secret_scanning,
)
from hayes_verify.pilots.github_evaluators import (
    evaluate_branch_protection,
    evaluate_pr_review,
    evaluate_secret_scanning,
)

CONTROL_MAP = {
    "EMS-CTRL-009": (collect_branch_protection, evaluate_branch_protection),
    "EMS-CTRL-010": (collect_pr_review, evaluate_pr_review),
    "EMS-CTRL-018": (collect_secret_scanning, evaluate_secret_scanning),
}


def run_pilot(
    bundle,
    request: dict,
    repository_path: Path,
    github_repo: str,
) -> tuple[list[dict], dict]:
    bundle.validate_request(request)

    if request["applicability_state"] != "APPLICABLE":
        raise ValueError("Pilot evaluator accepts only EMS-authorized APPLICABLE requests.")

    if request["control_id"] not in CONTROL_MAP:
        raise ValueError(f"Unsupported pilot control: {request['control_id']}")

    collector, evaluator = CONTROL_MAP[request["control_id"]]
    evidence = collector(request, repository_path, github_repo)
    result = evaluator(request, evidence)

    bundle.validate_result(result)

    if result["promotion_state"] != "NOT_PROMOTED":
        raise ValueError("Hayes Verify must not promote evidence.")

    return evidence, result
