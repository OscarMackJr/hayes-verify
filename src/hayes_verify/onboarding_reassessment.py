from __future__ import annotations

import hashlib
import json
from pathlib import Path


def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def inventory(run):return {str(p.relative_to(run)).replace("\\","/"):sha(p) for p in sorted(Path(run).rglob("*") if False else [])}
def compare(prior_run,current):
 prior=Path(prior_run);meta=json.loads((prior/'run_metadata.json').read_text());cert=json.loads((prior/'certification.json').read_text())
 if not (meta.get('synthetic') and meta.get('production_evidence') is False and cert.get('compliance_attestation') is False):return {'decision':'REASSESSMENT_BLOCKED','reason':'PRIOR_RUN_INTEGRITY_INVALID'}
 plan=json.loads((prior/'assessment_plan.json').read_text()); changes=[]
 for key in ('repository_snapshot_sha256','classification_snapshot_sha256','applicability_snapshot_sha256','ems_authority_sha256','hayes_registry_sha256','support_state','evidence_state','exception_state'):
  if key in current and current[key]!=current.get('prior_'+key):changes.append(key)
 return {'prior_run':prior.name,'assessment_plan_id':plan['assessment_plan_id'],'decision':'REASSESSMENT_REQUIRED' if changes else 'NO_REASSESSMENT_REQUIRED','material_changes':changes,'compliance_result':None}


CHANGE_TAXONOMY=frozenset({"REPOSITORY_IDENTITY","REPOSITORY_LIFECYCLE","REPOSITORY_LOCATION","CLASSIFICATION","EMS_AUTHORITY","POLICY","APPLICABILITY_INPUT","EFFECTIVE_APPLICABILITY","HAYES_REGISTRY","CONTROL_SUPPORT","CHECKOUT_REFERENCE","AUTHORITATIVE_EVIDENCE","EVIDENCE_FRESHNESS","EXCEPTION","HUMAN_REVIEW_CONDITION","RETENTION_OR_HOLD","LOCAL_EXECUTION_CONFIGURATION"})
def classify_changes(changes):
    records=[]
    for change in changes:
        category=change.get("category")
        if category not in CHANGE_TAXONOMY: return {"decision":"REASSESSMENT_BLOCKED","reason":"CURRENT_AUTHORITY_INSUFFICIENT","changes":records}
        if category=="LOCAL_EXECUTION_CONFIGURATION": materiality="NON_MATERIAL"
        elif change.get("ambiguous") or change.get("authority_missing"): materiality="UNRESOLVED"
        else: materiality="MATERIAL"
        records.append({"category":category,"materiality":materiality,"detail":change.get("detail")})
    if any(x["materiality"]=="UNRESOLVED" for x in records): decision="REASSESSMENT_BLOCKED"
    elif any(x["materiality"]=="MATERIAL" for x in records): decision="REASSESSMENT_REQUIRED"
    else: decision="NO_REASSESSMENT_REQUIRED"
    return {"decision":decision,"changes":records,"compliance_result":None,"new_assessment_run_created":False,"evaluator_execution_count":0}
