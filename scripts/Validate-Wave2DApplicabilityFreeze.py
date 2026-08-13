import argparse,csv,json,hashlib
from pathlib import Path
from datetime import datetime,timezone

ap=argparse.ArgumentParser()
ap.add_argument("--root",required=True)
ap.add_argument("--spec",required=True)
a=ap.parse_args()

root=Path(a.root).resolve()
spec=json.loads(Path(a.spec).read_text(encoding="utf-8"))
freeze_path=root/spec["freeze_output"]
matrix_path=root/spec["adjudicated_matrix"]

freeze=json.loads(freeze_path.read_text(encoding="utf-8"))
rows=list(csv.DictReader(matrix_path.open(encoding="utf-8-sig",newline="")))

def sha256(p):
    h=hashlib.sha256()
    with p.open("rb") as f:
        for c in iter(lambda:f.read(1024*1024),b""): h.update(c)
    return h.hexdigest()

errors=[]
if freeze.get("status")!="PASS": errors.append("freeze status not PASS")
if freeze.get("freeze_state")!="FROZEN_FOR_EVALUATION": errors.append("freeze_state invalid")
if freeze.get("matrix_sha256")!=sha256(matrix_path): errors.append("matrix hash changed after freeze")
if len(rows)!=560: errors.append("matrix row count changed")
if sum(r["applicability_state"]=="APPLICABLE" for r in rows)!=410: errors.append("applicable count changed")
if sum(r["applicability_state"]=="NOT_APPLICABLE" for r in rows)!=150: errors.append("not-applicable count changed")
for i,r in enumerate(rows,2):
    if r["evaluation_state"]!="NOT_STARTED": errors.append(f"row {i}: evaluation_state changed")
    if r["evidence_state"]!="NOT_COLLECTED": errors.append(f"row {i}: evidence_state changed")
    if r["result_state"]!="NOT_EVALUATED": errors.append(f"row {i}: result_state changed")
    if r["promotion_state"]!="NOT_PROMOTED": errors.append(f"row {i}: promotion_state changed")

validation={
    "wave":"2D",
    "validated_at_utc":datetime.now(timezone.utc).isoformat(),
    "status":"PASS" if not errors else "FAIL",
    "matrix_row_count":len(rows),
    "applicable_count":sum(r["applicability_state"]=="APPLICABLE" for r in rows),
    "not_applicable_count":sum(r["applicability_state"]=="NOT_APPLICABLE" for r in rows),
    "review_required_count":sum(r["applicability_state"]=="REVIEW_REQUIRED" for r in rows),
    "pending_count":sum(r["applicability_state"]=="PENDING_APPLICABILITY" for r in rows),
    "errors":errors,
    "evaluation_performed":False,
    "promotion_performed":False
}
(root/spec["freeze_validation"]).write_text(json.dumps(validation,indent=2),encoding="utf-8")
print(json.dumps(validation,indent=2))
raise SystemExit(0 if not errors else 1)
