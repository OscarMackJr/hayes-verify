"""RP1B controlled authority discovery and freeze helpers."""
from __future__ import annotations

import hashlib
import subprocess
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .archive_assessment import ArchiveWorkflowError
from .contract_hashing import CANONICAL_CONTRACT_HASH_ALGORITHM, sha256_canonical_contract_file


def _sha(p:Path): return hashlib.sha256(p.read_bytes()).hexdigest()
def _git(root:Path):
 try:return subprocess.run(['git','-C',str(root),'rev-parse','HEAD'],capture_output=True,text=True,check=True).stdout.strip()
 except (OSError,subprocess.CalledProcessError): return None
def discover_authority(hayes_root:Path,ems_root:Path)->dict[str,Any]:
 registry=hayes_root/'registry/wave2d_evaluator_registry_v1_11.json'; bindings=hayes_root/'registry/wave2d_runtime_bindings_v1_0.json'; request=hayes_root/'contracts/schemas/wave2d_evaluation_request.schema.json'; result=hayes_root/'contracts/schemas/wave2d_evaluation_result.schema.json'
 if not all(p.is_file() for p in (registry,bindings,request,result)): raise ArchiveWorkflowError('HAYES_AUTHORITY_UNAVAILABLE')
 if not ems_root.is_dir() or ems_root.resolve()==hayes_root.resolve(): raise ArchiveWorkflowError('EMS_AUTHORITY_UNAVAILABLE')
 ems_candidates=[ems_root/'registry/control_catalog.yaml',ems_root/'registry/policy_applicability.yaml',ems_root/'registry/policy_decisions.json',ems_root/'registry/adjudication_rules.json']
 ems_files=[p for p in ems_candidates if p.is_file()]
 if not ems_files: raise ArchiveWorkflowError('EMS_AUTHORITY_UNAVAILABLE')
 import json
 try:
  r=json.loads(registry.read_text()); b=json.loads(bindings.read_text())
 except json.JSONDecodeError as exc: raise ArchiveWorkflowError('invalid Hayes authority JSON') from exc
 return {'authority_context_version':'1.0','frozen_at':datetime.now(UTC).replace(microsecond=0).isoformat().replace('+00:00','Z'),'hayes_source_identity':'HAYES_CONTROLLED_ROOT','hayes_commit_sha':_git(hayes_root),'ems_source_identity':'EMS_CONTROLLED_ROOT','ems_commit_sha':_git(ems_root),'support_registry_version':r.get('registry_version'),'support_registry_sha256':_sha(registry),'runtime_binding_version':b.get('version'),'runtime_binding_sha256':_sha(bindings),'contract_hash_model':CANONICAL_CONTRACT_HASH_ALGORITHM,'request_contract_sha256':sha256_canonical_contract_file(request),'result_contract_sha256':sha256_canonical_contract_file(result),'relevant_ems_authorities':[{'relative_path':str(p.relative_to(ems_root)).replace('\\','/'),'sha256':_sha(p)} for p in ems_files]}
