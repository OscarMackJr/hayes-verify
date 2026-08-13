import argparse,json,csv
from pathlib import Path
ap=argparse.ArgumentParser();ap.add_argument("--envelopes",required=True);ap.add_argument("--outdir",required=True);a=ap.parse_args()
rows=[json.loads(x) for x in Path(a.envelopes).read_text(encoding="utf-8").splitlines() if x.strip()]
out=Path(a.outdir);out.mkdir(parents=True,exist_ok=True);q=[];g=[]
for e in rows:
    ok=e["status"]=="PASS" and e["evidence_class"]=="OPERATING_EVIDENCE" and all(v["result"]=="PASS" for v in e["assertions"].values()) and len(e["evidence_sources"])>0
    q.append({"control_id":e["control_id"],"control_name":e["control_name"],"status":e["status"],"source_class":"OPERATING_EVIDENCE","sufficiency":"SUFFICIENT" if ok else "INSUFFICIENT","promotion_eligible":ok,"evidence_id":e["evidence_id"],"evidence_sources":";".join(e["evidence_sources"])})
    if not ok:g.append({"control_id":e["control_id"],"control_name":e["control_name"],"status":e["status"],"gap_reason":"EVIDENCE_INTEGRITY_RELEASE_ASSERTIONS_INCOMPLETE"})
with (out/"qualified_evidence_integrity_release.csv").open("w",newline="",encoding="utf-8") as f:
    w=csv.DictWriter(f,fieldnames=list(q[0].keys()));w.writeheader();w.writerows(q)
with (out/"evidence_integrity_release_gaps.csv").open("w",newline="",encoding="utf-8") as f:
    w=csv.DictWriter(f,fieldnames=["control_id","control_name","status","gap_reason"]);w.writeheader();w.writerows(g)
summary={"control_count":len(q),"promotion_eligible_count":sum(x["promotion_eligible"] for x in q),"gap_count":len(g)}
(out/"qualification_summary.json").write_text(json.dumps(summary,indent=2),encoding="utf-8");print(json.dumps(summary,indent=2))
