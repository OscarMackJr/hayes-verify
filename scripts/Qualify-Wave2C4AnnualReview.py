import argparse,csv,json
from pathlib import Path

p=argparse.ArgumentParser()
p.add_argument("--root",required=True)
a=p.parse_args()

root=Path(a.root)
reg=root/"registers"/"wave2c"/"ems-review"/"annual_ems_review_register.csv"
out=root/"generated"/"wave2c"/"annual-review"
out.mkdir(parents=True,exist_ok=True)

with reg.open(encoding="utf-8-sig",newline="") as f:
    rows=list(csv.DictReader(f))

def nz(row,*keys):
    return all(str(row.get(k,"")).strip() for k in keys)

assertions=[]
def add(name,pred):
    q=sum(1 for r in rows if pred(r))
    assertions.append({
      "control_id":"EMS-CTRL-080",
      "assertion":name,
      "record_count":len(rows),
      "qualifying_record_count":q,
      "operating_evidence_sufficient":q>0,
      "reason":"QUALIFYING_RECORD_PRESENT" if q else ("EMPTY_REGISTER" if not rows else "NO_QUALIFYING_RECORD")
    })

add("annual_review_recorded",lambda r:nz(r,"review_id","review_status"))
add("review_date_recorded",lambda r:nz(r,"review_date"))
add("participants_recorded",lambda r:nz(r,"participants"))
add("findings_or_observations_recorded",lambda r:nz(r,"findings_or_observations"))
add("decisions_recorded",lambda r:nz(r,"decisions"))
add("actions_and_owners_recorded",lambda r:nz(r,"actions_and_owners"))
add("evidence_reference_retained",lambda r:nz(r,"evidence_reference"))

missing=[x["assertion"] for x in assertions if not x["operating_evidence_sufficient"]]
eligible=not missing

(out/"assertion_evidence.json").write_text(json.dumps({
 "wave":"2C.4","assertions":assertions,"promotion_performed":False
},indent=2),encoding="utf-8")

qualification={
 "wave":"2C.4",
 "control":{
   "control_id":"EMS-CTRL-080",
   "control_name":"Annual EMS Review",
   "scope":"EMS",
   "status":"PASS" if eligible else "WARNING",
   "sufficiency":"SUFFICIENT" if eligible else "INSUFFICIENT",
   "promotion_eligible":eligible,
   "promotion_status":"QUALIFIED_NOT_PROMOTED" if eligible else "NOT_PROMOTED",
   "remediation_state":"OPEN",
   "missing_assertions":";".join(missing)
 },
 "promotion_performed":False
}
(out/"qualification.json").write_text(json.dumps(qualification,indent=2),encoding="utf-8")
print(json.dumps(qualification,indent=2))
