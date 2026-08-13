import argparse,csv,json,shutil,yaml
from pathlib import Path
ap=argparse.ArgumentParser();ap.add_argument("--qualified",required=True);ap.add_argument("--envelopes",required=True);ap.add_argument("--evidence-root",required=True);ap.add_argument("--report",required=True);a=ap.parse_args()
with Path(a.qualified).open(encoding="utf-8-sig",newline="") as f:q={r["control_id"]:r for r in csv.DictReader(f)}
env={}
for x in Path(a.envelopes).read_text(encoding="utf-8").splitlines():
    if x.strip():
        e=json.loads(x);env[e["control_id"]]=e
folder=Path(a.evidence_root)/"ems";folder.mkdir(parents=True,exist_ok=True);prom=[];skip=[]
for cid,r in q.items():
    if str(r["promotion_eligible"]).lower()!="true":skip.append({"control_id":cid,"reason":"Not promotion eligible"});continue
    e=env[cid];dest=folder/f"{cid}.yaml"
    if dest.exists():shutil.copy2(dest,dest.with_suffix(dest.suffix+".pre-hs-continuous-compliance.bak"))
    payload={"evidence_id":e["evidence_id"],"control_id":cid,"scope":"EMS","authority_id":"EMS-GOVERNANCE","status":"PASS","evidence_date":e["evidence_date"],"expires_on":None,"evidence_summary":f"HS-CONTINUOUS-COMPLIANCE satisfied all required assertions for {cid}.","evidence_references":e["evidence_sources"],"notes":"collector_id=HS-CONTINUOUS-COMPLIANCE; collector_version=2B2.3"}
    dest.write_text(yaml.safe_dump(payload,sort_keys=False),encoding="utf-8");prom.append({"control_id":cid,"destination":str(dest)})
res={"promoted_count":len(prom),"skipped_count":len(skip),"promoted":prom,"skipped":skip}
Path(a.report).write_text(json.dumps(res,indent=2),encoding="utf-8");print(json.dumps(res,indent=2))
