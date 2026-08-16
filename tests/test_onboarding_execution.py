import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator
from test_onboarding_plan import current, plan

from hayes_verify.contracts import ContractBundle
from hayes_verify.onboarding_execution import EvidenceCompositionError, compose_requests

ROOT=Path(__file__).parents[1]
def evidence(control,authority,value=True,**more):return {"evidence_id":"E-"+control,"control_id":control,"target_id":"REPO-9004","target_role":"AUTHORITATIVE_EVALUATION","authority_type":authority,"source_type":"SYNTHETIC","source_reference":"ref-"+control,"observed_at":"2026-08-16T00:00:00Z","collected_at":"2026-08-16T00:00:00Z","observed_value":value,**more}
def compose(items):
 p=plan();return p,compose_requests(p,current_hashes=current(p),evidence_candidates=items,requested_at_utc="2026-08-16T00:00:00Z")
def res(output,control):return next(x for x in output['evidence_resolutions'] if x['control_id']==control)
def test_frozen_plan_and_repository_evidence_produce_contract_request():
 _,o=compose([evidence('EMS-CTRL-025','REPOSITORY')]);assert o['manifest']['plan_hash_unchanged'] is True and len(o['requests'])==1;ContractBundle(ROOT).validate_request(o['requests'][0])
def test_repository_evidence_cannot_satisfy_service_or_organization():
 _,o=compose([evidence('EMS-CTRL-029','REPOSITORY'),evidence('EMS-CTRL-007','REPOSITORY')]);assert res(o,'EMS-CTRL-029')['resolution_state']=='INSUFFICIENT';assert res(o,'EMS-CTRL-007')['resolution_state']=='INSUFFICIENT'
def test_missing_stale_conflicting_and_inaccessible_evidence_are_not_compliance_results():
 _,missing=compose([]);assert res(missing,'EMS-CTRL-025')['resolution_state']=='MISSING';_,stale=compose([evidence('EMS-CTRL-025','REPOSITORY',freshness_state='STALE')]);assert res(stale,'EMS-CTRL-025')['resolution_state']=='STALE';_,conflict=compose([evidence('EMS-CTRL-025','REPOSITORY',True),evidence('EMS-CTRL-025','REPOSITORY',False)]);assert res(conflict,'EMS-CTRL-025')['resolution_state']=='CONFLICTING';_,bad=compose([evidence('EMS-CTRL-025','REPOSITORY',availability_state='INACCESSIBLE')]);assert res(bad,'EMS-CTRL-025')['resolution_state']=='INACCESSIBLE'
def test_not_implemented_human_and_unresolved_never_generate_normal_request():
 _,o=compose([evidence('EMS-CTRL-025','REPOSITORY')]);d={x['control_id']:x['composition_disposition'] for x in o['manifest']['control_coverage']};assert d['EMS-CTRL-016']=='NO_REQUEST_UNSUPPORTED';assert d['EMS-CTRL-007']=='NO_REQUEST_APPLICABILITY_UNRESOLVED';assert d['EMS-CTRL-029']=='NO_REQUEST_APPLICABILITY_UNRESOLVED'
def test_every_plan_control_is_accounted_for_and_artifacts_validate():
 _,o=compose([evidence('EMS-CTRL-025','REPOSITORY')]);assert len(o['manifest']['control_coverage'])==4;Draft202012Validator(json.loads((ROOT/'schemas/request_composition_manifest.schema.json').read_text())).validate(o['manifest']);[Draft202012Validator(json.loads((ROOT/'schemas/evidence_resolution.schema.json').read_text())).validate(x) for x in o['evidence_resolutions']]
def test_changed_plan_binding_is_rejected_without_rewrite():
 p=plan();h=current(p);h['hayes_registry']='f'*64
 with pytest.raises(EvidenceCompositionError):compose_requests(p,current_hashes=h,evidence_candidates=[],requested_at_utc="2026-08-16T00:00:00Z")



