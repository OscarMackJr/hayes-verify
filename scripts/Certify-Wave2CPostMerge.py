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
    raise SystemExit(f"Post-merge certification blocked: expected branch {spec['expected_branch']}, current={branch}")

status=run("git","status","--porcelain")
if status.strip():
    raise SystemExit("Post-merge certification blocked: working tree is not clean.")

head=run("git","rev-parse","HEAD")
remote=run("git","rev-parse",spec["expected_remote"])
if head!=remote:
    raise SystemExit(f"Post-merge certification blocked: HEAD {head} != {spec['expected_remote']} {remote}")

paths={
    "closeout_certification":root/spec["closeout_certification"],
    "reconciliation_record":root/spec["reconciliation_record"],
    "remediation_queue":root/spec["remediation_queue"],
    "inheritance_impact":root/spec["inheritance_impact"],
    "higher_scope_results":root/spec["higher_scope_results"],
}
for name,p in paths.items():
    if not p.exists():
        raise SystemExit(f"Post-merge certification blocked: missing {name}: {p}")

closeout=json.loads(paths["closeout_certification"].read_text(encoding="utf-8"))
recon=json.loads(paths["reconciliation_record"].read_text(encoding="utf-8"))

required=spec["required_state"]
for k,v in required.items():
    if closeout.get(k)!=v:
        raise SystemExit(f"Post-merge certification blocked: closeout {k}={closeout.get(k)!r}, expected {v!r}")

if recon.get("status")!="PASS":
    raise SystemExit("Post-merge certification blocked: reconciliation status is not PASS.")
for field in ("control_results_changed","remediation_population_changed","evidence_artifacts_changed"):
    if recon.get(field) is not False:
        raise SystemExit(f"Post-merge certification blocked: reconciliation says {field} changed.")

with paths["remediation_queue"].open(encoding="utf-8-sig",newline="") as f:
    rows=list(csv.DictReader(f))
open_rows=[r for r in rows if r.get("remediation_state")=="OPEN"]
if open_rows:
    raise SystemExit(f"Post-merge certification blocked: open remediation remains {[r.get('control_id') for r in open_rows]}")

def sha256(p):
    h=hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda:f.read(1024*1024),b""):
            h.update(chunk)
    return h.hexdigest()

tag=spec["release"]
tag_exists=subprocess.run(["git","rev-parse","-q","--verify",f"refs/tags/{tag}"],cwd=root,capture_output=True,text=True).returncode==0
if tag_exists:
    tag_sha=run("git","rev-list","-n","1",tag)
    if tag_sha!=head:
        raise SystemExit(f"Post-merge certification blocked: existing tag {tag} points to {tag_sha}, not HEAD {head}")

result={
    "wave":"2C",
    "release":tag,
    "status":"PASS",
    "certified_at_utc":datetime.now(timezone.utc).isoformat(),
    "branch":branch,
    "merge_commit_sha":head,
    "origin_main_sha":remote,
    "closeout_status":"PASS",
    "wave2c_state":"CLOSED",
    "open_remediation_count":0,
    "inheritance_validation":"PASS",
    "closeout_certification_sha256":sha256(paths["closeout_certification"]),
    "reconciliation_record_sha256":sha256(paths["reconciliation_record"]),
    "remediation_queue_sha256":sha256(paths["remediation_queue"]),
    "inheritance_impact_sha256":sha256(paths["inheritance_impact"]),
    "higher_scope_results_sha256":sha256(paths["higher_scope_results"]),
    "tag_exists":tag_exists,
    "tag_ready":True,
    "control_results_changed":False
}
Path(a.out).parent.mkdir(parents=True,exist_ok=True)
Path(a.out).write_text(json.dumps(result,indent=2),encoding="utf-8")
print(json.dumps(result,indent=2))
