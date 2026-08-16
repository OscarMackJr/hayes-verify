"""WS3 current effective-applicability compiler; it never reads historical freezes."""
from __future__ import annotations

import hashlib
import json
from typing import Any

from jsonschema import Draft202012Validator, ValidationError

from hayes_verify.onboarding_classification import validate_repository_snapshot

APPLICABILITY_STATES = frozenset({"APPLICABLE", "NOT_APPLICABLE", "APPLICABILITY_UNRESOLVED"})
LOCAL_PATH_FIELDS = frozenset({"local_path", "repository_path", "execution_path", "filesystem_path"})


class ApplicabilityValidationError(ValueError):
    """Raised when a current-policy applicability snapshot cannot be safely built."""


def _sha(value: dict[str, Any]) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def _assert_no_local_paths(value: Any) -> None:
    if isinstance(value, dict):
        if LOCAL_PATH_FIELDS.intersection(value):
            raise ApplicabilityValidationError("local path is not applicability authority")
        for child in value.values():
            _assert_no_local_paths(child)
    elif isinstance(value, list):
        for child in value:
            _assert_no_local_paths(child)


def _load_schema(path: str) -> dict[str, Any]:
    with open(path, encoding="utf-8") as stream:
        return json.load(stream)


def _validate_classification(snapshot: dict[str, Any], schema_path: str) -> None:
    try:
        Draft202012Validator(_load_schema(schema_path)).validate(snapshot)
    except ValidationError as exc:
        raise ApplicabilityValidationError("invalid WS2 classification snapshot") from exc


def _condition_index(evidence: list[dict[str, Any]]) -> dict[tuple[str, str], dict[str, Any]]:
    result: dict[tuple[str, str], dict[str, Any]] = {}
    for item in evidence:
        _assert_no_local_paths(item)
        required = ("condition_id", "control_id", "source_type", "source_reference", "observed_at", "authority")
        if not all(item.get(key) for key in required):
            raise ApplicabilityValidationError("condition evidence requires controlled provenance")
        key = (str(item["control_id"]), str(item["condition_id"]))
        if key in result:
            raise ApplicabilityValidationError(f"duplicate condition evidence: {key}")
        result[key] = item
    return result


def _evaluate_condition(condition: dict[str, Any], control_id: str, classification: dict[str, Any], evidence: dict[tuple[str, str], dict[str, Any]]) -> tuple[bool | None, str, list[dict[str, Any]]]:
    """Return true, false, or None (unresolved), a rationale, and consumed refs."""
    expected = condition.get("equals")
    if "attribute" in condition:
        name = str(condition["attribute"])
        attribute = classification["attributes"].get(name)
        if not attribute or attribute.get("state") == "UNKNOWN":
            return None, f"classification attribute {name} is UNKNOWN", []
        return attribute.get("value") == expected, f"classification {name} evaluated", [attribute["source"]]
    condition_id = str(condition.get("condition_id", ""))
    item = evidence.get((control_id, condition_id))
    if not item:
        return None, f"condition evidence {condition_id} is unavailable", []
    if item.get("observed_value") is None:
        return None, f"condition evidence {condition_id} is ambiguous", [item]
    return item["observed_value"] == expected, f"condition evidence {condition_id} evaluated", [item]


def compile_effective_applicability(
    repository_snapshot: dict[str, Any],
    classification_snapshot: dict[str, Any],
    *,
    repository_snapshot_sha256: str,
    classification_snapshot_sha256: str,
    repository_snapshot_schema: str,
    classification_snapshot_schema: str,
    current_policy: dict[str, Any],
    condition_evidence: list[dict[str, Any]],
    captured_at: str,
    ems_authority_reference: str,
    ems_authority_sha256: str,
    hayes_registry: dict[str, str] | None = None,
    historical_freeze_reference: dict[str, str] | None = None,
) -> dict[str, Any]:
    """Compile current policy; unsupported status is recorded, never used for applicability."""
    validate_repository_snapshot(repository_snapshot, repository_snapshot_schema)
    _validate_classification(classification_snapshot, classification_snapshot_schema)
    _assert_no_local_paths(repository_snapshot)
    _assert_no_local_paths(classification_snapshot)
    _assert_no_local_paths(current_policy)
    if classification_snapshot.get("repository_id") != repository_snapshot.get("repository_id"):
        raise ApplicabilityValidationError("repository identity binding mismatch")
    if classification_snapshot.get("repository_snapshot_sha256") != repository_snapshot_sha256:
        raise ApplicabilityValidationError("WS2 repository snapshot hash binding mismatch")
    if _sha(classification_snapshot) != classification_snapshot_sha256:
        raise ApplicabilityValidationError("classification snapshot SHA-256 mismatch")
    if len(ems_authority_sha256) != 64 or not ems_authority_reference:
        raise ApplicabilityValidationError("current EMS authority reference/hash required")
    controls = current_policy.get("controls")
    if not isinstance(controls, list) or not controls:
        raise ApplicabilityValidationError("current policy must contain controls")
    evidence = _condition_index(condition_evidence)
    rows: list[dict[str, Any]] = []
    for policy in controls:
        control_id = str(policy.get("control_id", ""))
        scope = str(policy.get("scope", ""))
        if not control_id or not scope:
            raise ApplicabilityValidationError("each current-policy control needs control_id and scope")
        conditions = policy.get("conditions", [])
        unresolved: list[str] = []
        refs: list[dict[str, Any]] = []
        false = False
        for condition in conditions:
            outcome, reason, consumed = _evaluate_condition(condition, control_id, classification_snapshot, evidence)
            refs.extend(consumed)
            if outcome is None:
                unresolved.append(reason)
            elif not outcome:
                false = True
        if unresolved:
            state, reason = "APPLICABILITY_UNRESOLVED", "; ".join(unresolved)
        elif false:
            state, reason = "NOT_APPLICABLE", "current policy conditions positively establish non-applicability"
        elif scope in {"SERVICE", "ORGANIZATION", "PLATFORM", "EMS"} and not conditions:
            state, reason = "APPLICABILITY_UNRESOLVED", f"{scope} scope requires non-repository policy-condition evidence"
        else:
            state, reason = "APPLICABLE", "current policy conditions establish applicability"
        row = {
            "control_id": control_id,
            "scope": scope,
            "applicability_state": state,
            "decision_reason": reason,
            "policy_reference": policy.get("policy_reference", current_policy.get("policy_reference", ems_authority_reference)),
            "policy_sha256": current_policy.get("policy_sha256", ems_authority_sha256),
            "classification_inputs": sorted(condition["attribute"] for condition in conditions if "attribute" in condition),
            "condition_evidence_refs": refs,
            "unresolved_reasons": unresolved,
            "support_state": (hayes_registry or {}).get(control_id),
            "authority": policy.get("authority", ems_authority_reference),
        }
        rows.append(row)
    body = {
        "repository_id": repository_snapshot["repository_id"],
        "repository_snapshot_sha256": repository_snapshot_sha256,
        "classification_snapshot_sha256": classification_snapshot_sha256,
        "captured_at": captured_at,
        "ems_authority_reference": ems_authority_reference,
        "ems_authority_sha256": ems_authority_sha256,
        "hayes_registry": hayes_registry,
        "historical_freeze_reference": historical_freeze_reference,
        "controls": rows,
    }
    body["snapshot_id"] = "APP-" + _sha(body)[:16]
    return body
