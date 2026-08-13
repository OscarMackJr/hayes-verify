import argparse,csv,json
from pathlib import Path

ap=argparse.ArgumentParser()
ap.add_argument("--root",required=True)
ap.add_argument("--spec",required=True)
a=ap.parse_args()

root=Path(a.root).resolve()
spec=json.loads(Path(a.spec).read_text(encoding="utf-8"))
path=root/spec["review_import"]
if not path.exists():
    raise SystemExit(f"Human review decisions file missing: {path}")

rows=list(csv.DictReader(path.open(encoding="utf-8-sig",newline="")))
allowed=set(spec["allowed_human_decisions"])
errors=[]

seen=set()
for idx,r in enumerate(rows,2):
    key=(r.get("control_id",""),r.get("target_id",""))
    if key in seen:
        errors.append(f"row {idx}: duplicate control-target pair {key}")
    seen.add(key)

    decision=(r.get("human_decision") or "").strip().upper()
    rationale=(r.get("human_rationale") or "").strip()
    owner=(r.get("human_decision_owner") or "").strip()
    source=(r.get("human_decision_source") or "").strip()

    if decision not in allowed:
        errors.append(f"row {idx}: human_decision must be APPLICABLE or NOT_APPLICABLE")
    if not rationale:
        errors.append(f"row {idx}: human_rationale required")
    if not owner:
        errors.append(f"row {idx}: human_decision_owner required")
    if not source.startswith(spec["human_source_prefix"]):
        errors.append(f"row {idx}: human_decision_source must begin with HUMAN_")

expected=spec["expected_review_count"]
if len(rows)!=expected:
    errors.append(f"review decision row count={len(rows)}, expected={expected}")

print(json.dumps({
    "status":"PASS" if not errors else "FAIL",
    "row_count":len(rows),
    "expected_row_count":expected,
    "errors":errors
},indent=2))
raise SystemExit(0 if not errors else 1)
