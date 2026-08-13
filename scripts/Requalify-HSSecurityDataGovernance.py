import argparse,csv,json
from pathlib import Path

TARGETS={"EMS-CTRL-063","EMS-CTRL-065","EMS-CTRL-066"}

ap=argparse.ArgumentParser()
ap.add_argument("--base-matrix",required=True)
ap.add_argument("--register-evidence",required=True)
ap.add_argument("--outdir",required=True)
a=ap.parse_args()

with Path(a.base_matrix).open(encoding="utf-8-sig",newline="") as f:
    base=list(csv.DictReader(f))
with Path(a.register_evidence).open(encoding="utf-8-sig",newline="") as f:
    reg=list(csv.DictReader(f))

regmap={(r["control_id"],r["assertion"]):r for r in reg}
merged=[]

for r in base:
    key=(r["control_id"],r["assertion"])
    if r["control_id"] in TARGETS and key in regmap and str(r["operating_evidence_sufficient"]).lower()!="true":
        rr=regmap[key]
        if str(rr["operating_evidence_sufficient"]).lower()=="true":
            r["operating_evidence_count"]=str(int(r.get("operating_evidence_count") or 0)+1)
            r["operating_evidence_sufficient"]="True"
            prior=r.get("operating_sources","")
            r["operating_sources"]=";".join(x for x in [prior,rr["operating_source"]] if x)
    merged.append(r)

out=Path(a.outdir); out.mkdir(parents=True,exist_ok=True)

with (out/"assertion_evidence_matrix_requalified.csv").open("w",newline="",encoding="utf-8") as f:
    w=csv.DictWriter(f,fieldnames=merged[0].keys())
    w.writeheader(); w.writerows(merged)

by={}
for r in merged:
    by.setdefault(r["control_id"],[]).append(r)

qualified=[]
gaps=[]
for cid,items in sorted(by.items()):
    good=bool(items) and all(str(x["operating_evidence_sufficient"]).lower()=="true" for x in items)
    qualified.append({
        "control_id":cid,
        "control_name":items[0]["control_name"],
        "scope":items[0]["scope"],
        "assertion_count":len(items),
        "assertions_with_operating_evidence":sum(str(x["operating_evidence_sufficient"]).lower()=="true" for x in items),
        "status":"PASS" if good else "WARNING",
        "sufficiency":"SUFFICIENT" if good else "INSUFFICIENT",
        "promotion_eligible":good
    })
    if not good:
        gaps.append({
            "control_id":cid,
            "control_name":items[0]["control_name"],
            "scope":items[0]["scope"],
            "missing_assertions":";".join(x["assertion"] for x in items if str(x["operating_evidence_sufficient"]).lower()!="true")
        })

with (out/"qualified_security_data_governance_requalified.csv").open("w",newline="",encoding="utf-8") as f:
    w=csv.DictWriter(f,fieldnames=list(qualified[0].keys()))
    w.writeheader(); w.writerows(qualified)

with (out/"security_data_governance_gaps_requalified.csv").open("w",newline="",encoding="utf-8") as f:
    fields=["control_id","control_name","scope","missing_assertions"]
    w=csv.DictWriter(f,fieldnames=fields)
    w.writeheader(); w.writerows(gaps)

summary={
    "control_count":len(qualified),
    "promotion_eligible_count":sum(str(x["promotion_eligible"]).lower()=="true" for x in qualified),
    "gap_count":len(gaps)
}
(out/"qualification_summary_requalified.json").write_text(json.dumps(summary,indent=2),encoding="utf-8")
print(json.dumps(summary,indent=2))
