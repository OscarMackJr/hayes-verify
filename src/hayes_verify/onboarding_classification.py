"""WS2 tri-state classification snapshots; this module does not calculate applicability."""
from __future__ import annotations

import hashlib
import json
from typing import Any

from jsonschema import Draft202012Validator, ValidationError

TRI_STATES = frozenset({"KNOWN_TRUE", "KNOWN_FALSE", "UNKNOWN"})
VALUE_STATES = frozenset({"KNOWN", "UNKNOWN"})
BOOLEAN_ATTRIBUTES = frozenset({"production", "internet_exposed", "contains_customer_data", "ai_enabled"})
NON_BOOLEAN_ATTRIBUTES = frozenset({"owner", "tier", "service_criticality", "data_classification"})
HUMAN_CONFIRMATION_REQUIRED = frozenset({"production", "contains_customer_data", "ai_enabled", "service_criticality", "data_classification"})
LOCAL_PATH_FIELDS = frozenset({"local_path", "repository_path", "execution_path", "filesystem_path"})

class ClassificationValidationError(ValueError): pass

def _load_schema(path: str) -> dict[str, Any]:
    return json.loads(open(path, encoding="utf-8").read())

def validate_repository_snapshot(snapshot: dict[str, Any], schema_path: str) -> None:
    try: Draft202012Validator(_load_schema(schema_path)).validate(snapshot)
    except ValidationError as exc: raise ClassificationValidationError("invalid WS1 repository snapshot") from exc

def _attribute(name: str, item: dict[str, Any]) -> dict[str, Any]:
    if LOCAL_PATH_FIELDS.intersection(item): raise ClassificationValidationError("local path is not classification authority")
    source = item.get("source")
    if isinstance(source, dict) and LOCAL_PATH_FIELDS.intersection(source):
        raise ClassificationValidationError("local path is not classification authority")
    if not isinstance(source, dict) or not source.get("source_type") or not source.get("source_reference") or not source.get("observation_timestamp"):
        raise ClassificationValidationError(f"{name} requires source provenance")
    confirmation = item.get("confirmation_state", "UNKNOWN")
    if confirmation not in {"AUTO_DISCOVERED", "HUMAN_CONFIRMED", "UNKNOWN"}: raise ClassificationValidationError(f"invalid confirmation state for {name}")
    if name in BOOLEAN_ATTRIBUTES:
        state=item.get("state")
        if state not in TRI_STATES: raise ClassificationValidationError(f"{name} requires explicit tri-state")
        if state=="KNOWN_TRUE" and item.get("value") is not True: raise ClassificationValidationError(f"{name} true state/value mismatch")
        if state=="KNOWN_FALSE" and item.get("value") is not False: raise ClassificationValidationError(f"{name} false state/value mismatch")
        if state=="UNKNOWN" and item.get("value") is not None: raise ClassificationValidationError(f"{name} UNKNOWN must not have boolean value")
    else:
        state=item.get("state")
        if state not in VALUE_STATES: raise ClassificationValidationError(f"{name} requires KNOWN or UNKNOWN")
        if state=="UNKNOWN" and item.get("value") is not None: raise ClassificationValidationError(f"{name} UNKNOWN must have null value")
        if state=="KNOWN" and not item.get("value"): raise ClassificationValidationError(f"{name} KNOWN requires value")
    if name in HUMAN_CONFIRMATION_REQUIRED and confirmation=="HUMAN_CONFIRMED" and not item.get("confirmed_by"):
        raise ClassificationValidationError(f"{name} human confirmation requires confirmed_by")
    return {"value":item.get("value"),"state":state,"source":source,"confirmation_state":confirmation,"confirmed_by":item.get("confirmed_by"),"confirmed_at":item.get("confirmed_at")}

def classification_snapshot(repository_snapshot: dict[str, Any], repository_snapshot_sha256: str, attributes: dict[str, dict[str, Any]], *, captured_at: str, authority_reference: str, authority_sha256: str, repository_snapshot_schema: str) -> dict[str, Any]:
    validate_repository_snapshot(repository_snapshot, repository_snapshot_schema)
    if len(repository_snapshot_sha256)!=64 or not authority_reference or len(authority_sha256)!=64: raise ClassificationValidationError("hash-bound authority references are required")
    if any(x in repository_snapshot for x in LOCAL_PATH_FIELDS): raise ClassificationValidationError("repository snapshot contains local path")
    if set(attributes)-BOOLEAN_ATTRIBUTES-NON_BOOLEAN_ATTRIBUTES: raise ClassificationValidationError("unknown classification attribute")
    normalized={name:_attribute(name,attributes.get(name,{"state":"UNKNOWN","value":None,"source":{"source_type":"UNKNOWN","source_reference":"UNSPECIFIED","observation_timestamp":captured_at},"confirmation_state":"UNKNOWN"})) for name in sorted(BOOLEAN_ATTRIBUTES|NON_BOOLEAN_ATTRIBUTES)}
    unknown=[n for n,v in normalized.items() if v["state"]=="UNKNOWN"]
    gaps=[n for n,v in normalized.items() if n in HUMAN_CONFIRMATION_REQUIRED and v["confirmation_state"]!="HUMAN_CONFIRMED"]
    completeness="BLOCKED_BY_UNKNOWN" if any(n in HUMAN_CONFIRMATION_REQUIRED for n in unknown) else ("INCOMPLETE" if gaps else "COMPLETE")
    body={"repository_id":repository_snapshot["repository_id"],"repository_snapshot_sha256":repository_snapshot_sha256,"captured_at":captured_at,"authority_reference":authority_reference,"authority_sha256":authority_sha256,"attributes":normalized,"classification_completeness":{"state":completeness,"known_material_attributes":[n for n in HUMAN_CONFIRMATION_REQUIRED if normalized[n]["state"]!="UNKNOWN"],"unknown_material_attributes":[n for n in HUMAN_CONFIRMATION_REQUIRED if normalized[n]["state"]=="UNKNOWN"],"human_confirmation_gaps":gaps},"human_confirmation_state":"COMPLETE" if not gaps else "INCOMPLETE"}
    body["classification_snapshot_id"]="CLS-"+hashlib.sha256(json.dumps(body,sort_keys=True,separators=(",",":")).encode()).hexdigest()[:16]
    return body
