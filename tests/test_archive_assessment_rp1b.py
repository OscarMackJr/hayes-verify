from __future__ import annotations

import json
import zipfile
from pathlib import Path

import pytest

from hayes_verify.archive_assessment import (
 ArchiveWorkflowError,
 consume_classification_response,
 create_workflow,
 initialize_intake_authority_and_classification,
 load_workflow,
 validate_checkpoint_chain,
)

ROOT=Path(__file__).resolve().parents[1]
def zip_at(path:Path, entries:dict[str,str]):
 with zipfile.ZipFile(path,'w') as z:
  for name,value in entries.items(): z.writestr(name,value)
 return path
def ems(tmp_path:Path):
 p=tmp_path/'ems/registry';p.mkdir(parents=True,exist_ok=True);(p/'control_catalog.yaml').write_text('controls: []\n');return p.parent
def response(run:Path, *, unknown=False):
 state=load_workflow(run); fields={}
 for name in ['production','internet_exposed','contains_customer_data','ai_enabled','owner','tier','service_criticality','data_classification']:
  fields[name]={'state':'UNKNOWN' if unknown else 'KNOWN_FALSE','value':'UNKNOWN' if unknown else False,'confirmed_by':'owner@example.test','confirmed_at':'2026-08-17T00:00:00Z','basis':'controlled test'}
 value={'schema_version':'1.0','workflow_id':state['workflow_id'],'archive_target_id':state['archive_target_id'],'source_zip_sha256':state['source_zip_sha256'],'authority_context_sha256':state['authority_context_sha256'],'responded_at':'2026-08-17T00:00:00Z','fields':fields}; path=run/'response.json';path.write_text(json.dumps(value));return path
def initialized(tmp_path:Path):
 run=create_workflow(zip_at(tmp_path/'a.zip',{'safe/a.txt':'x'}),tmp_path/'out',non_production=True);(run/'logs/local_execution.json').write_text(json.dumps({'archive_path':str(tmp_path/'a.zip'),'classification':'EXECUTION_LOCAL'}));initialize_intake_authority_and_classification(run,hayes_authority_root=ROOT,ems_authority_root=ems(tmp_path));return run
def test_intake_authority_and_request(tmp_path:Path):
 run=initialized(tmp_path); state=load_workflow(run);assert state['workflow_status']=='AWAITING_HUMAN_INPUT';assert (run/'inputs/archive_source_manifest.json').exists();assert (run/'workflow/archive_assessment_authority_context.json').exists();assert validate_checkpoint_chain(run)
def test_unknown_response_advances_to_applicability(tmp_path:Path):
 run=initialized(tmp_path); result=consume_classification_response(run,response(run,unknown=True));assert result['current_stage']=='APPLICABILITY';assert load_workflow(run)['workflow_status']=='RUNNING'
def test_response_attribution_and_binding_fail_closed(tmp_path:Path):
 run=initialized(tmp_path); p=response(run); data=json.loads(p.read_text());data['fields']['owner']['confirmed_by']='';p.write_text(json.dumps(data));
 with pytest.raises(ArchiveWorkflowError): consume_classification_response(run,p)
def test_duplicate_and_conflicting_response(tmp_path:Path):
 run=initialized(tmp_path); p=response(run);consume_classification_response(run,p);assert consume_classification_response(run,p)['current_stage']=='APPLICABILITY';data=json.loads(p.read_text());data['fields']['owner']['basis']='changed';p.write_text(json.dumps(data));
 with pytest.raises(ArchiveWorkflowError): consume_classification_response(run,p)
def test_traversal_and_wrong_authority_fail_closed(tmp_path:Path):
 run=create_workflow(zip_at(tmp_path/'bad.zip',{'../outside.txt':'x'}),tmp_path/'out',non_production=True);(run/'logs/local_execution.json').write_text(json.dumps({'archive_path':str(tmp_path/'bad.zip')}));
 with pytest.raises(ArchiveWorkflowError): initialize_intake_authority_and_classification(run,hayes_authority_root=ROOT,ems_authority_root=ems(tmp_path))
 run2=create_workflow(zip_at(tmp_path/'ok.zip',{'safe.txt':'x'}),tmp_path/'out2',non_production=True);(run2/'logs/local_execution.json').write_text(json.dumps({'archive_path':str(tmp_path/'ok.zip')}));
 with pytest.raises(ArchiveWorkflowError): initialize_intake_authority_and_classification(run2,hayes_authority_root=ems(tmp_path),ems_authority_root=ems(tmp_path))
def test_frozen_authority_is_not_replaced(tmp_path:Path):
 run=initialized(tmp_path); before=load_workflow(run)['authority_context_sha256'];(ems(tmp_path)/'registry/control_catalog.yaml').write_text('controls: [changed]\n');assert load_workflow(run)['authority_context_sha256']==before
