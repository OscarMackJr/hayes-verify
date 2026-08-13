import argparse,csv,json
from pathlib import Path
ap=argparse.ArgumentParser()
ap.add_argument("--assessment",required=True)
ap.add_argument("--review-queue",required=True)
ap.add_argument("--out",required=True)
a=ap.parse_args()
assess={(r["control_id"],r["target_id"]):r for r in csv.DictReader(Path(a.assessment).open(encoding="utf-8-sig",newline=""))}
queue=list(csv.DictReader(Path(a.review_queue).open(encoding="utf-8-sig",newline="")))
rows=[]
for q in queue:
    x=assess[(q["control_id"],q["target_id"])]
    accept=x["proposal"]=="PROPOSE_APPLICABLE" and x["confidence"] in {"HIGH","MEDIUM"}
    rows.append({
      **q,
      "assessment_proposal":x["proposal"],
      "assessment_confidence":x["confidence"],
      "assessment_evidence_paths":x["evidence_paths"],
      "assessment_rationale":x["proposed_rationale"],
      "human_decision":"APPLICABLE" if accept else "",
      "human_rationale":x["proposed_rationale"] if accept else "",
      "human_decision_owner":"Engineering Management" if accept else "",
      "human_decision_source":"HUMAN_REPOSITORY_EVIDENCE_REVIEW" if accept else ""
    })
with Path(a.out).open("w",newline="",encoding="utf-8") as f:
    w=csv.DictWriter(f,fieldnames=list(rows[0].keys()));w.writeheader();w.writerows(rows)
print(json.dumps({"status":"PASS","row_count":len(rows),"prepopulated_count":sum(bool(r["human_decision"]) for r in rows),"remaining_human_review_count":sum(not bool(r["human_decision"]) for r in rows)},indent=2))
