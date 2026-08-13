import argparse,csv,json,hashlib,subprocess
from pathlib import Path
from datetime import datetime,timezone

ap=argparse.ArgumentParser()
ap.add_argument("--root",required=True)
ap.add_argument("--spec",required=True)
ap.add_argument("--out",required=True)
a=ap.parse_args()

root=Path(a.root).resolve()
spec=json.loads(Path(a.spec).read_text(encoding="utf-8"))

def run(*args):
    cp=subprocess.run(args,cwd=root,capture_output=True,text=True)
    if cp.returncode!=0:
        raise SystemExit(cp.stderr.strip() or cp.stdout.strip() or f"Command failed: {args}")
    return cp.stdout.strip()

branch=run("git","branch","--show-current")
if branch!=spec["expected_branch"]:
    raise SystemExit(f"Certification blocked: expected branch {spec['expected_branch']}, current={branch}")

cert_path=root/spec["closeout_certification"]
recon_path=root/spec["reconciliation_record"]
queue_path=root/spec["remediation_queue"]

for p in (cert_path,recon_path,queue_path):
    if not p.exists():
        raise SystemExit(f"Certification blocked: missing {p}")

cert=json.loads(cert_path.read_text(encoding="utf-8"))
recon=json.loads(recon_path.read_text(encoding="utf-8"))

checks={
    "closeout_status":cert.get("status")=="PASS",
    "wave2c_state":cert.get("wave2c_state")=="CLOSED",
    "open_remediation_count":int(cert.get("open_remediation_count",-1))==0,
    "inheritance_validation":cert.get("inheritance_validation")=="PASS",
    "reconciliation_status":recon.get("status")=="PASS",
    "no_control_results_changed":recon.get("control_results_changed") is False,
    "no_population_changed":recon.get("remediation_population_changed") is False,
    "no_evidence_changed":recon.get("evidence_artifacts_changed") is False
}
failed=[k for k,v in checks.items() if not v]
if failed:
    raise SystemExit(f"Certification blocked: failed checks {failed}")

with queue_path.open(encoding="utf-8-sig",newline="") as f:
    rows=list(csv.DictReader(f))
open_rows=[r for r in rows if r.get("remediation_state")=="OPEN"]
if open_rows:
    raise SystemExit(f"Certification blocked: open remediation rows remain {[r.get('control_id') for r in open_rows]}")

def sha256(p):
    h=hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda:f.read(1024*1024),b""):
            h.update(chunk)
    return h.hexdigest()

status_lines=run("git","status","--porcelain").splitlines()
changed=[x[3:] if len(x)>3 else x for x in status_lines if x]

result={
    "wave":"2C",
    "status":"PASS",
    "certified_at_utc":datetime.now(timezone.utc).isoformat(),
    "branch":branch,
    "head_sha":run("git","rev-parse","HEAD"),
    "closeout_status":"PASS",
    "wave2c_state":"CLOSED",
    "open_remediation_count":0,
    "inheritance_validation":"PASS",
    "closeout_certification_sha256":sha256(cert_path),
    "reconciliation_record_sha256":sha256(recon_path),
    "remediation_queue_sha256":sha256(queue_path),
    "working_tree_changed_path_count":len(changed),
    "working_tree_changed_paths":changed,
    "control_results_changed":False
}
Path(a.out).parent.mkdir(parents=True,exist_ok=True)
Path(a.out).write_text(json.dumps(result,indent=2),encoding="utf-8")
print(json.dumps(result,indent=2))
