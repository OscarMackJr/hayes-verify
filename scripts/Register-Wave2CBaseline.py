import argparse,json,hashlib,subprocess
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
    raise SystemExit(f"Baseline registration blocked: expected branch {spec['expected_branch']}, current={branch}")

head=run("git","rev-parse","HEAD")
origin=run("git","rev-parse","origin/main")
if head!=origin:
    raise SystemExit(f"Baseline registration blocked: HEAD {head} != origin/main {origin}")

tag=spec["release_tag"]
tag_sha=run("git","rev-list","-n","1",tag)
if tag_sha!=head:
    raise SystemExit(f"Baseline registration blocked: tag {tag} points to {tag_sha}, expected {head}")

paths={
    "release_zip":root/spec["release_zip"],
    "release_manifest":root/spec["release_manifest"],
    "post_merge_certification":root/spec["post_merge_certification"],
    "release_summary":root/spec["release_summary"],
}
for name,p in paths.items():
    if not p.exists():
        raise SystemExit(f"Baseline registration blocked: missing {name}: {p}")

cert=json.loads(paths["post_merge_certification"].read_text(encoding="utf-8"))
summary=json.loads(paths["release_summary"].read_text(encoding="utf-8"))

if cert.get("status")!="PASS":
    raise SystemExit("Baseline registration blocked: post-merge certification is not PASS.")
if cert.get("merge_commit_sha")!=head:
    raise SystemExit("Baseline registration blocked: certification merge commit does not match current main.")
if cert.get("release")!=tag:
    raise SystemExit("Baseline registration blocked: certification release tag mismatch.")
if summary.get("status")!="PASS":
    raise SystemExit("Baseline registration blocked: release summary is not PASS.")

def sha256(p):
    h=hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda:f.read(1024*1024),b""):
            h.update(chunk)
    return h.hexdigest()

record={
    "wave":"2C",
    "release_tag":tag,
    "status":"PASS",
    "registered_at_utc":datetime.now(timezone.utc).isoformat(),
    "branch":"main",
    "main_commit_sha":head,
    "tag_commit_sha":tag_sha,
    "release_zip":str(paths["release_zip"]),
    "release_zip_sha256":sha256(paths["release_zip"]),
    "release_manifest":str(paths["release_manifest"]),
    "release_manifest_sha256":sha256(paths["release_manifest"]),
    "post_merge_certification_sha256":sha256(paths["post_merge_certification"]),
    "release_summary_sha256":sha256(paths["release_summary"]),
    "baseline_state":spec["next_wave_baseline"]["baseline_state"],
    "next_wave":spec["next_wave_baseline"]["next_wave"],
    "next_wave_baseline_tag":spec["next_wave_baseline"]["baseline_tag"],
    "control_results_changed":False
}
out=Path(a.out)
out.parent.mkdir(parents=True,exist_ok=True)
out.write_text(json.dumps(record,indent=2),encoding="utf-8")
print(json.dumps(record,indent=2))
