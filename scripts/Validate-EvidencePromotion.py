import argparse,csv,json,sys
from pathlib import Path

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--qualified-best",required=True)
    ap.add_argument("--report",required=True)
    a=ap.parse_args()

    with Path(a.qualified_best).open(encoding="utf-8-sig",newline="") as fh:
        rows=list(csv.DictReader(fh))

    errors=[]
    for r in rows:
        eligible=str(r.get("promotion_eligible","")).lower()=="true"
        if eligible:
            if r.get("source_class")!="OPERATING_EVIDENCE":
                errors.append(f"{r['control_id']}: eligible source is not OPERATING_EVIDENCE")
            if r.get("sufficiency")!="SUFFICIENT":
                errors.append(f"{r['control_id']}: eligible source is not SUFFICIENT")
            if float(r.get("confidence") or 0)<0.90:
                errors.append(f"{r['control_id']}: eligible confidence below 0.90")
            if r.get("candidate_status") not in {"PASS","WARNING"}:
                errors.append(f"{r['control_id']}: eligible status not PASS/WARNING")

    result={
        "status":"PASS" if not errors else "FAIL",
        "row_count":len(rows),
        "promotion_eligible_count":sum(str(r.get("promotion_eligible","")).lower()=="true" for r in rows),
        "errors":errors
    }
    Path(a.report).write_text(json.dumps(result,indent=2),encoding="utf-8")
    print(json.dumps(result,indent=2))
    sys.exit(1 if errors else 0)

if __name__=="__main__":main()
