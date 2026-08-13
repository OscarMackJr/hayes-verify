#!/usr/bin/env python3
import argparse,csv,json
from pathlib import Path
ap=argparse.ArgumentParser(); ap.add_argument("--input",required=True); ap.add_argument("--outdir",required=True); a=ap.parse_args()
rows=[json.loads(x) for x in Path(a.input).read_text(encoding="utf-8").splitlines() if x.strip()]
out=Path(a.outdir); out.mkdir(parents=True,exist_ok=True)
q=[]; gaps=[]
for r in rows:
    eligible=(r.get("collector_status")=="PASS" and r.get("promotion_candidate") is True and
              all(v.get("result")=="PASS" for v in r.get("assertions",{}).values()))
    row={"control_id":r["control_id"],"control_name":r["control_name"],"scope":r["scope"],
         "status":r["collector_status"],"sufficiency":"SUFFICIENT" if eligible else "INSUFFICIENT",
         "promotion_eligible":eligible}
    q.append(row)
    if not eligible:
        gaps.append({**row,"gap_reason":"AI_GOVERNANCE_ASSERTIONS_INCOMPLETE"})
with (out/"qualification.csv").open("w",newline="",encoding="utf-8") as f:
    w=csv.DictWriter(f,fieldnames=q[0].keys()); w.writeheader(); w.writerows(q)
with (out/"gaps.csv").open("w",newline="",encoding="utf-8") as f:
    fields=["control_id","control_name","scope","status","sufficiency","promotion_eligible","gap_reason"]
    w=csv.DictWriter(f,fieldnames=fields); w.writeheader(); w.writerows(gaps)
summary={"control_count":len(q),"promotion_eligible_count":sum(1 for x in q if x["promotion_eligible"]),"gap_count":len(gaps)}
(out/"qualification_summary.json").write_text(json.dumps(summary,indent=2),encoding="utf-8")
print(json.dumps(summary,indent=2))
