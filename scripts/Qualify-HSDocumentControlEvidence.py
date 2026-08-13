import argparse,json,csv
from pathlib import Path
import yaml

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--envelopes",required=True)
    ap.add_argument("--outdir",required=True)
    a=ap.parse_args()

    out=Path(a.outdir);out.mkdir(parents=True,exist_ok=True)
    rows=[]
    with Path(a.envelopes).open(encoding="utf-8") as fh:
        for line in fh:
            if line.strip(): rows.append(json.loads(line))

    q=[]
    gaps=[]
    for e in rows:
        all_pass=all(v["result"]=="PASS" for v in e["assertions"].values())
        eligible=(
            e["evidence_class"]=="OPERATING_EVIDENCE"
            and e["status"]=="PASS"
            and all_pass
            and len(e["evidence_sources"])>0
        )
        q.append({
            "control_id":e["control_id"],
            "control_name":e["control_name"],
            "status":e["status"],
            "source_class":"OPERATING_EVIDENCE",
            "sufficiency":"SUFFICIENT" if eligible else "INSUFFICIENT",
            "promotion_eligible":eligible,
            "evidence_id":e["evidence_id"],
            "evidence_sources":";".join(e["evidence_sources"])
        })
        if not eligible:
            gaps.append({
                "control_id":e["control_id"],
                "control_name":e["control_name"],
                "status":e["status"],
                "gap_reason":"DOCUMENT_CONTROL_ASSERTIONS_INCOMPLETE"
            })

    with (out/"qualified_document_control.csv").open("w",newline="",encoding="utf-8") as fh:
        w=csv.DictWriter(fh,fieldnames=list(q[0].keys()));w.writeheader();w.writerows(q)

    with (out/"document_control_gaps.csv").open("w",newline="",encoding="utf-8") as fh:
        w=csv.DictWriter(fh,fieldnames=["control_id","control_name","status","gap_reason"]);w.writeheader();w.writerows(gaps)

    summary={
        "control_count":len(q),
        "promotion_eligible_count":sum(x["promotion_eligible"] for x in q),
        "gap_count":len(gaps)
    }
    (out/"qualification_summary.json").write_text(json.dumps(summary,indent=2),encoding="utf-8")
    print(json.dumps(summary,indent=2))

if __name__=="__main__":main()
