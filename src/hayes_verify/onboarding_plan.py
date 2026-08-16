"""WS4 immutable onboarding assessment plans; no requests or outcomes are generated."""
from __future__ import annotations

import hashlib
import json
from typing import Any

LOCAL_PATH_FIELDS = frozenset({"local_path", "repository_path", "execution_path", "filesystem_path"})

class PlanValidationError(ValueError): pass

def _sha(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()

def _no_paths(value: Any) -> None:
    if isinstance(value, dict):
        if LOCAL_PATH_FIELDS.intersection(value): raise PlanValidationError("local execution paths are excluded from plans")
        for item in value.values(): _no_paths(item)
    elif isinstance(value, list):
        for item in value: _no_paths(item)

def _reference(value: str) -> str:
    if not value or "\\" in value or ":/" in value or ":\\" in value: raise PlanValidationError("plan references must not be local paths")
    return value

def _support(registry: dict[str, Any], control_id: str) -> tuple[str, str | None]:
    item=registry.get("controls",{}).get(control_id,{})
    state=item.get("implementation_state","NOT_IMPLEMENTED")
    if state == "IMPLEMENTED": return ("SUPPORTED_HYBRID" if item.get("automation_boundary") == "HYBRID" else "SUPPORTED_AUTOMATED", item.get("family"))
    if state == "HUMAN_EVIDENCE_REQUIRED": return ("HUMAN_EVIDENCE_REQUIRED", item.get("family"))
    return "NOT_IMPLEMENTED", item.get("family")

def _authority(scope: str) -> str:
    return {"REPOSITORY":"REPOSITORY_EVIDENCE","SERVICE":"SERVICE_EVIDENCE","ORGANIZATION":"ORGANIZATION_EVIDENCE","PLATFORM":"PLATFORM_EVIDENCE","EMS":"EMS_EVIDENCE"}.get(scope,"CONTROLLED_EVIDENCE")

def create_frozen_assessment_plan(repository_snapshot: dict[str, Any], classification_snapshot: dict[str, Any], applicability_snapshot: dict[str, Any], *, snapshot_references: dict[str,str], ems_authorities: dict[str,dict[str,str]], registry: dict[str,Any], registry_reference: str, registry_sha256: str, created_at: str, frozen_at: str, baseline_commit_sha: str | None=None) -> dict[str,Any]:
    """Bind immutable WS1-WS3 data and policy/registry identity before WS5 request composition."""
    _no_paths([repository_snapshot,classification_snapshot,applicability_snapshot,ems_authorities,registry])
    if repository_snapshot.get("repository_id") != classification_snapshot.get("repository_id") != applicability_snapshot.get("repository_id"): raise PlanValidationError("snapshot repository identity mismatch")
    expected={"repository_snapshot": hashlib.sha256(json.dumps(repository_snapshot, sort_keys=True).encode()).hexdigest(), "classification_snapshot": _sha(classification_snapshot), "effective_applicability_snapshot": _sha(applicability_snapshot)}
    for key,digest in expected.items():
        if snapshot_references.get(key,{}).get("sha256") != digest: raise PlanValidationError(f"{key} hash binding mismatch")
        _reference(snapshot_references[key].get("reference",""))
    if classification_snapshot.get("repository_snapshot_sha256") != expected["repository_snapshot"]: raise PlanValidationError("WS2 -> WS1 binding mismatch")
    if applicability_snapshot.get("classification_snapshot_sha256") != expected["classification_snapshot"]: raise PlanValidationError("WS3 -> WS2 binding mismatch")
    if len(registry_sha256)!=64 or not registry.get("registry_version"): raise PlanValidationError("registry version/hash required")
    if not all(value.get("reference") and len(value.get("sha256",""))==64 for value in ems_authorities.values()): raise PlanValidationError("EMS authority references/hashes required")
    controls=[]; evidence=[]; reviews=[]; targets=[]
    for item in applicability_snapshot.get("controls",[]):
        state,family=_support(registry,item["control_id"]); scope=item["scope"]; applicable=item["applicability_state"]
        review = applicable == "APPLICABILITY_UNRESOLVED" or state in {"HUMAN_EVIDENCE_REQUIRED","NOT_IMPLEMENTED"}
        reason = item["decision_reason"] if applicable == "APPLICABILITY_UNRESOLVED" else ("human evidence required" if state=="HUMAN_EVIDENCE_REQUIRED" else ("evaluator not implemented" if state=="NOT_IMPLEMENTED" else None))
        eligible = applicable == "APPLICABLE" and state in {"SUPPORTED_AUTOMATED","SUPPORTED_HYBRID"}
        entry={"control_id":item["control_id"],"scope":scope,"applicability_state":applicable,"applicability_snapshot_reference":snapshot_references["effective_applicability_snapshot"]["reference"],"support_state":state,"evaluator_family":family,"evidence_authority":_authority(scope),"evidence_requirements":[_authority(scope)],"execution_role":"AUTHORITATIVE_EVALUATION" if scope=="REPOSITORY" else "PROJECTION","target_type":scope,"human_review_required":review,"human_review_reason":reason,"request_generation_eligible":eligible}
        controls.append(entry); evidence.append({"control_id":entry["control_id"],"authority":entry["evidence_authority"],"requirements":entry["evidence_requirements"]}); targets.append({"control_id":entry["control_id"],"scope":scope,"role":entry["execution_role"]})
        if review: reviews.append({"control_id":entry["control_id"],"required":True,"reason":reason,"required_reviewer_role":"CONTROL_OWNER_OR_AUTHORITY"})
    body={"repository_id":repository_snapshot["repository_id"],"repository_snapshot":snapshot_references["repository_snapshot"],"classification_snapshot":snapshot_references["classification_snapshot"],"effective_applicability_snapshot":snapshot_references["effective_applicability_snapshot"],"ems_authorities":ems_authorities,"hayes":{"registry_version":registry["registry_version"],"registry_sha256":registry_sha256,"registry_reference":_reference(registry_reference),"baseline_commit_sha":baseline_commit_sha},"created_at":created_at,"frozen_at":frozen_at,"state":"FROZEN","controls":controls,"execution_targets":targets,"evidence_requirements":evidence,"human_review_requirements":reviews}
    body["assessment_plan_id"]="PLAN-"+_sha(body)[:16];body["plan_sha256"]=_sha(body);return body

def validate_frozen_plan(plan: dict[str,Any], *, current_hashes: dict[str,str]) -> str:
    """Validate immutable bindings; caller must create a new plan after PLAN_INPUT_CHANGED."""
    if plan.get("state") != "FROZEN": raise PlanValidationError("assessment plan is not frozen")
    copy=dict(plan);stored=copy.pop("plan_sha256",None)
    if stored != _sha(copy): raise PlanValidationError("frozen plan integrity failure")
    mapping={"repository_snapshot":"repository_snapshot","classification_snapshot":"classification_snapshot","effective_applicability_snapshot":"effective_applicability_snapshot"}
    for source,key in mapping.items():
        if current_hashes.get(key)!=plan[source]["sha256"]: return "PLAN_INPUT_CHANGED"
    for name,value in plan["ems_authorities"].items():
        if current_hashes.get(f"ems:{name}") != value["sha256"]: return "PLAN_INPUT_CHANGED"
    if current_hashes.get("hayes_registry") != plan["hayes"]["registry_sha256"]: return "PLAN_INPUT_CHANGED"
    return "VALID"
