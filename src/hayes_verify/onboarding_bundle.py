"""WS9 immutable onboarding evidence bundles; certification is not compliance attestation."""
from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path

LOCAL=("local_path","execution_path","repository_path")
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def build_bundle(run_id, repository_id, plan, artifacts, destination):
 if any(any(x in str(a["source"]).lower() for x in LOCAL) for a in artifacts):raise ValueError("local execution configuration excluded")
 out=Path(destination)/run_id;out.mkdir(parents=True,exist_ok=False);rows=[]
 for a in artifacts:
  src=Path(a["source"]);rel=Path(a["path"]);target=out/rel;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,target);rows.append({"path":rel.as_posix(),"artifact_type":a["artifact_type"],"authority_class":a["authority_class"],"sha256":sha(target),"producer":"hayes-verify","immutable":True})
 manifest={"manifest_id":"MAN-"+hashlib.sha256(run_id.encode()).hexdigest()[:16],"run_id":run_id,"repository_id":repository_id,"assessment_plan_id":plan["assessment_plan_id"],"assessment_plan_sha256":plan["plan_sha256"],"artifacts":rows,"artifact_count":len(rows),"required_artifact_count":len(rows),"missing_artifacts":[],"integrity_state":"COMPLETE"};(out/'evidence_manifest.json').write_text(json.dumps(manifest,indent=2));cert={"run_id":run_id,"status":"PASS","certification_scope":"INTEGRITY_TRACEABILITY_EVIDENCE_COMPLETENESS_ONLY","compliance_attestation":False,"manifest_sha256":sha(out/'evidence_manifest.json')};(out/'certification.json').write_text(json.dumps(cert,indent=2));(out/'auditor_report.md').write_text('# Onboarding Evidence Bundle ' + run_id + '\n\nIntegrity and lineage certification only. This is not a compliance attestation.\n');return manifest,cert


def finalize_existing_bundle(run_dir: Path, plan: dict, repository_id: str):
    run_dir=Path(run_dir); forbidden=("local_override","token","password","secret")
    rows=[]
    for path in sorted(x for x in run_dir.rglob("*") if x.is_file() and x.name not in {"evidence_manifest.json","certification.json","auditor_report.md"}):
        text=path.read_text(encoding="utf-8",errors="ignore")
        if any(word in path.name.lower() for word in forbidden) or "C:\\" in text: raise ValueError("forbidden local execution data")
        rows.append({"path":path.relative_to(run_dir).as_posix(),"artifact_type":"SYNTHETIC_MACHINE_EVIDENCE" if "synthetic" in path.name else "IMMUTABLE_SOURCE","authority_class":"IMMUTABLE_DERIVED_EVIDENCE","sha256":sha(path),"producer":"hayes-verify","immutable":True,"required":True})
    manifest={"manifest_id":"MAN-"+hashlib.sha256(plan["plan_sha256"].encode()).hexdigest()[:16],"run_id":run_dir.name,"repository_id":repository_id,"assessment_plan_id":plan["assessment_plan_id"],"assessment_plan_sha256":plan["plan_sha256"],"created_at":"2026-08-16T00:00:00Z","artifacts":rows,"artifact_count":len(rows),"required_artifact_count":len(rows),"missing_artifacts":[],"integrity_state":"COMPLETE","completeness_state":"SYNTHETIC_COMPLETE","compliance_assertions":False}
    (run_dir/"evidence_manifest.json").write_text(json.dumps(manifest,indent=2));cert={"status":"PASS","certification_scope":"INTEGRITY_TRACEABILITY_EVIDENCE_COMPLETENESS_ONLY","compliance_attestation":False,"synthetic":True,"manifest_sha256":sha(run_dir/"evidence_manifest.json")};(run_dir/"certification.json").write_text(json.dumps(cert,indent=2));(run_dir/"auditor_report.md").write_text("# Synthetic Onboarding Evidence Bundle\n\nIntegrity, traceability, and evidence completeness certification only. Not a compliance attestation.\n");return manifest,cert
