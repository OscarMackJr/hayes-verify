from __future__ import annotations

import json
import zipfile
from pathlib import Path

import pytest
from jsonschema import validate

from hayes_verify.archive_assessment import (
    ArchiveWorkflowError,
    advance_workflow,
    archive_target_id,
    block_workflow,
    create_workflow,
    fail_workflow,
    get_status,
    load_workflow,
    pause_workflow,
    resume_workflow,
    validate_checkpoint_chain,
)


def archive(path:Path, data:bytes=b'x')->Path:
    with zipfile.ZipFile(path,'w') as z: z.writestr('safe.txt',data)
    return path

def test_creation_identity_and_manifests(tmp_path:Path)->None:
    run=create_workflow(archive(tmp_path/'a.zip'),tmp_path/'out',non_production=True)
    state=load_workflow(run); assert state['archive_target_id'].startswith('ARCHIVE-'); assert (run/'workflow'/'archive_assessment_input_manifest.json').exists(); assert validate_checkpoint_chain(run)

def test_same_zip_creates_independent_runs(tmp_path:Path)->None:
    path=archive(tmp_path/'a.zip'); first=create_workflow(path,tmp_path/'out',non_production=True); second=create_workflow(path,tmp_path/'out',non_production=True)
    assert first.parent==second.parent and first.name != second.name

def test_non_production_and_nonzip_fail_closed(tmp_path:Path)->None:
    path=archive(tmp_path/'a.zip')
    with pytest.raises(ArchiveWorkflowError): create_workflow(path,tmp_path/'out',non_production=False)
    (tmp_path/'bad.txt').write_text('bad')
    with pytest.raises(ArchiveWorkflowError): create_workflow(tmp_path/'bad.txt',tmp_path/'out',non_production=True)

def test_transitions_pause_resume_block_fail(tmp_path:Path)->None:
    run=create_workflow(archive(tmp_path/'a.zip'),tmp_path/'out',non_production=True)
    with pytest.raises(ArchiveWorkflowError): advance_workflow(run,'EXECUTION')
    advance_workflow(run,'CLASSIFICATION'); pause_workflow(run,input_type='CLASSIFICATION_RESPONSE',resume_requirements=['response']); assert get_status(run)['workflow_status']=='AWAITING_HUMAN_INPUT'
    resume_workflow(run); assert get_status(run)['current_stage']=='CLASSIFICATION'; block_workflow(run,'authority missing'); assert get_status(run)['workflow_status']=='BLOCKED'
    resume_workflow(run); fail_workflow(run,'broken runtime'); assert get_status(run)['workflow_status']=='FAILED'

def test_checkpoint_and_input_tampering_fail_closed(tmp_path:Path)->None:
    run=create_workflow(archive(tmp_path/'a.zip'),tmp_path/'out',non_production=True)
    checkpoint=next((run/'checkpoints').glob('*.json')); checkpoint.write_text('{}')
    with pytest.raises(ArchiveWorkflowError): load_workflow(run)
    run2=create_workflow(archive(tmp_path/'b.zip'),tmp_path/'out',non_production=True); p=run2/'workflow'/'archive_assessment_input_manifest.json'; data=json.loads(p.read_text()); data['source_zip_sha256']='0'*64;p.write_text(json.dumps(data))
    with pytest.raises(ArchiveWorkflowError): load_workflow(run2)

def test_unknown_version_and_identity_validation_fail_closed(tmp_path:Path)->None:
    with pytest.raises(ArchiveWorkflowError): archive_target_id('not-a-hash')
    run=create_workflow(archive(tmp_path/'a.zip'),tmp_path/'out',non_production=True); p=run/'workflow'/'archive_assessment_workflow_state.json'; data=json.loads(p.read_text());data['schema_version']='9.0';p.write_text(json.dumps(data))
    with pytest.raises(ArchiveWorkflowError): load_workflow(run)


def test_created_artifacts_validate_against_rp1a_schemas(tmp_path: Path) -> None:
    root = Path(__file__).resolve().parents[1]
    run = create_workflow(archive(tmp_path / "a.zip"), tmp_path / "out", non_production=True)
    artifacts = {
        "archive_assessment_workflow_state.schema.json": run / "workflow" / "archive_assessment_workflow_state.json",
        "archive_assessment_input_manifest.schema.json": run / "workflow" / "archive_assessment_input_manifest.json",
        "archive_assessment_checkpoint.schema.json": next((run / "checkpoints").glob("*.json")),
    }
    for schema_name, artifact in artifacts.items():
        validate(json.loads(artifact.read_text()), json.loads((root / "schemas" / schema_name).read_text()))
