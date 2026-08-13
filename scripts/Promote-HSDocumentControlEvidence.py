import argparse,csv,json,shutil
from pathlib import Path
import yaml

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--qualified",required=True)
    ap.add_argument("--envelopes",required=True)
    ap.add_argument("--evidence-root",required=True)
    ap.add_argument("--report",required=True)
    a=ap.parse_args()

    with Path(a.qualified).open(encoding="utf-8-sig",newline="") as fh:
        q={r["control_id"]:r for r in csv.DictReader(fh)}

    env={}
    with Path(a.envelopes).open(encoding="utf-8") as fh:
        for line in fh:
            if line.strip():
                e=json.loads(line);env[e["control_id"]]=e

    promoted=[]
    skipped=[]
    folder=Path(a.evidence_root)/"ems"
    folder.mkdir(parents=True,exist_ok=True)

    for cid,r in q.items():
        eligible=str(r["promotion_eligible"]).lower()=="true"
        if not eligible:
            skipped.append({"control_id":cid,"reason":"Not promotion eligible"})
            continue
        e=env[cid]
        dest=folder/f"{cid}.yaml"
        if dest.exists():
            shutil.copy2(dest, dest.with_suffix(dest.suffix+".pre-hs-document-control.bak"))
        payload={
            "evidence_id":e["evidence_id"],
            "control_id":cid,
            "scope":"EMS",
            "authority_id":"EMS-GOVERNANCE",
            "status":"PASS",
            "evidence_date":e["evidence_date"],
            "expires_on":None,
            "evidence_summary":f"HS-DOCUMENT-CONTROL collector satisfied all required assertions for {cid}.",
            "evidence_references":e["evidence_sources"],
            "notes":f"collector_id={e['collector_id']}; collector_version={e['collector_version']}"
        }
        dest.write_text(yaml.safe_dump(payload,sort_keys=False),encoding="utf-8")
        promoted.append({"control_id":cid,"destination":str(dest),"evidence_id":e["evidence_id"]})

    result={"promoted_count":len(promoted),"skipped_count":len(skipped),"promoted":promoted,"skipped":skipped}
    Path(a.report).write_text(json.dumps(result,indent=2),encoding="utf-8")
    print(json.dumps(result,indent=2))

if __name__=="__main__":main()
