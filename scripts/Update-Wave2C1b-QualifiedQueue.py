import argparse,csv,json
from pathlib import Path

ap=argparse.ArgumentParser()
ap.add_argument("--queue",required=True)
ap.add_argument("--evidence",required=True)
ap.add_argument("--out",required=True)
a=ap.parse_args()

e=json.loads(Path(a.evidence).read_text(encoding="utf-8"))

with Path(a.queue).open(encoding="utf-8-sig",newline="") as f:
    rows=list(csv.DictReader(f))

found=False
for r in rows:
    if r.get("control_id")=="EMS-CTRL-072":
        found=True
        r["current_status"]=e["status"]
        r["evidence_sufficiency"]=e["sufficiency"]
        r["promotion_eligible"]="True" if e["promotion_eligible"] else "False"
        r["promotion_status"]=e["promotion_status"]
        r["remediation_state"]="OPEN"
        r["evidence_record_count"]=str(e["evidence_summary"]["record_count"])
        r["next_action"]="REVIEW_FOR_PROMOTION" if e["promotion_eligible"] else "REMEDIATE_GENERATION_PROVENANCE"

if not found:
    raise SystemExit("EMS-CTRL-072 not found in Wave 2C remediation queue.")

with Path(a.out).open("w",encoding="utf-8",newline="") as f:
    w=csv.DictWriter(f,fieldnames=list(rows[0].keys()))
    w.writeheader();w.writerows(rows)

print(json.dumps({
    "control_id":"EMS-CTRL-072",
    "promotion_eligible":e["promotion_eligible"],
    "promotion_status":e["promotion_status"],
    "remediation_state":"OPEN",
    "promotion_performed":False
},indent=2))
