"""Contract-bound AA4 live-runtime primitives; callers inject all HTTP access."""
from __future__ import annotations

import hashlib
import json
from typing import Any

from hayes_verify.aa4_real_evidence import (
    AA4_TARGET,
    AA4EvidenceContractError,
    build_static_candidate,
)


def collect_with_getter(contract: dict[str, Any], *, control_id: str, target: dict[str, str], collected_at_utc: str, getter: Any, default_branch: str = "main") -> dict[str, Any]:
    """Collect one contract-listed evidence record through an injected GET-only client."""
    mapping = next((item for item in contract["source_contract"]["control_to_source_mapping"] if item["control_id"] == control_id), None)
    if mapping is None:
        raise AA4EvidenceContractError("control is outside the approved AA4 D5 scope")
    sources = []
    for template in mapping["sources"]:
        response = getter(template.replace("{default_branch}", default_branch))
        if not isinstance(response, dict) or response.get("response_status") != 200:
            raise AA4EvidenceContractError("authorized source request did not return a usable response")
        sources.append({"request_method": "GET", "request_uri": template, "response_status": 200, "response_etag": response.get("response_etag"), "source_object_sha": response.get("source_object_sha"), "captured_payload": response.get("captured_payload")})
    return build_static_candidate(contract, control_id=control_id, target=target, collected_at_utc=collected_at_utc, sources=sources)


def evaluate_record(record: dict[str, Any]) -> dict[str, str]:
    """Evaluate approved projections; every unsupported or invalid case fails closed."""
    if record.get("target") != AA4_TARGET or not record.get("canonical_payload_sha256"):
        return {"result_status": "EXECUTION_BLOCKED", "result_reason": "TARGET_OR_HASH_INVALID"}
    payloads = [item.get("captured_payload", {}) for item in record.get("sources", [])]
    control = record.get("control_id")
    if control == "EMS-CTRL-012":
        passed = bool(payloads and payloads[0].get("enabled") is True)
    elif control == "EMS-CTRL-018":
        security = payloads[0].get("security_and_analysis", {}) if payloads else {}
        passed = security.get("secret_scanning", {}).get("status") == "enabled" and security.get("secret_scanning_push_protection", {}).get("status") == "enabled"
    elif control == "EMS-CTRL-039":
        value = payloads[0] if payloads else {}
        passed = value.get("id") == 20656884777 and any(rule.get("type") == "required_reviewers" for rule in value.get("protection_rules", []))
    else:
        return {"result_status": "UNRESOLVED", "result_reason": "CONTROL_RULE_REQUIRES_FULL_APPROVED_PROJECTION"}
    return {"result_status": "PASS" if passed else "FAIL", "result_reason": "APPROVED_RULE_EVALUATED"}


def result_record(evidence: dict[str, Any], result: dict[str, str], *, authorization_reference: str, created_at_utc: str) -> dict[str, Any]:
    """Build an in-memory governed result; persistence remains an orchestration concern."""
    body = {"control_id": evidence["control_id"], "target": evidence["target"], "evidence_record_sha256": evidence["canonical_payload_sha256"], "evaluator_identity": "hayes-aa4-live-runtime", "evaluator_version": "1.0.0-proposed", **result, "created_at_utc": created_at_utc, "authorization_reference": authorization_reference}
    body["result_id"] = "AA4-RESULT-" + hashlib.sha256(json.dumps(body, sort_keys=True, separators=(",", ":")).encode()).hexdigest()[:16]
    return body
