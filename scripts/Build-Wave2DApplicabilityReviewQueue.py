import argparse,csv,json
from pathlib import Path

ap=argparse.ArgumentParser()
ap.add_argument("--root",required=True)
ap.add_argument("--spec",required=True)
a=ap.parse_args()

root=Path(a.root).resolve()
spec=json.loads(Path(a.spec).read_text(encoding="utf-8"))

source=root/spec["source_decisions"]
if not source.exists():
    raise SystemExit(f"Missing applicability decisions: {source}")

rows=list(csv.DictReader(source.open(encoding="utf-8-sig",newline="")))
review=[r for r in rows if (r.get("decision") or "").strip().upper()=="REVIEW_REQUIRED"]

queue=root/spec["review_queue"]
queue.parent.mkdir(parents=True,exist_ok=True)
fields=[
    "wave","control_id","control_name","target_id","repository_name",
    "current_decision","current_rationale","decision_owner","decision_source",
    "human_decision","human_rationale","human_decision_owner","human_decision_source"
]
with queue.open("w",newline="",encoding="utf-8") as f:
    w=csv.DictWriter(f,fieldnames=fields)
    w.writeheader()
    for r in review:
        w.writerow({
            "wave":"2D",
            "control_id":r["control_id"],
            "control_name":r["control_name"],
            "target_id":r["target_id"],
            "repository_name":r["repository_name"],
            "current_decision":"REVIEW_REQUIRED",
            "current_rationale":r.get("rationale",""),
            "decision_owner":r.get("decision_owner",""),
            "decision_source":r.get("decision_source",""),
            "human_decision":"",
            "human_rationale":"",
            "human_decision_owner":"",
            "human_decision_source":""
        })

template=root/spec["review_template"]
template.write_text(queue.read_text(encoding="utf-8"),encoding="utf-8")

print(json.dumps({
    "status":"PASS",
    "review_required_count":len(review),
    "queue":str(queue),
    "template":str(template)
},indent=2))
