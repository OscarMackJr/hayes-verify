"""Generic Wave 2D execution-target and evidence-provider contracts."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

TARGET_TYPES = {"REPOSITORY", "ORGANIZATION"}
ROLES = {"AUTHORITATIVE_EVALUATION", "PROJECTION"}


def validate_target(target: dict[str, Any]) -> None:
    target_type = target.get("target_type")
    role = target.get("evaluation_role")
    if target_type not in TARGET_TYPES:
        raise ValueError("unsupported target_type")
    if role not in ROLES:
        raise ValueError("unsupported evaluation_role")
    if target_type == "ORGANIZATION":
        if target.get("repository_path"):
            raise ValueError("organization target forbids repository_path")
        if not target.get("organization_id"):
            raise ValueError("organization target requires organization_id")
    if target_type == "REPOSITORY" and not target.get("repository_path"):
        raise ValueError("repository target requires repository_path")
    if role == "PROJECTION" and target.get("authoritative_pass") is True:
        raise ValueError("projection cannot establish authoritative PASS")


def resolve_file_evidence(reference: str | None) -> tuple[dict[str, Any] | None, dict[str, Any]]:
    """Load JSON evidence without granting the runtime authority over its meaning."""
    provenance: dict[str, Any] = {
        "provider_type": "FILE",
        "provider_reference": reference,
    }
    if not reference:
        provenance["state"] = "UNAVAILABLE"
        return None, provenance
    path = Path(reference)
    if not path.is_file():
        provenance.update({"state": "UNAVAILABLE", "reason": "evidence file does not exist"})
        return None, provenance
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        provenance.update({"state": "UNAVAILABLE", "reason": f"evidence file is unreadable or invalid: {error}"})
        return None, provenance
    if not isinstance(value, dict):
        provenance.update({"state": "UNAVAILABLE", "reason": "evidence JSON must be an object"})
        return None, provenance
    provenance.update({"state": "AVAILABLE", "resolved_path": str(path.resolve())})
    return value, provenance


def resolve_evidence_provider(request: dict[str, Any]) -> tuple[dict[str, Any] | None, dict[str, Any]]:
    provider_type = request.get("evidence_provider_type")
    if provider_type in (None, ""):
        return None, {"state": "NOT_CONFIGURED"}
    if provider_type != "FILE":
        return None, {"provider_type": provider_type, "state": "UNAVAILABLE", "reason": "unsupported evidence provider type"}
    payload, provenance = resolve_file_evidence(request.get("evidence_provider_reference"))
    if request.get("evidence_authority"):
        provenance["evidence_authority"] = request["evidence_authority"]
    if request.get("evidence_timestamp"):
        provenance["evidence_timestamp"] = request["evidence_timestamp"]
    return payload, provenance


def normalize_result_authority(request: dict[str, Any], result: dict[str, Any]) -> None:
    """Attach target metadata and prevent projections from becoming authority."""
    result["target_type"] = request["target_type"]
    result["evaluation_role"] = request["evaluation_role"]
    if request["evaluation_role"] == "PROJECTION" and result.get("result_state") == "PASS":
        result["result_state"] = "WARNING"
        result["evidence_state"] = "INSUFFICIENT"
        result["rationale"] = "Projection observations cannot independently establish authoritative compliance PASS."
        result["authoritative_compliance"] = False
    else:
        result["authoritative_compliance"] = request["evaluation_role"] == "AUTHORITATIVE_EVALUATION"