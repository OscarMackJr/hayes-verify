from __future__ import annotations

import json
import subprocess
import sys
import zipfile
from pathlib import Path


def test_cli_assess_status_and_resume_surface(tmp_path:Path)->None:
    archive=tmp_path/'archive.zip'
    with zipfile.ZipFile(archive,'w') as z:z.writestr('x.txt','x')
    (tmp_path/'ems/registry').mkdir(parents=True); (tmp_path/'ems/registry/control_catalog.yaml').write_text('controls: []\n')
    command=[sys.executable,'-m','hayes_verify.archive_assessment','assess',str(archive),'--output-root',str(tmp_path/'out'),'--hayes-authority-root',str(Path(__file__).resolve().parents[1]),'--ems-authority-root',str(tmp_path/'ems'),'--non-production','--json']
    result=subprocess.run(command,capture_output=True,text=True,check=True); payload=json.loads(result.stdout); assert payload['workflow_status']=='AWAITING_HUMAN_INPUT'
    run=payload['run_dir']; status=subprocess.run([sys.executable,'-m','hayes_verify.archive_assessment','status',run,'--json'],capture_output=True,text=True,check=True); assert json.loads(status.stdout)['workflow_id']==payload['workflow_id']
    resumed=subprocess.run([sys.executable,'-m','hayes_verify.archive_assessment','resume',run,'--json'],capture_output=True,text=True,check=True); assert json.loads(resumed.stdout)['workflow_status']=='AWAITING_HUMAN_INPUT'

def test_cli_requires_non_production(tmp_path:Path)->None:
    archive=tmp_path/'archive.zip'
    with zipfile.ZipFile(archive,'w') as z:z.writestr('x.txt','x')
    result=subprocess.run([sys.executable,'-m','hayes_verify.archive_assessment','assess',str(archive),'--output-root',str(tmp_path/'out'),'--hayes-authority-root',str(Path(__file__).resolve().parents[1]),'--ems-authority-root',str(tmp_path/'none')],capture_output=True,text=True,check=False)
    assert result.returncode==3
