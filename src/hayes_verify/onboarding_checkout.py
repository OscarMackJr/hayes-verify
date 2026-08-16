"""WS6 execution-only checkout identity verifier; no evaluator execution."""
from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any


class CheckoutVerificationError(ValueError):pass
def _sha(v:Any)->str:return hashlib.sha256(json.dumps(v,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def _git(path:Path,*args:str)->str:
 try:return subprocess.check_output(['git','-C',str(path),*args],text=True,stderr=subprocess.DEVNULL).strip()
 except subprocess.CalledProcessError:raise CheckoutVerificationError('git inspection failed')
def _optional_git(path: Path, *args: str) -> str | None:
 try: return _git(path, *args)
 except CheckoutVerificationError: return None

def normalize_remote(value:str)->tuple[str,str,str]:
 value=value.strip().removesuffix('.git').rstrip('/')
 if value.startswith('git@') and ':' in value: host,path=value[4:].split(':',1)
 elif value.startswith('ssh://git@'): host,path=value[10:].split('/',1)
 elif '://' in value: host,path=value.split('://',1)[1].split('/',1)
 else:raise CheckoutVerificationError('remote identity is unverifiable')
 owner,sep,name=path.strip('/').partition('/')
 if not sep or not host or not owner or not name:raise CheckoutVerificationError('remote identity is unverifiable')
 return host.lower(),owner.lower(),name.lower()
def verify_checkout(plan:dict[str,Any], manifest:dict[str,Any], mapping:dict[str,str], controlled_identity:dict[str,str], *, dirty_allowed:bool=False, expected_commit:str|None=None)->dict[str,Any]:
 if plan.get('state')!='FROZEN' or manifest.get('assessment_plan_sha256')!=plan.get('plan_sha256'):raise CheckoutVerificationError('frozen plan/manifest binding invalid')
 repo_id=plan['repository_id']; path_value=mapping.get(repo_id)
 base={'assessment_plan_id':plan['assessment_plan_id'],'assessment_plan_sha256':plan['plan_sha256'],'repository_id':repo_id,'request_composition_manifest_sha256':_sha(manifest),'local_mapping_reference':'LOCAL_EXECUTION_ONLY','expected':{'host':controlled_identity.get('repository_host'),'owner_or_org':controlled_identity.get('repository_owner_or_org'),'repository_name':controlled_identity.get('repository_name'),'branch_or_ref':controlled_identity.get('default_branch'),'commit':expected_commit},'observed':{'repository_path_classification':'LOCAL_EXECUTION_ONLY'},'verification_reasons':[]}
 if not path_value:return {**base,'checkout_verification_id':'CHK-'+_sha(base)[:16],'verification_state':'PATH_MISSING','request_execution_permitted':False}
 path=Path(path_value)
 if not path.exists():return {**base,'checkout_verification_id':'CHK-'+_sha(base)[:16],'verification_state':'PATH_MISSING','request_execution_permitted':False}
 try:
  if Path(_git(path, 'rev-parse', '--show-toplevel')).resolve() != path.resolve(): raise CheckoutVerificationError('mapped path is not checkout root')
 except CheckoutVerificationError:return {**base,'checkout_verification_id':'CHK-'+_sha(base)[:16],'verification_state':'NOT_GIT_REPOSITORY','request_execution_permitted':False}
 remotes={name:_git(path,'remote','get-url',name) for name in _git(path,'remote').splitlines()}
 if not remotes:state='REMOTE_MISSING';canonical=None
 else:
  parsed={name:normalize_remote(url) for name,url in remotes.items()}
  canonical=parsed.get('origin')
  if canonical is None and len(set(parsed.values()))>1:state='REMOTE_AMBIGUOUS'
  else:
   canonical=canonical or next(iter(parsed.values()));expected=(controlled_identity['repository_host'].lower(),controlled_identity['repository_owner_or_org'].lower(),controlled_identity['repository_name'].lower());state='VERIFIED' if canonical==expected else 'REMOTE_MISMATCH'
 branch=_optional_git(path,'symbolic-ref','--short','-q','HEAD');head=_git(path,'rev-parse','HEAD');dirty=bool(_git(path,'status','--porcelain'))
 observed={'repository_path_classification':'LOCAL_EXECUTION_ONLY','git_repository':True,'remote_identities':list(remotes), 'canonical_remote':canonical,'active_branch':branch,'detached_head':branch is None,'head_commit_sha':head,'dirty_state':'DIRTY' if dirty else 'CLEAN'}
 reasons=[]
 if state=='VERIFIED' and expected_commit and head!=expected_commit:state='COMMIT_MISMATCH'
 elif state=='VERIFIED' and branch is None and controlled_identity.get('default_branch') and not expected_commit:state='DETACHED_HEAD_NOT_ALLOWED'
 elif state=='VERIFIED' and branch and controlled_identity.get('default_branch') and branch!=controlled_identity['default_branch']:state='REFERENCE_MISMATCH'
 elif state=='VERIFIED' and dirty and not dirty_allowed:state='DIRTY_NOT_ALLOWED'
 if state!='VERIFIED':reasons.append(state)
 result={**base,'observed':observed,'verification_state':state,'verification_reasons':reasons,'request_execution_permitted':state=='VERIFIED'};result['checkout_verification_id']='CHK-'+_sha(result)[:16];return result
def gate_requests(manifest:dict[str,Any], checkout:dict[str,Any])->dict[str,Any]:
 rows=[]
 for item in manifest.get('control_coverage',[]):
  repository_backed=item.get('target_role')=='AUTHORITATIVE_EVALUATION' # requests in current contract are repository-backed
  ready=item['composition_disposition']=='REQUEST_READY' and (not repository_backed or checkout['verification_state']=='VERIFIED')
  rows.append({'control_id':item['control_id'],'target_role':item['target_role'],'readiness_disposition':'EXECUTION_READY' if ready else ('BLOCKED_BY_CHECKOUT' if repository_backed and item['composition_disposition']=='REQUEST_READY' else 'NOT_REQUEST_READY'),'execution_permitted':ready})
 return {'assessment_plan_id':manifest['assessment_plan_id'],'assessment_plan_sha256':manifest['assessment_plan_sha256'],'request_composition_manifest_sha256':_sha(manifest),'repository_id':manifest['repository_id'],'checkout_verification_id':checkout['checkout_verification_id'],'checkout_verification_sha256':_sha(checkout),'request_count':manifest['request_count'],'repository_backed_request_count':sum(x['target_role']=='AUTHORITATIVE_EVALUATION' for x in rows),'non_repository_request_count':sum(x['target_role']!='AUTHORITATIVE_EVALUATION' for x in rows),'execution_ready_request_count':sum(x['execution_permitted'] for x in rows),'blocked_by_checkout_count':sum(x['readiness_disposition']=='BLOCKED_BY_CHECKOUT' for x in rows),'request_level_readiness':rows}
