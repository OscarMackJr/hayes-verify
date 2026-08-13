from __future__ import annotations

from hayes_verify.collectors import collect_repository_evidence
from hayes_verify.evaluators import evaluate_request


def run_evaluation(bundle, request: dict) -> dict:
    bundle.validate_request(request)

    if request["applicability_state"] != "APPLICABLE":
        raise ValueError("Hayes Verify only accepts EMS-authorized APPLICABLE requests.")

    evidence = collect_repository_evidence(request)
    result = evaluate_request(request, evidence)
    bundle.validate_result(result)
    return result
