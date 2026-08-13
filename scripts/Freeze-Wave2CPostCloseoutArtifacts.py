import argparse,json,hashlib,zipfile,csv
from pathlib import Path
from datetime import datetime,timezone

ap=argparse.ArgumentParser()
ap.add_argument("--root",required=True)
ap.add_argument("--spec",required=True)
ap.add_argument("--outdir",required=True)
a=ap.parse_args()

root=Path(a.root).resolve()
spec=json.loads(Path(a.spec).read_text(encoding="utf-8"))
out=Path(a.outdir).resolve()
out.mkdir(parents=True,exist_ok=True)

targets=[
    root/"generated"/"wave2c"/"annual-review-closeout"/"wave2c_closeout_certification.json",
    root/"generated"/"wave2c"/"annual-review-closeout"/"inheritance_status_reconciliation.json",
    root/"generated"/"wave2c"/"annual-review-closeout"/"promotion_record.json",
    root/"generated"/"wave2c"/"annual-review-closeout"/"review_record.json",
    root/"generated"/"wave2c"/"remediation_queue.csv",
    root/"generated"/"wave2"/"inheritance"/"inheritance_impact_report.json",
    root/"generated"/"wave2"/"inheritance"/"higher_scope_results.json"
]

for p in targets:
    if not p.exists():
        raise SystemExit(f"Freeze blocked: missing required artifact {p}")

def sha256(p):
    h=hashlib.sha256()
    with p.open("rb") as f:
        for c in iter(lambda:f.read(1024*1024),b""):h.update(c)
    return h.hexdigest()

manifest=[]
for p in targets:
    manifest.append({
        "path":str(p.relative_to(root)).replace("\\","/"),
        "size_bytes":p.stat().st_size,
        "sha256":sha256(p)
    })

manifest_obj={
    "wave":"2C",
    "frozen_at_utc":datetime.now(timezone.utc).isoformat(),
    "artifact_count":len(manifest),
    "control_results_changed":False,
    "artifacts":manifest
}
(out/"wave2c_frozen_artifact_manifest.json").write_text(json.dumps(manifest_obj,indent=2),encoding="utf-8")

with (out/"wave2c_frozen_artifact_manifest.csv").open("w",newline="",encoding="utf-8") as f:
    w=csv.DictWriter(f,fieldnames=["path","size_bytes","sha256"])
    w.writeheader();w.writerows(manifest)

zip_path=out/"ems-wave2c-post-closeout-artifacts.zip"
with zipfile.ZipFile(zip_path,"w",zipfile.ZIP_DEFLATED) as z:
    for p in targets:
        z.write(p,p.relative_to(root))
    z.write(out/"wave2c_frozen_artifact_manifest.json","release-manifest/wave2c_frozen_artifact_manifest.json")
    z.write(out/"wave2c_frozen_artifact_manifest.csv","release-manifest/wave2c_frozen_artifact_manifest.csv")

summary={
    "status":"PASS",
    "artifact_count":len(manifest),
    "zip_path":str(zip_path),
    "zip_sha256":sha256(zip_path),
    "control_results_changed":False
}
(out/"release_package_summary.json").write_text(json.dumps(summary,indent=2),encoding="utf-8")
print(json.dumps(summary,indent=2))
