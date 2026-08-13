import argparse,csv,json
from pathlib import Path
from datetime import datetime,timezone

ap=argparse.ArgumentParser()
ap.add_argument("--root",required=True)
ap.add_argument("--spec",required=True)
a=ap.parse_args()

root=Path(a.root).resolve()
spec=json.loads(Path(a.spec).read_text(encoding="utf-8"))
matrix=list(csv.DictReader((root/spec["matrix_file"]).open(encoding="utf-8-sig",newline="")))
decisions=list(csv.DictReader((root/spec["decisions_output"]).open(encoding="utf-8-sig",newline="")))
dmap={(r["control_id"],r["target_id"]):r for r in decisions}

rows=[]
errors=[]
for r in matrix:
    key=(r["control_id"],r["target_id"])
    d=dmap.get(key)
    if not d:
        errors.append(f"missing applicability decision for {key}")
        continue
    state=d["decision"].strip().upper()
    if state not in set(spec["allowed_states"]):
        errors.append(f"invalid applicability state {state} for {key}")
        continue

    out=dict(r)
    out["applicability_state"]=state
    out["applicability_rationale"]=d.get("rationale","")
    out["applicability_owner"]=d.get("decision_owner","")
    # Preserve fail-closed non-evaluation state.
    out["evaluation_state"]="NOT_STARTED"
    out["evidence_state"]="NOT_COLLECTED"
    out["result_state"]="NOT_EVALUATED"
    out["promotion_state"]="NOT_PROMOTED"
    rows.append(out)

if errors:
    print(json.dumps({"status":"FAIL","errors":errors},indent=2))
    raise SystemExit(1)

out_path=root/spec["adjudicated_matrix"]
fields=list(rows[0].keys())
with out_path.open("w",newline="",encoding="utf-8") as f:
    w=csv.DictWriter(f,fieldnames=fields)
    w.writeheader();w.writerows(rows)

summary={
    "wave":"2D",
    "generated_at_utc":datetime.now(timezone.utc).isoformat(),
    "status":"PASS" if all(r["applicability_state"]!="REVIEW_REQUIRED" for r in rows) else "WARNING",
    "matrix_row_count":len(rows),
    "applicable_count":sum(1 for r in rows if r["applicability_state"]=="APPLICABLE"),
    "not_applicable_count":sum(1 for r in rows if r["applicability_state"]=="NOT_APPLICABLE"),
    "review_required_count":sum(1 for r in rows if r["applicability_state"]=="REVIEW_REQUIRED"),
    "pending_count":sum(1 for r in rows if r["applicability_state"]=="PENDING_APPLICABILITY"),
    "coverage_complete":len(rows)==560,
    "evaluation_performed":False,
    "promotion_performed":False
}
(root/spec["adjudication_summary"]).write_text(json.dumps(summary,indent=2),encoding="utf-8")
print(json.dumps(summary,indent=2))
