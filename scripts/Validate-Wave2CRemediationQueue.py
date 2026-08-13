import argparse,csv,json
from pathlib import Path
ap=argparse.ArgumentParser();ap.add_argument("--outdir",required=True);ap.add_argument("--report",required=True);a=ap.parse_args()
out=Path(a.outdir); errors=[]
required=[out/"remediation_queue.csv",out/"evidence_requirements.csv",out/"remediation_summary.json",out/"wave2c_initialization.json"]
for p in required:
    if not p.exists(): errors.append(f"Missing artifact: {p}")
rows=[]
if (out/"remediation_queue.csv").exists():
    with (out/"remediation_queue.csv").open(encoding="utf-8-sig",newline="") as f: rows=list(csv.DictReader(f))
if len(rows)!=8: errors.append(f"Expected 8 remediation controls; found {len(rows)}.")
ids=[r.get("control_id","") for r in rows]
if len(ids)!=len(set(ids)): errors.append("Duplicate control_id values.")
for r in rows:
    if r.get("remediation_state")!="OPEN": errors.append(f"{r.get('control_id')}: remediation_state must be OPEN.")
    if r.get("promotion_eligible")!="False": errors.append(f"{r.get('control_id')}: promotion_eligible must be False.")
    if r.get("promotion_status")!="NOT_PROMOTED": errors.append(f"{r.get('control_id')}: promotion_status must be NOT_PROMOTED.")
    if r.get("evidence_sufficiency")!="INSUFFICIENT": errors.append(f"{r.get('control_id')}: evidence_sufficiency must be INSUFFICIENT.")
    if r.get("intake_classification") not in {"MANUAL","HYBRID","AUTOMATABLE"}: errors.append(f"{r.get('control_id')}: invalid classification.")
if (out/"remediation_summary.json").exists():
    s=json.loads((out/"remediation_summary.json").read_text())
    if int(s.get("promotion_eligible_count",-1))!=0: errors.append("promotion_eligible_count must be 0.")
if (out/"wave2c_initialization.json").exists():
    i=json.loads((out/"wave2c_initialization.json").read_text())
    if i.get("promotion_performed") is not False: errors.append("promotion_performed must be false.")
result={"status":"PASS" if not errors else "FAIL","control_count":len(rows),"errors":errors,"promotion_performed":False}
Path(a.report).write_text(json.dumps(result,indent=2),encoding="utf-8"); print(json.dumps(result,indent=2))
raise SystemExit(0 if not errors else 1)
