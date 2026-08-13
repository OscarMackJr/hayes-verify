import argparse,csv,json
from pathlib import Path

ap=argparse.ArgumentParser()
ap.add_argument("--ems-root",required=True)
ap.add_argument("--record",required=True)
ap.add_argument("--queue",required=True)
ap.add_argument("--report",required=True)
a=ap.parse_args()

root=Path(a.ems_root)
record=json.loads(Path(a.record).read_text(encoding="utf-8"))
with Path(a.queue).open(encoding="utf-8-sig",newline="") as f:
    rows=list(csv.DictReader(f))

errors=[]
target=[r for r in rows if r.get("control_id")=="EMS-CTRL-072"]
if len(target)!=1:
    errors.append("CTRL-072 row missing/duplicated.")
else:
    t=target[0]
    if t.get("current_status")!="PASS": errors.append("CTRL-072 current_status must be PASS.")
    if t.get("evidence_sufficiency")!="SUFFICIENT": errors.append("CTRL-072 evidence_sufficiency must be SUFFICIENT.")
    if t.get("promotion_status")!="PROMOTED": errors.append("CTRL-072 promotion_status must be PROMOTED.")
    if t.get("remediation_state")!="CLOSED": errors.append("CTRL-072 remediation_state must be CLOSED.")

open_rows=[r for r in rows if r.get("remediation_state")=="OPEN"]
remaining=sorted(r["control_id"] for r in open_rows)
expected=sorted(record.get("remaining_open_controls",[]))

if len(open_rows)!=7:
    errors.append(f"Expected 7 open Wave 2C controls, found {len(open_rows)}.")
if remaining!=expected:
    errors.append(f"Remaining population mismatch. expected={expected} actual={remaining}")
if record.get("promotion_performed") is not True:
    errors.append("promotion_performed must be true in promotion record.")
if record.get("pre_open_count")!=8 or record.get("post_open_count")!=7:
    errors.append("Promotion record counts must reconcile 8 -> 7.")

dest=Path(record.get("authoritative_evidence",""))
if not dest.exists():
    errors.append(f"Authoritative evidence file missing: {dest}")

result={
    "status":"PASS" if not errors else "FAIL",
    "control_id":"EMS-CTRL-072",
    "open_remediation_count":len(open_rows),
    "remaining_open_controls":remaining,
    "errors":errors
}
Path(a.report).write_text(json.dumps(result,indent=2),encoding="utf-8")
print(json.dumps(result,indent=2))
raise SystemExit(0 if not errors else 1)
