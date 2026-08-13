import argparse,csv,json
from pathlib import Path
import yaml

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--qualified",required=True)
    ap.add_argument("--scope-registry",required=True)
    ap.add_argument("--outdir",required=True)
    a=ap.parse_args()

    with Path(a.qualified).open(encoding="utf-8-sig",newline="") as fh:
        rows=list(csv.DictReader(fh))

    reg=yaml.safe_load(Path(a.scope_registry).read_text(encoding="utf-8")) or {}
    targets={c["control_id"]:c for c in reg.get("controls",[]) if c.get("scope") in {"EMS","ORGANIZATION"}}

    best={}
    for r in rows:
        if str(r.get("is_best_candidate","")).lower()!="true":
            continue
        best[r["control_id"]]=r

    out=Path(a.outdir);out.mkdir(parents=True,exist_ok=True)

    final=[]
    gaps=[]
    for cid,c in sorted(targets.items()):
        r=best.get(cid)
        if not r:
            gaps.append({
                "control_id":cid,"control_name":c["control_name"],"scope":c["scope"],
                "gap_reason":"NO_CANDIDATE_EVIDENCE","source_class":"","sufficiency":"","best_source":""
            })
            continue

        final.append(r)
        if str(r.get("promotion_eligible","")).lower()!="true":
            gaps.append({
                "control_id":cid,
                "control_name":c["control_name"],
                "scope":c["scope"],
                "gap_reason":"EVIDENCE_NOT_PROMOTION_ELIGIBLE",
                "source_class":r.get("source_class",""),
                "sufficiency":r.get("sufficiency",""),
                "best_source":r.get("source_file","")
            })

    if final:
        with (out/"qualified_best_candidates.csv").open("w",newline="",encoding="utf-8") as fh:
            w=csv.DictWriter(fh,fieldnames=list(final[0].keys()));w.writeheader();w.writerows(final)

    gfields=["control_id","control_name","scope","gap_reason","source_class","sufficiency","best_source"]
    with (out/"qualified_evidence_gaps.csv").open("w",newline="",encoding="utf-8") as fh:
        w=csv.DictWriter(fh,fieldnames=gfields);w.writeheader();w.writerows(gaps)

    summary={
        "target_control_count":len(targets),
        "best_candidate_count":len(final),
        "promotion_eligible_count":sum(str(r.get("promotion_eligible","")).lower()=="true" for r in final),
        "gap_count":len(gaps),
        "source_class_counts":{},
        "sufficiency_counts":{}
    }
    for r in final:
        summary["source_class_counts"][r.get("source_class","")]=summary["source_class_counts"].get(r.get("source_class",""),0)+1
        summary["sufficiency_counts"][r.get("sufficiency","")]=summary["sufficiency_counts"].get(r.get("sufficiency",""),0)+1

    (out/"evidence_qualification_summary.json").write_text(json.dumps(summary,indent=2),encoding="utf-8")
    print(json.dumps(summary,indent=2))

if __name__=="__main__":main()
