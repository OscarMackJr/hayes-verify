import argparse,csv,json,shutil
from pathlib import Path

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--resolution",required=True)
    ap.add_argument("--evidence-root",required=True)
    ap.add_argument("--report",required=True)
    a=ap.parse_args()

    with Path(a.resolution).open(encoding="utf-8-sig",newline="") as fh:
        rows=list(csv.DictReader(fh))

    promoted=[];skipped=[]
    folder=Path(a.evidence_root)/"organization"
    folder.mkdir(parents=True,exist_ok=True)

    for r in rows:
        cid=r["control_id"]
        if str(r["promotion_eligible"]).lower()!="true":
            skipped.append({"control_id":cid,"reason":"Targeted operating evidence still missing"})
            continue
        refs=[x for x in r["operating_sources"].split(";") if x]
        dest=folder/f"{cid}.yaml"
        if dest.exists():
            shutil.copy2(dest,dest.with_suffix(dest.suffix+".pre-ai-governance-gap-remediation.bak"))
        payload={
            "control_id":cid,
            "scope":"ORGANIZATION",
            "status":"PASS",
            "authority_id":"ENGINEERING-LEADERSHIP",
            "evidence_class":"OPERATING_EVIDENCE",
            "evidence_references":refs,
            "notes":"Promoted by Wave 2B.2.5b after targeted operating-evidence gap resolution."
        }
        dest.write_text(json.dumps(payload,indent=2),encoding="utf-8")
        promoted.append({"control_id":cid,"destination":str(dest)})

    result={"promoted_count":len(promoted),"skipped_count":len(skipped),"promoted":promoted,"skipped":skipped}
    Path(a.report).write_text(json.dumps(result,indent=2),encoding="utf-8")
    print(json.dumps(result,indent=2))

if __name__=="__main__":main()
