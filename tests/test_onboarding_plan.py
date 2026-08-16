import hashlib
import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

from hayes_verify.onboarding_applicability import compile_effective_applicability
from hayes_verify.onboarding_classification import classification_snapshot
from hayes_verify.onboarding_identity import RepositoryIdentity, repository_snapshot
from hayes_verify.onboarding_plan import (
 PlanValidationError,
 create_frozen_assessment_plan,
 validate_frozen_plan,
)

ROOT=Path(__file__).parents[1]

def repo(): return repository_snapshot(RepositoryIdentity("REPO-9004","fixture","synthetic","github.com","https://github.com/synthetic/fixture","ACTIVE","main"),captured_at="2026-08-16T00:00:00Z",authority_reference="ems",authority_sha256="a"*64)
def src(): return {"source_type":"SYNTHETIC","source_reference":"fixture","observation_timestamp":"2026-08-16T00:00:00Z"}
def attrs(): return {n:{"state":s,"value":v,"source":src(),"confirmation_state":"HUMAN_CONFIRMED","confirmed_by":"owner"} for n,s,v in [("production","KNOWN_TRUE",True),("internet_exposed","KNOWN_FALSE",False),("contains_customer_data","KNOWN_FALSE",False),("ai_enabled","KNOWN_FALSE",False),("owner","KNOWN","Synthetic"),("tier","KNOWN","Tier2"),("service_criticality","KNOWN","Low"),("data_classification","KNOWN","Internal")]}
def sh(x): return hashlib.sha256(json.dumps(x,sort_keys=True,separators=(",",":")).encode()).hexdigest()
def inputs():
 r=repo(); rh=hashlib.sha256(json.dumps(r,sort_keys=True).encode()).hexdigest(); c=classification_snapshot(r,rh,attrs(),captured_at="2026-08-16T00:00:00Z",authority_reference="ems-class",authority_sha256="b"*64,repository_snapshot_schema=str(ROOT/'schemas/repository_snapshot.schema.json'));ch=sh(c)
 policy={"policy_reference":"policy","policy_sha256":"c"*64,"controls":[{"control_id":"EMS-CTRL-025","scope":"REPOSITORY","conditions":[]},{"control_id":"EMS-CTRL-029","scope":"SERVICE","conditions":[]},{"control_id":"EMS-CTRL-007","scope":"ORGANIZATION","conditions":[]},{"control_id":"EMS-CTRL-016","scope":"REPOSITORY","conditions":[]}]}
 a=compile_effective_applicability(r,c,repository_snapshot_sha256=rh,classification_snapshot_sha256=ch,repository_snapshot_schema=str(ROOT/'schemas/repository_snapshot.schema.json'),classification_snapshot_schema=str(ROOT/'schemas/classification_snapshot.schema.json'),current_policy=policy,condition_evidence=[],captured_at="2026-08-16T00:00:00Z",ems_authority_reference="authority",ems_authority_sha256="c"*64)
 refs={"repository_snapshot":{"reference":"ws1","sha256":rh},"classification_snapshot":{"reference":"ws2","sha256":ch},"effective_applicability_snapshot":{"reference":"ws3","sha256":sh(a)}}
 ems={"requirements":{"reference":"registry/requirements","sha256":"a"*64},"certification":{"reference":"registry/cert","sha256":"b"*64}}
 registry={"registry_version":"1.10","controls":{"EMS-CTRL-025":{"implementation_state":"IMPLEMENTED","family":"test_quality"},"EMS-CTRL-029":{"implementation_state":"IMPLEMENTED","automation_boundary":"HYBRID","family":"test_quality"},"EMS-CTRL-007":{"implementation_state":"HUMAN_EVIDENCE_REQUIRED","family":"human_judgment"},"EMS-CTRL-016":{"implementation_state":"PLANNED_AUTOMATED","family":"documentation_governance"}}}
 return r,c,a,refs,ems,registry

def plan():
 r,c,a,refs,ems,registry=inputs();return create_frozen_assessment_plan(r,c,a,snapshot_references=refs,ems_authorities=ems,registry=registry,registry_reference="registry/v1.10",registry_sha256="d"*64,created_at="2026-08-16T00:00:00Z",frozen_at="2026-08-16T00:00:00Z")
def current(p): return {"repository_snapshot":p["repository_snapshot"]["sha256"],"classification_snapshot":p["classification_snapshot"]["sha256"],"effective_applicability_snapshot":p["effective_applicability_snapshot"]["sha256"],"ems:requirements":p["ems_authorities"]["requirements"]["sha256"],"ems:certification":p["ems_authorities"]["certification"]["sha256"],"hayes_registry":p["hayes"]["registry_sha256"]}
def entry(p,c):return next(x for x in p["controls"] if x["control_id"]==c)
def test_hash_bound_plan_freezes_before_requests_and_schema_validates():
 p=plan();Draft202012Validator(json.loads((ROOT/'schemas/assessment_plan.schema.json').read_text())).validate(p);assert p["state"]=="FROZEN" and "requests" not in p and "compliance_result" not in p
def test_support_applicability_and_authority_boundaries():
 p=plan();assert entry(p,"EMS-CTRL-025")["support_state"]=="SUPPORTED_AUTOMATED";assert entry(p,"EMS-CTRL-029")["support_state"]=="SUPPORTED_HYBRID";assert entry(p,"EMS-CTRL-016")["support_state"]=="NOT_IMPLEMENTED" and entry(p,"EMS-CTRL-016")["applicability_state"]=="APPLICABLE";assert entry(p,"EMS-CTRL-029")["evidence_authority"]=="SERVICE_EVIDENCE" and entry(p,"EMS-CTRL-007")["target_type"]=="ORGANIZATION"
def test_unresolved_and_human_evidence_project_review_without_decision():
 p=plan();assert entry(p,"EMS-CTRL-029")["human_review_required"] is True;assert entry(p,"EMS-CTRL-007")["human_review_required"] is True;assert all("decision" not in x for x in p["human_review_requirements"])
@pytest.mark.parametrize("key",["repository_snapshot","classification_snapshot","effective_applicability_snapshot","ems:requirements","hayes_registry"])
def test_changed_input_invalidates_without_mutating(key):
 p=plan();h=current(p);h[key]="e"*64;assert validate_frozen_plan(p,current_hashes=h)=="PLAN_INPUT_CHANGED"
def test_frozen_integrity_and_local_paths_fail_closed():
    frozen = plan()
    assert validate_frozen_plan(frozen, current_hashes=current(frozen)) == "VALID"
    frozen["controls"][0]["scope"] = "SERVICE"
    with pytest.raises(PlanValidationError):
        validate_frozen_plan(frozen, current_hashes=current(plan()))
