import argparse,csv,json
from pathlib import Path
import yaml

ap=argparse.ArgumentParser()
ap.add_argument("--root",required=True)
ap.add_argument("--spec",required=True)
a=ap.parse_args()
root=Path(a.root).resolve()
spec=json.loads(Path(a.spec).read_text(encoding="utf-8"))
out=root/"generated"/"wave2d"/"scope-definition"
out.mkdir(parents=True,exist_ok=True)

def walk(obj):
    if isinstance(obj,dict):
        yield obj
        for v in obj.values(): yield from walk(v)
    elif isinstance(obj,list):
        for v in obj: yield from walk(v)

catalog_path=root/spec["control_catalog"]
repo_path=root/spec["repository_registry"]
if not catalog_path.exists(): raise SystemExit(f"Missing control catalog: {catalog_path}")
if not repo_path.exists(): raise SystemExit(f"Missing repository registry: {repo_path}")

catalog=yaml.safe_load(catalog_path.read_text(encoding="utf-8"))
controls={}
for d in walk(catalog):
    cid=d.get("control_id") or d.get("id")
    if isinstance(cid,str) and cid.startswith("EMS-CTRL-"):
        controls[cid]={
            "control_id":cid,
            "control_name":str(d.get("control_name") or d.get("name") or ""),
            "scope":str(d.get("scope") or d.get("control_scope") or ""),
            "source":"registry/control_catalog.yaml"
        }

with (out/"candidate_controls.csv").open("w",newline="",encoding="utf-8") as f:
    w=csv.DictWriter(f,fieldnames=["control_id","control_name","scope","source"])
    w.writeheader()
    for cid in sorted(controls): w.writerow(controls[cid])

repos=yaml.safe_load(repo_path.read_text(encoding="utf-8"))
targets={}
for d in walk(repos):
    name=d.get("repository_name") or d.get("name")
    rid=d.get("repository_id") or d.get("id")
    if isinstance(name,str) and name:
        key=str(rid or name)
        targets[key]={
            "target_id":key,
            "repository_name":name,
            "owner":str(d.get("owner") or ""),
            "tier":str(d.get("tier") or ""),
            "service_criticality":str(d.get("service_criticality") or ""),
            "production":str(d.get("production") if "production" in d else ""),
            "source":"registry/repository_registry.yaml"
        }

with (out/"candidate_targets.csv").open("w",newline="",encoding="utf-8") as f:
    w=csv.DictWriter(f,fieldnames=["target_id","repository_name","owner","tier","service_criticality","production","source"])
    w.writeheader()
    for key in sorted(targets): w.writerow(targets[key])

print(json.dumps({"status":"PASS","candidate_control_count":len(controls),"candidate_target_count":len(targets),"evaluation_performed":False,"promotion_performed":False},indent=2))
