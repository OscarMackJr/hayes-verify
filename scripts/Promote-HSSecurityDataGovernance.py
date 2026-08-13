import argparse,csv,json,shutil
from pathlib import Path
def main():
    ap=argparse.ArgumentParser();ap.add_argument("--qualified",required=True);ap.add_argument("--matrix",required=True);ap.add_argument("--evidence-root",required=True);ap.add_argument("--report",required=True);a=ap.parse_args()
    with Path(a.qualified).open(encoding="utf-8-sig",newline="") as f:q=list(csv.DictReader(f))
    with Path(a.matrix).open(encoding="utf-8-sig",newline="") as f:m=list(csv.DictReader(f))
    by={}
    for r in m:by.setdefault(r["control_id"],[]).append(r)
    folder=Path(a.evidence_root)/"organization";folder.mkdir(parents=True,exist_ok=True)
    prom=[];skip=[]
    for r in q:
        cid=r["control_id"]
        if str(r["promotion_eligible"]).lower()!="true":
            skip.append({"control_id":cid,"reason":"Not promotion eligible after operating-evidence qualification"});continue
        refs=[]
        for x in by.get(cid,[]):refs.extend([s for s in x["operating_sources"].split(";") if s])
        dest=folder/f"{cid}.yaml"
        if dest.exists():shutil.copy2(dest,dest.with_suffix(dest.suffix+".pre-security-data-governance.bak"))
        payload={"control_id":cid,"scope":"ORGANIZATION","status":"PASS","authority_id":"SECURITY-DATA-GOVERNANCE",
                 "evidence_class":"OPERATING_EVIDENCE","evidence_references":sorted(set(refs)),
                 "notes":"Promoted by Wave 2B.2.6 after assertion-level operating-evidence qualification."}
        dest.write_text(json.dumps(payload,indent=2),encoding="utf-8");prom.append({"control_id":cid,"destination":str(dest)})
    result={"promoted_count":len(prom),"skipped_count":len(skip),"promoted":prom,"skipped":skip}
    Path(a.report).write_text(json.dumps(result,indent=2),encoding="utf-8");print(json.dumps(result,indent=2))
if __name__=="__main__":main()
