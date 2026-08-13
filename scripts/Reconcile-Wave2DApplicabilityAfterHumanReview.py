import argparse,csv,json
from pathlib import Path
from datetime import datetime,timezone

ap=argparse.ArgumentParser()
ap.add_argument("--root",required=True)
ap.add_argument("--spec",required=True)
a=ap.parse_args()
root=Path(a.root).resolve()
spec=json.loads(Path(a.spec).read_text(encoding="utf-8"))

decisions=list(csv.DictReader((root/spec["source_decisions"]).open(encoding="utf-8-sig",newline="")))
matrix=list(csv.DictReader((root/spec["adjudicated_matrix"]).open(encoding="utf-8-sig",newline="")))
dmap={(r["control_id"],r["target_id"]):r for r in decisions}

errors=[]
rows=[]
for r in matrix:
    key=(r["control_id"],r["target_id"])
    d=dmap.get(key)
    if not d:
        errors.append(f"missing decision for {key}")
        continue
    state=(d.get("decision") or "").strip().upper()
    if state not in {"APPLICABLE","NOT_APPLICABLE"}:
        errors.append(f"unresolved decision {state} for {key}")
        continue

    out=dict(r)
    out["applicability_state"]=state
    out["applicability_rationale"]=d.get("rationale","")
    out["applicability_owner"]=d.get("decision_owner","")
    out["evaluation_state"]="NOT_STARTED"
    out["evidence_state"]="NOT_COLLECTED"
    out["result_state"]="NOT_EVALUATED"
    out["promotion_state"]="NOT_PROMOTED"
    rows.append(out)

if errors:
    print(json.dumps({"status":"FAIL","errors":errors},indent=2))
    raise SystemExit(1)

fields=list(rows[0].keys())
with (root/spec["adjudicated_matrix"]).open("w",newline="",encoding="utf-8") as f:
    w=csv.DictWriter(f,fieldnames=fields)
    w.writeheader();w.writerows(rows)

applicable=sum(1 for r in rows if r["applicability_state"]=="APPLICABLE")
not_applicable=sum(1 for r in rows if r["applicability_state"]=="NOT_APPLICABLE")

summary={
    "wave":"2D",
    "generated_at_utc":datetime.now(timezone.utc).isoformat(),
    "status":"PASS",
    "matrix_row_count":len(rows),
    "applicable_count":applicable,
    "not_applicable_count":not_applicable,
    "review_required_count":0,
    "pending_count":0,
    "coverage_complete":len(rows)==560,
    "evaluation_performed":False,
    "promotion_performed":False
}
(root/spec["adjudication_summary"]).write_text(json.dumps(summary,indent=2),encoding="utf-8")
print(json.dumps(summary,indent=2))
