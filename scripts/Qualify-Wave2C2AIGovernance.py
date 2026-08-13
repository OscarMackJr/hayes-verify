import argparse,json,csv
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument("--root",required=True);a=p.parse_args();o=Path(a.root)/"generated"/"wave2c"/"ai-governance"
e=json.loads((o/"assertion_evidence.json").read_text())["assertions"];names={"EMS-CTRL-049":"Approved AI Platforms","EMS-CTRL-050":"Prompt Data Classification","EMS-CTRL-053":"AI Security Review"};rows=[]
for c,n in names.items():
 x=[z for z in e if z["control_id"]==c];m=[z["assertion"] for z in x if not z["operating_evidence_sufficient"]];ok=not m
 rows.append({"control_id":c,"control_name":n,"scope":"ORGANIZATION","status":"PASS" if ok else "WARNING","sufficiency":"SUFFICIENT" if ok else "INSUFFICIENT","promotion_eligible":ok,"promotion_status":"QUALIFIED_NOT_PROMOTED" if ok else "NOT_PROMOTED","remediation_state":"OPEN","missing_assertions":";".join(m)})
(o/"qualification.json").write_text(json.dumps({"wave":"2C.2","controls":rows,"promotion_performed":False},indent=2))
print(json.dumps({"control_count":3,"promotion_eligible_count":sum(x["promotion_eligible"] for x in rows),"gap_count":sum(not x["promotion_eligible"] for x in rows),"promotion_performed":False},indent=2))