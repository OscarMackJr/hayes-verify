import argparse,json
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument("--root",required=True);a=p.parse_args();o=Path(a.root)/"generated"/"wave2c"/"ai-governance";errs=[]
try:q=json.loads((o/"qualification.json").read_text())
except Exception as e:q={};errs.append("QUALIFICATION_MISSING")
if q.get("promotion_performed") is not False:errs.append("AUTOMATIC_PROMOTION_DETECTED")
if {x.get("control_id") for x in q.get("controls",[])}!={"EMS-CTRL-049","EMS-CTRL-050","EMS-CTRL-053"}:errs.append("CONTROL_POPULATION_MISMATCH")
for x in q.get("controls",[]):
 if x.get("remediation_state")!="OPEN":errs.append("PREMATURE_CLOSE:"+x["control_id"])
 if x.get("promotion_status")=="PROMOTED":errs.append("PREMATURE_PROMOTION:"+x["control_id"])
print(json.dumps({"status":"PASS" if not errs else "FAIL","errors":errs,"promotion_performed":False},indent=2));raise SystemExit(bool(errs))