import argparse,json,hashlib,zipfile
from pathlib import Path
from datetime import datetime,timezone

ap=argparse.ArgumentParser()
ap.add_argument("--root",required=True)
ap.add_argument("--spec",required=True)
ap.add_argument("--certification",required=True)
ap.add_argument("--outdir",required=True)
a=ap.parse_args()

root=Path(a.root).resolve()
spec=json.loads(Path(a.spec).read_text(encoding="utf-8"))
cert=json.loads(Path(a.certification).read_text(encoding="utf-8"))
out=Path(a.outdir).resolve()
out.mkdir(parents=True,exist_ok=True)

targets=[
    root/spec["closeout_certification"],
    root/spec["reconciliation_record"],
    root/spec["remediation_queue"],
    root/spec["inheritance_impact"],
    root/spec["higher_scope_results"],
    Path(a.certification)
]
for p in targets:
    if not p.exists():
        raise SystemExit(f"Freeze blocked: missing {p}")

def sha256(p):
    h=hashlib.sha256()
    with p.open("rb") as f:
        for c in iter(lambda:f.read(1024*1024),b""): h.update(c)
    return h.hexdigest()

artifacts=[]
for p in targets:
    try:
        rel=str(p.resolve().relative_to(root)).replace("\\","/")
    except ValueError:
        rel=p.name
    artifacts.append({"path":rel,"size_bytes":p.stat().st_size,"sha256":sha256(p)})

manifest={
    "wave":"2C",
    "release":spec["release"],
    "frozen_at_utc":datetime.now(timezone.utc).isoformat(),
    "merge_commit_sha":cert["merge_commit_sha"],
    "artifact_count":len(artifacts),
    "control_results_changed":False,
    "artifacts":artifacts
}
manifest_path=out/"wave2c_post_merge_manifest.json"
manifest_path.write_text(json.dumps(manifest,indent=2),encoding="utf-8")

zip_path=out/f"{spec['release']}.zip"
with zipfile.ZipFile(zip_path,"w",zipfile.ZIP_DEFLATED) as z:
    for p in targets:
        try:
            arc=str(p.resolve().relative_to(root)).replace("\\","/")
        except ValueError:
            arc=f"certification/{p.name}"
        z.write(p,arc)
    z.write(manifest_path,"release-manifest/wave2c_post_merge_manifest.json")

summary={
    "status":"PASS",
    "release":spec["release"],
    "merge_commit_sha":cert["merge_commit_sha"],
    "artifact_count":len(artifacts),
    "release_zip":str(zip_path),
    "release_zip_sha256":sha256(zip_path),
    "manifest_sha256":sha256(manifest_path),
    "control_results_changed":False
}
(out/"release_summary.json").write_text(json.dumps(summary,indent=2),encoding="utf-8")
print(json.dumps(summary,indent=2))
