"""WS5 evidence readiness and frozen-plan request composition; never executes evaluators."""
from __future__ import annotations

import hashlib
import json
from typing import Any

from hayes_verify.onboarding_plan import validate_frozen_plan


class EvidenceCompositionError(ValueError): pass

def _sha(v:Any)->str:return hashlib.sha256(json.dumps(v,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def _expected(authority:str)->str:return authority.removesuffix('_EVIDENCE')
def _evidence_state(entry:dict[str,Any], candidates:list[dict[str,Any]])->tuple[str,list[dict[str,Any]]]:
 required=entry['evidence_authority']; supplied=[x for x in candidates if x.get('control_id')==entry['control_id']]
 qualified=[x for x in supplied if x.get('authority_type')==_expected(required)]
 if not supplied:return 'MISSING',[]
 if any(x.get('availability_state')=='INACCESSIBLE' for x in qualified):return 'INACCESSIBLE',qualified
 if not qualified:return 'INSUFFICIENT',supplied
 if any(x.get('freshness_state')=='STALE' for x in qualified):return 'STALE',qualified
 values={json.dumps(x.get('observed_value'),sort_keys=True) for x in qualified}
 if len(values)>1:return 'CONFLICTING',qualified
 return 'RESOLVED',qualified

def compose_requests(plan:dict[str,Any], *, current_hashes:dict[str,str], evidence_candidates:list[dict[str,Any]], requested_at_utc:str)->dict[str,Any]:
 if validate_frozen_plan(plan,current_hashes=current_hashes)!='VALID':raise EvidenceCompositionError('frozen plan binding invalid: PLAN_INPUT_CHANGED')
 before=_sha(plan); resolutions=[];requests=[];coverage=[]
 for entry in plan['controls']:
  state,refs=_evidence_state(entry,evidence_candidates)
  app,support=entry['applicability_state'],entry['support_state']
  if app=='NOT_APPLICABLE':disposition='NO_REQUEST_NOT_APPLICABLE';state='NOT_REQUIRED'
  elif app=='APPLICABILITY_UNRESOLVED':disposition='NO_REQUEST_APPLICABILITY_UNRESOLVED'
  elif support=='NOT_IMPLEMENTED':disposition='NO_REQUEST_UNSUPPORTED'
  elif support=='HUMAN_EVIDENCE_REQUIRED':disposition='NO_REQUEST_HUMAN_EVIDENCE_REQUIRED';state='HUMAN_EVIDENCE_REQUIRED'
  elif state!='RESOLVED' or entry['target_type'] not in {'REPOSITORY','ORGANIZATION'} or entry['execution_role']!='AUTHORITATIVE_EVALUATION':disposition='NO_REQUEST_EVIDENCE_UNRESOLVED'
  else:
   disposition='REQUEST_READY'; request={'contract_version':'1.0','wave':'2D','request_id':'ONB-'+_sha({'plan':plan['assessment_plan_id'],'control':entry['control_id'],'at':requested_at_utc})[:16],'control_id':entry['control_id'],'target_id':plan['repository_id'],'repository_name':plan['repository_id'],'applicability_state':'APPLICABLE','requested_at_utc':requested_at_utc,'control_definition_sha256':plan['ems_authorities']['requirements']['sha256'],'applicability_matrix_sha256':plan['effective_applicability_snapshot']['sha256'],'requested_evidence_types':entry['evidence_requirements'],'target_type':entry['target_type'],'evaluation_role':entry['execution_role'],'evidence_authority':entry['evidence_authority']};requests.append(request)
  resolutions.append({'control_id':entry['control_id'],'required_evidence':entry['evidence_requirements'],'supplied_evidence':refs,'authority_evaluation':entry['evidence_authority'],'freshness_evaluation':'CONSTRAINED' if any(x.get('freshness_state') for x in refs) else 'NOT_CONSTRAINED_BY_CURRENT_AUTHORITY','conflict_evaluation':state=='CONFLICTING','resolution_state':state,'request_generation_effect':disposition,'references':[x.get('source_reference') for x in refs]})
  coverage.append({'control_id':entry['control_id'],'composition_disposition':disposition,'target_role':entry['execution_role']})
 if _sha(plan)!=before:raise EvidenceCompositionError('frozen plan mutation detected')
 manifest={'assessment_plan_id':plan['assessment_plan_id'],'assessment_plan_sha256':plan['plan_sha256'],'repository_id':plan['repository_id'],'created_at':requested_at_utc,'ems_authority_hashes':{k:v['sha256'] for k,v in plan['ems_authorities'].items()},'hayes_registry_sha256':plan['hayes']['registry_sha256'],'evidence_set_sha256':_sha(evidence_candidates),'request_count':len(requests),'non_request_count':len(coverage)-len(requests),'composition_disposition_counts':{x:sum(r['composition_disposition']==x for r in coverage) for x in sorted({r['composition_disposition'] for r in coverage})},'request_references':[r['request_id'] for r in requests],'unresolved_evidence_references':[r['control_id'] for r in resolutions if r['resolution_state']!='RESOLVED'],'target_roles':coverage,'control_coverage':coverage,'plan_hash_unchanged':True}
 return {'evidence_resolutions':resolutions,'requests':requests,'manifest':manifest}
