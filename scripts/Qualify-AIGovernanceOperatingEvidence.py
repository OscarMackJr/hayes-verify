import argparse,csv,json
from pathlib import Path

EXPECTED={
"EMS-CTRL-007","EMS-CTRL-049","EMS-CTRL-050",
"EMS-CTRL-052","EMS-CTRL-053","EMS-CTRL-054"
}

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--matrix",required=True)
    ap.add_argument("--outdir",required=True)
    a=ap.parse_args()

    with Path(a.matrix).open(encoding="utf-8-sig",newline="") as fh:
        rows=list(csv.DictReader(fh))

    by={}
    for r in rows:
        by.setdefault(r["control_id"],[]).append(r)

    qualified=[];gaps=[]
    for cid in sorted(EXPECTED):
        items=by.get(cid,[])
        all_material=bool(items) and all(str(x["operating_evidence_sufficient"]).lower()=="true" for x in items)
        name=items[0]["control_name"] if items else ""
        scope=items[0]["scope"] if items else "ORGANIZATION"
        qualified.append({
            "control_id":cid,
            "control_name":name,
            "scope":scope,
            "assertion_count":len(items),
            "assertions_with_operating_evidence":sum(str(x["operating_evidence_sufficient"]).lower()=="true" for x in items),
            "status":"PASS" if all_material else "WARNING",
            "sufficiency":"SUFFICIENT" if all_material else "INSUFFICIENT",
            "promotion_eligible":all_material
        })
        if not all_material:
            missing=[x["assertion"] for x in items if str(x["operating_evidence_sufficient"]).lower()!="true"]
            if not items: missing=["NO_ASSERTION_EVIDENCE"]
            gaps.append({
                "control_id":cid,
                "control_name":name,
                "scope":scope,
                "gap_reason":"OPERATING_EVIDENCE_MISSING",
                "missing_assertions":";".join(missing)
            })

    out=Path(a.outdir);out.mkdir(parents=True,exist_ok=True)

    with (out/"qualified_ai_governance.csv").open("w",newline="",encoding="utf-8") as fh:
        w=csv.DictWriter(fh,fieldnames=list(qualified[0].keys()));w.writeheader();w.writerows(qualified)

    with (out/"ai_governance_gaps.csv").open("w",newline="",encoding="utf-8") as fh:
        fields=["control_id","control_name","scope","gap_reason","missing_assertions"]
        w=csv.DictWriter(fh,fieldnames=fields);w.writeheader();w.writerows(gaps)

    summary={
        "control_count":len(qualified),
        "promotion_eligible_count":sum(str(x["promotion_eligible"]).lower()=="true" for x in qualified),
        "gap_count":len(gaps)
    }
    (out/"qualification_summary.json").write_text(json.dumps(summary,indent=2),encoding="utf-8")
    print(json.dumps(summary,indent=2))

if __name__=="__main__":main()
