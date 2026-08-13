import argparse,csv,json
from pathlib import Path

ap=argparse.ArgumentParser()
ap.add_argument("--record",required=True)
ap.add_argument("--queue",required=True)
ap.add_argument("--report",required=True)
a=ap.parse_args()

record=json.loads(Path(a.record).read_text(encoding="utf-8"))
with Path(a.queue).open(encoding="utf-8-sig",newline="") as f:
    rows=list(csv.DictReader(f))

errors=[]
promoted={"EMS-CTRL-063","EMS-CTRL-065","EMS-CTRL-066"}

for cid in promoted:
    rr=[r for r in rows if r.get("control_id")==cid]
    if len(rr)!=1:
        errors.append(f"{cid}: row missing/duplicated")
        continue
    r=rr[0]
    for k,v in {
        "current_status":"PASS",
        "evidence_sufficiency":"SUFFICIENT",
        "promotion_status":"PROMOTED",
        "remediation_state":"CLOSED"
    }.items():
        if r.get(k)!=v:
            errors.append(f"{cid}: {k}={r.get(k)} expected={v}")

open_rows=[r for r in rows if r.get("remediation_state")=="OPEN"]
remaining=sorted(r["control_id"] for r in open_rows)

if len(open_rows)!=1:
    errors.append(f"Expected 1 open control, found {len(open_rows)}")
if remaining!=["EMS-CTRL-080"]:
    errors.append(f"Expected EMS-CTRL-080 as sole remaining open control, actual={remaining}")
if record.get("promotion_performed") is not True:
    errors.append("promotion_performed must be true")
if record.get("pre_open_count")!=4 or record.get("post_open_count")!=1:
    errors.append("Population counts must reconcile 4 -> 1")
for e in record.get("evidence_files",[]):
    if not Path(e["path"]).exists():
        errors.append(f"Missing authoritative evidence {e['path']}")

result={
    "status":"PASS" if not errors else "FAIL",
    "promoted_controls":sorted(promoted),
    "open_remediation_count":len(open_rows),
    "remaining_open_controls":remaining,
    "errors":errors
}
Path(a.report).write_text(json.dumps(result,indent=2),encoding="utf-8")
print(json.dumps(result,indent=2))
raise SystemExit(0 if not errors else 1)
