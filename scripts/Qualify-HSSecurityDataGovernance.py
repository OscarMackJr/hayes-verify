import argparse,csv,json
from pathlib import Path
EXPECTED={"EMS-CTRL-023","EMS-CTRL-024","EMS-CTRL-063","EMS-CTRL-065","EMS-CTRL-066"}
def main():
    ap=argparse.ArgumentParser();ap.add_argument("--matrix",required=True);ap.add_argument("--outdir",required=True);a=ap.parse_args()
    with Path(a.matrix).open(encoding="utf-8-sig",newline="") as f:rows=list(csv.DictReader(f))
    by={}
    for r in rows:by.setdefault(r["control_id"],[]).append(r)
    q=[];g=[]
    for cid in sorted(EXPECTED):
        items=by.get(cid,[])
        ok=bool(items) and all(str(x["operating_evidence_sufficient"]).lower()=="true" for x in items)
        name=items[0]["control_name"] if items else ""
        scope=items[0]["scope"] if items else "ORGANIZATION"
        q.append({"control_id":cid,"control_name":name,"scope":scope,"assertion_count":len(items),
                  "assertions_with_operating_evidence":sum(str(x["operating_evidence_sufficient"]).lower()=="true" for x in items),
                  "status":"PASS" if ok else "WARNING","sufficiency":"SUFFICIENT" if ok else "INSUFFICIENT","promotion_eligible":ok})
        if not ok:
            missing=[x["assertion"] for x in items if str(x["operating_evidence_sufficient"]).lower()!="true"]
            if not items:missing=["NO_ASSERTION_EVIDENCE"]
            g.append({"control_id":cid,"control_name":name,"scope":scope,"gap_reason":"OPERATING_EVIDENCE_MISSING","missing_assertions":";".join(missing)})
    out=Path(a.outdir);out.mkdir(parents=True,exist_ok=True)
    with (out/"qualified_security_data_governance.csv").open("w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=list(q[0].keys()));w.writeheader();w.writerows(q)
    with (out/"security_data_governance_gaps.csv").open("w",newline="",encoding="utf-8") as f:
        fields=["control_id","control_name","scope","gap_reason","missing_assertions"];w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(g)
    summary={"control_count":len(q),"promotion_eligible_count":sum(str(x["promotion_eligible"]).lower()=="true" for x in q),"gap_count":len(g)}
    (out/"qualification_summary.json").write_text(json.dumps(summary,indent=2),encoding="utf-8")
    print(json.dumps(summary,indent=2))
if __name__=="__main__":main()
