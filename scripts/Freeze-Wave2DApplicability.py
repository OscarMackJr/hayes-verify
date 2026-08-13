import argparse,csv,json,hashlib
from pathlib import Path
from datetime import datetime,timezone

ap=argparse.ArgumentParser()
ap.add_argument("--root",required=True)
ap.add_argument("--spec",required=True)
a=ap.parse_args()

root=Path(a.root).resolve()
spec=json.loads(Path(a.spec).read_text(encoding="utf-8"))

matrix_path=root/spec["adjudicated_matrix"]
summary_path=root/spec["applicability_summary"]
review_path=root/spec["human_review_record"]
scope_freeze_path=root/spec["scope_freeze"]
pop_freeze_path=root/spec["population_freeze"]

for p in [matrix_path,summary_path,review_path,scope_freeze_path,pop_freeze_path]:
    if not p.exists():
        raise SystemExit(f"Freeze blocked: missing {p}")

summary=json.loads(summary_path.read_text(encoding="utf-8"))
review=json.loads(review_path.read_text(encoding="utf-8"))
rows=list(csv.DictReader(matrix_path.open(encoding="utf-8-sig",newline="")))

errors=[]
checks={
 "matrix_row_count":len(rows),
 "applicable_count":sum(r["applicability_state"]=="APPLICABLE" for r in rows),
 "not_applicable_count":sum(r["applicability_state"]=="NOT_APPLICABLE" for r in rows),
 "review_required_count":sum(r["applicability_state"]=="REVIEW_REQUIRED" for r in rows),
 "pending_count":sum(r["applicability_state"]=="PENDING_APPLICABILITY" for r in rows),
}

for k,expected in [
    ("matrix_row_count",spec["expected_matrix_rows"]),
    ("applicable_count",spec["expected_applicable_count"]),
    ("not_applicable_count",spec["expected_not_applicable_count"]),
    ("review_required_count",spec["expected_review_required_count"]),
    ("pending_count",spec["expected_pending_count"])
]:
    if checks[k]!=expected:
        errors.append(f"{k}={checks[k]}, expected={expected}")

if summary.get("status")!="PASS":
    errors.append("applicability summary is not PASS")
if review.get("status")!="PASS":
    errors.append("human review record is not PASS")
if int(review.get("remaining_review_required_count",-1))!=0:
    errors.append("human review still has unresolved rows")

for i,r in enumerate(rows,2):
    if r["evaluation_state"]!="NOT_STARTED":
        errors.append(f"row {i}: evaluation_state changed")
    if r["evidence_state"]!="NOT_COLLECTED":
        errors.append(f"row {i}: evidence_state changed")
    if r["result_state"]!="NOT_EVALUATED":
        errors.append(f"row {i}: result_state changed")
    if r["promotion_state"]!="NOT_PROMOTED":
        errors.append(f"row {i}: promotion_state changed")

if errors:
    print(json.dumps({"status":"FAIL","errors":errors},indent=2))
    raise SystemExit(1)

def sha256(p):
    h=hashlib.sha256()
    with p.open("rb") as f:
        for c in iter(lambda:f.read(1024*1024),b""): h.update(c)
    return h.hexdigest()

freeze={
    "wave":"2D",
    "frozen_at_utc":datetime.now(timezone.utc).isoformat(),
    "status":"PASS",
    **checks,
    "coverage_complete":True,
    "matrix_sha256":sha256(matrix_path),
    "applicability_summary_sha256":sha256(summary_path),
    "human_review_record_sha256":sha256(review_path),
    "scope_freeze_sha256":sha256(scope_freeze_path),
    "population_freeze_sha256":sha256(pop_freeze_path),
    "evaluation_performed":False,
    "promotion_performed":False,
    "freeze_state":"FROZEN_FOR_EVALUATION"
}
out=root/spec["freeze_output"]
out.parent.mkdir(parents=True,exist_ok=True)
out.write_text(json.dumps(freeze,indent=2),encoding="utf-8")
print(json.dumps(freeze,indent=2))
