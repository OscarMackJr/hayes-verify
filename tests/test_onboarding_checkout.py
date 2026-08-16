import json
import subprocess
from pathlib import Path

from jsonschema import Draft202012Validator
from test_onboarding_plan import current, plan

from hayes_verify.onboarding_checkout import gate_requests, normalize_remote, verify_checkout
from hayes_verify.onboarding_execution import compose_requests

ROOT=Path(__file__).parents[1]
def git(path,*args):return subprocess.check_output(['git','-C',str(path),*args],text=True).strip()
def fixture(tmp_path,remote='https://github.com/synthetic/fixture.git'):
 p=tmp_path/'repo';p.mkdir(parents=True);git(p,'init','-b','main');git(p,'config','user.email','test@example.invalid');git(p,'config','user.name','Test');(p/'x').write_text('x');git(p,'add','x');git(p,'commit','-m','init');
 if remote:git(p,'remote','add','origin',remote)
 return p
def inputs():
 p=plan();m=compose_requests(p,current_hashes=current(p),evidence_candidates=[{'control_id':'EMS-CTRL-025','authority_type':'REPOSITORY','source_reference':'x','observed_value':True}],requested_at_utc='2026-08-16T00:00:00Z')['manifest'];i={'repository_host':'github.com','repository_owner_or_org':'synthetic','repository_name':'fixture','default_branch':'main'};return p,m,i
def test_normalization():assert normalize_remote('git@github.com:OWNER/REPO.git')==('github.com','owner','repo') and normalize_remote('https://github.com/OWNER/REPO')==('github.com','owner','repo')
def test_correct_remote_branch_commit_and_gate(tmp_path):
 path=fixture(tmp_path);p,m,i=inputs();v=verify_checkout(p,m,{'REPO-9004':str(path)},i);g=gate_requests(m,v);assert v['verification_state']=='VERIFIED' and v['observed']['head_commit_sha'] and g['execution_ready_request_count']==1
def test_wrong_missing_and_ambiguous_remote_fail_closed(tmp_path):
 p,m,i=inputs();wrong=fixture(tmp_path/'w','https://github.com/other/repo.git');assert verify_checkout(p,m,{'REPO-9004':str(wrong)},i)['verification_state']=='REMOTE_MISMATCH';missing=fixture(tmp_path/'m','');assert verify_checkout(p,m,{'REPO-9004':str(missing)},i)['verification_state']=='REMOTE_MISSING';amb=fixture(tmp_path/'a','');git(amb,'remote','add','x','https://github.com/a/a.git');git(amb,'remote','add','y','https://github.com/b/b.git');assert verify_checkout(p,m,{'REPO-9004':str(amb)},i)['verification_state']=='REMOTE_AMBIGUOUS'
def test_branch_commit_dirty_and_path_safety(tmp_path):
 path=fixture(tmp_path);p,m,i=inputs();git(path,'checkout','-b','other');assert verify_checkout(p,m,{'REPO-9004':str(path)},i)['verification_state']=='REFERENCE_MISMATCH';git(path,'checkout','main');(path/'x').write_text('dirty');assert verify_checkout(p,m,{'REPO-9004':str(path)},i)['verification_state']=='DIRTY_NOT_ALLOWED';assert verify_checkout(p,m,{},i)['verification_state']=='PATH_MISSING';d=tmp_path/'notgit';d.mkdir();assert verify_checkout(p,m,{'REPO-9004':str(d)},i)['verification_state']=='NOT_GIT_REPOSITORY'
def test_schemas_and_request_manifest_remains_unchanged(tmp_path):
 path=fixture(tmp_path);p,m,i=inputs();before=json.dumps(m,sort_keys=True);v=verify_checkout(p,m,{'REPO-9004':str(path)},i);r=gate_requests(m,v);Draft202012Validator(json.loads((ROOT/'schemas/checkout_verification.schema.json').read_text())).validate(v);Draft202012Validator(json.loads((ROOT/'schemas/execution_readiness_manifest.schema.json').read_text())).validate(r);assert before==json.dumps(m,sort_keys=True)
