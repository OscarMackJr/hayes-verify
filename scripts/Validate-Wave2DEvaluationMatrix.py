import argparse,csv,json
from pathlib import Path
from datetime import datetime,timezone

ap=argparse.ArgumentParser()
ap.add_argument("--root",required=True)
ap.add_argument("--spec",required=True)
a=ap.parse_args()
root=Path(a.root).resolve()
spec=json.loads(Path(a.spec).read_text(encoding="utf-8"))

rows=list(csv.DictReader((root/spec["matrix_file"]).open(encoding="utf-8-sig",newline="")))
summary=json.loads((root/spec["matrix_summary"]).read_text(encoding="utf-8"))

errors=[]
expected=spec["expected_matrix_rows"]
if len(rows)!=expected: errors.append(f"matrix rows={len(rows)}, expected={expected}")

pairs={(r["control_id"],r["target_id"]) for r in rows}
if len(pairs)!=expected: errors.append(f"unique control-target pairs={len(pairs)}, expected={expected}")

states=set(spec["applicability_states"])
for i,r in enumerate(rows,2):
    if r["applicability_state"] not in states:
        errors.append(f"row {i}: invalid applicability_state={r['applicability_state']}")
    if r["evaluation_state"]!="NOT_STARTED":
        errors.append(f"row {i}: evaluation_state must be NOT_STARTED")
    if r["evidence_state"]!="NOT_COLLECTED":
        errors.append(f"row {i}: evidence_state must be NOT_COLLECTED")
    if r["result_state"]!="NOT_EVALUATED":
        errors.append(f"row {i}: result_state must be NOT_EVALUATED")
    if r["promotion_state"]!="NOT_PROMOTED":
        errors.append(f"row {i}: promotion_state must be NOT_PROMOTED")

if summary.get("evaluation_performed") is not False: errors.append("summary evaluation_performed must be false")
if summary.get("promotion_performed") is not False: errors.append("summary promotion_performed must be false")
if summary.get("coverage_complete") is not True: errors.append("summary coverage_complete must be true")

validation={
    "wave":"2D",
    "validated_at_utc":datetime.now(timezone.utc).isoformat(),
    "status":"PASS" if not errors else "FAIL",
    "matrix_row_count":len(rows),
    "unique_pair_count":len(pairs),
    "expected_matrix_row_count":expected,
    "pending_applicability_count":sum(1 for r in rows if r["applicability_state"]=="PENDING_APPLICABILITY"),
    "errors":errors,
    "evaluation_performed":False,
    "promotion_performed":False
}
(root/spec["matrix_validation"]).write_text(json.dumps(validation,indent=2),encoding="utf-8")
print(json.dumps(validation,indent=2))
raise SystemExit(0 if not errors else 1)
