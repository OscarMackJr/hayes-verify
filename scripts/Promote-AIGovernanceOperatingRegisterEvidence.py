import argparse,json,shutil
from pathlib import Path

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--envelopes",required=True)
    ap.add_argument("--evidence-root",required=True)
    ap.add_argument("--report",required=True)
    a=ap.parse_args()

    rows=[json.loads(x) for x in Path(a.envelopes).read_text(encoding="utf-8").splitlines() if x.strip()]
    folder=Path(a.evidence_root)/"organization"; folder.mkdir(parents=True,exist_ok=True)
    promoted=[];skipped=[]

    for r in rows:
        cid=r["control_id"]
        if not r["promotion_eligible"]:
            skipped.append({"control_id":cid,"reason":r["reason"]}); continue
        dest=folder/f"{cid}.yaml"
        if dest.exists():
            shutil.copy2(dest,dest.with_suffix(dest.suffix+".pre-ai-governance-registers.bak"))
        dest.write_text(json.dumps(r,indent=2),encoding="utf-8")
        promoted.append({"control_id":cid,"destination":str(dest)})

    result={"promoted_count":len(promoted),"skipped_count":len(skipped),"promoted":promoted,"skipped":skipped}
    Path(a.report).write_text(json.dumps(result,indent=2),encoding="utf-8")
    print(json.dumps(result,indent=2))

if __name__=="__main__":main()
