import argparse,csv,json,sys
from pathlib import Path
import yaml

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--candidates",required=True)
    ap.add_argument("--proposed-dir",required=True)
    ap.add_argument("--report",required=True)
    ap.add_argument("--min-confidence",type=float,default=0.90)
    a=ap.parse_args()

    with Path(a.candidates).open(encoding="utf-8-sig",newline="") as fh:
        rows=list(csv.DictReader(fh))

    best={r["control_id"]:r for r in rows if str(r.get("is_best_candidate","")).lower()=="true"}
    errors=[];eligible=[]

    for cid,r in best.items():
        conf=float(r["confidence"])
        status=r["candidate_status"]
        p=Path(a.proposed_dir)/f"{cid}.yaml"
        if not p.exists():
            errors.append(f"{cid}: proposed evidence record missing")
            continue
        d=yaml.safe_load(p.read_text(encoding="utf-8"))
        if d.get("control_id")!=cid:
            errors.append(f"{cid}: proposed record control_id mismatch")
        if status in {"PASS","WARNING"} and conf>=a.min_confidence:
            eligible.append(cid)

    result={
        "status":"PASS" if not errors else "FAIL",
        "best_candidate_count":len(best),
        "auto_promote_eligible_count":len(eligible),
        "auto_promote_eligible_controls":sorted(eligible),
        "errors":errors
    }
    Path(a.report).write_text(json.dumps(result,indent=2),encoding="utf-8")
    print(json.dumps(result,indent=2))
    sys.exit(1 if errors else 0)

if __name__=="__main__":main()
