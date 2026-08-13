import argparse,csv,json
from pathlib import Path
from datetime import datetime,timezone

ap=argparse.ArgumentParser()
ap.add_argument("--root",required=True)
ap.add_argument("--spec",required=True)
a=ap.parse_args()

root=Path(a.root).resolve()
spec=json.loads(Path(a.spec).read_text(encoding="utf-8"))

source_path=root/spec["source_decisions"]
review_path=root/spec["review_import"]

source=list(csv.DictReader(source_path.open(encoding="utf-8-sig",newline="")))
reviews=list(csv.DictReader(review_path.open(encoding="utf-8-sig",newline="")))
review_map={(r["control_id"],r["target_id"]):r for r in reviews}

updated=[]
reviewed=0
for r in source:
    key=(r["control_id"],r["target_id"])
    if (r.get("decision") or "").strip().upper()=="REVIEW_REQUIRED":
        h=review_map.get(key)
        if not h:
            raise SystemExit(f"Missing human decision for {key}")
        r["decision"]=h["human_decision"].strip().upper()
        r["rationale"]=h["human_rationale"].strip()
        r["decision_owner"]=h["human_decision_owner"].strip()
        r["decision_source"]=h["human_decision_source"].strip()
        reviewed+=1
    updated.append(r)

fields=list(source[0].keys())
with source_path.open("w",newline="",encoding="utf-8") as f:
    w=csv.DictWriter(f,fieldnames=fields)
    w.writeheader();w.writerows(updated)

remaining=sum(1 for r in updated if (r.get("decision") or "").strip().upper()=="REVIEW_REQUIRED")

record={
    "wave":"2D",
    "applied_at_utc":datetime.now(timezone.utc).isoformat(),
    "status":"PASS" if remaining==0 else "WARNING",
    "reviewed_row_count":reviewed,
    "remaining_review_required_count":remaining,
    "evaluation_performed":False,
    "promotion_performed":False
}
out=root/spec["final_review_record"]
out.parent.mkdir(parents=True,exist_ok=True)
out.write_text(json.dumps(record,indent=2),encoding="utf-8")
print(json.dumps(record,indent=2))
