import argparse,csv,json
from pathlib import Path
from datetime import datetime,timezone

ap=argparse.ArgumentParser()
ap.add_argument("--root",required=True)
ap.add_argument("--spec",required=True)
a=ap.parse_args()

root=Path(a.root).resolve()
spec=json.loads(Path(a.spec).read_text(encoding="utf-8"))
rows=list(csv.DictReader((root/spec["adjudicated_matrix"]).open(encoding="utf-8-sig",newline="")))
summary=json.loads((root/spec["adjudication_summary"]).read_text(encoding="utf-8"))

errors=[]
if len(rows)!=560: errors.append(f"row_count={len(rows)}, expected=560")
pairs={(r["control_id"],r["target_id"]) for r in rows}
if len(pairs)!=560: errors.append(f"unique_pair_count={len(pairs)}, expected=560")

for i,r in enumerate(rows,2):
    if r["applicability_state"] not in set(spec["allowed_states"]):
        errors.append(f"row {i}: invalid applicability state")
    if r["evaluation_state"]!="NOT_STARTED": errors.append(f"row {i}: evaluation_state changed")
    if r["evidence_state"]!="NOT_COLLECTED": errors.append(f"row {i}: evidence_state changed")
    if r["result_state"]!="NOT_EVALUATED": errors.append(f"row {i}: result_state changed")
    if r["promotion_state"]!="NOT_PROMOTED": errors.append(f"row {i}: promotion_state changed")

pending=sum(1 for r in rows if r["applicability_state"]=="PENDING_APPLICABILITY")
review=sum(1 for r in rows if r["applicability_state"]=="REVIEW_REQUIRED")
validation={
    "wave":"2D",
    "validated_at_utc":datetime.now(timezone.utc).isoformat(),
    "status":"PASS" if not errors else "FAIL",
    "matrix_row_count":len(rows),
    "unique_pair_count":len(pairs),
    "applicable_count":sum(1 for r in rows if r["applicability_state"]=="APPLICABLE"),
    "not_applicable_count":sum(1 for r in rows if r["applicability_state"]=="NOT_APPLICABLE"),
    "review_required_count":review,
    "pending_count":pending,
    "coverage_complete":len(rows)==560 and len(pairs)==560,
    "errors":errors,
    "evaluation_performed":False,
    "promotion_performed":False
}
(root/spec["adjudication_validation"]).write_text(json.dumps(validation,indent=2),encoding="utf-8")
print(json.dumps(validation,indent=2))
raise SystemExit(0 if not errors else 1)
