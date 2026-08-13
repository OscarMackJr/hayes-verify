import argparse,csv,json,shutil
from pathlib import Path
import yaml

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--candidates",required=True)
    ap.add_argument("--proposed-dir",required=True)
    ap.add_argument("--evidence-root",required=True)
    ap.add_argument("--report",required=True)
    ap.add_argument("--min-confidence",type=float,default=0.90)
    a=ap.parse_args()

    with Path(a.candidates).open(encoding="utf-8-sig",newline="") as fh:
        rows=list(csv.DictReader(fh))
    best={r["control_id"]:r for r in rows if str(r.get("is_best_candidate","")).lower()=="true"}

    promoted=[];skipped=[]
    for cid,r in best.items():
        conf=float(r["confidence"])
        status=r["candidate_status"]
        if conf < a.min_confidence or status not in {"PASS","WARNING"}:
            skipped.append({"control_id":cid,"reason":"Below confidence threshold or not affirmative"})
            continue
        src=Path(a.proposed_dir)/f"{cid}.yaml"
        if not src.exists():
            skipped.append({"control_id":cid,"reason":"Proposed record missing"})
            continue
        d=yaml.safe_load(src.read_text(encoding="utf-8"))
        scope=d["scope"]
        folder=Path(a.evidence_root)/("ems" if scope=="EMS" else "organization")
        folder.mkdir(parents=True,exist_ok=True)
        dest=folder/f"{cid}.yaml"
        if dest.exists():
            shutil.copy2(dest, dest.with_suffix(dest.suffix+".pre-discovery-promotion.bak"))
        shutil.copy2(src,dest)
        promoted.append({
            "control_id":cid,
            "status":status,
            "confidence":conf,
            "destination":str(dest),
            "source_evidence":r["source_file"]
        })

    result={
        "promoted_count":len(promoted),
        "skipped_count":len(skipped),
        "promoted":promoted,
        "skipped":skipped
    }
    Path(a.report).write_text(json.dumps(result,indent=2),encoding="utf-8")
    print(json.dumps(result,indent=2))

if __name__=="__main__":main()
