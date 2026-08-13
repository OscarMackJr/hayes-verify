import argparse,csv,json
from pathlib import Path

p=argparse.ArgumentParser()
p.add_argument("--root",required=True)
a=p.parse_args()

root=Path(a.root)
reg=root/"registers"/"wave2c"/"data-governance"
out=root/"generated"/"wave2c"/"data-governance"
out.mkdir(parents=True,exist_ok=True)

def load(name):
    with (reg/name).open(encoding="utf-8-sig",newline="") as f:
        return list(csv.DictReader(f))

def nz(row,*keys):
    return all(str(row.get(k,"")).strip() for k in keys)

classification=load("data_classification_register.csv")
retention=load("data_retention_register.csv")
protection=load("production_data_protection_register.csv")

assertions=[]
def add(cid,name,pop,predicate):
    q=sum(1 for r in pop if predicate(r))
    assertions.append({
        "control_id":cid,
        "assertion":name,
        "record_count":len(pop),
        "qualifying_record_count":q,
        "operating_evidence_sufficient":q>0,
        "reason":"QUALIFYING_RECORD_PRESENT" if q else ("EMPTY_REGISTER" if not pop else "NO_QUALIFYING_RECORD")
    })

add("EMS-CTRL-063","classification_recorded",classification,lambda r:nz(r,"record_id","system_or_dataset"))
add("EMS-CTRL-063","classification_level_recorded",classification,lambda r:nz(r,"data_classification"))
add("EMS-CTRL-063","data_owner_or_steward_recorded",classification,lambda r:nz(r,"data_owner_or_steward"))
add("EMS-CTRL-063","system_or_dataset_scope_recorded",classification,lambda r:nz(r,"system_or_dataset"))
add("EMS-CTRL-063","review_history_retained",classification,lambda r:nz(r,"review_date","reviewer","review_outcome","evidence_reference"))

add("EMS-CTRL-065","retention_schedule_recorded",retention,lambda r:nz(r,"record_id","data_scope_or_category"))
add("EMS-CTRL-065","retention_period_recorded",retention,lambda r:nz(r,"retention_period"))
add("EMS-CTRL-065","data_scope_or_category_recorded",retention,lambda r:nz(r,"data_scope_or_category"))
add("EMS-CTRL-065","owner_or_authority_recorded",retention,lambda r:nz(r,"retention_authority","owner"))
add("EMS-CTRL-065","retention_execution_or_disposition_evidence_retained",retention,lambda r:nz(r,"execution_or_disposition","execution_date","evidence_reference"))

add("EMS-CTRL-066","production_data_protection_recorded",protection,lambda r:nz(r,"record_id","system_or_dataset"))
add("EMS-CTRL-066","sensitive_or_production_data_scope_recorded",protection,lambda r:nz(r,"data_scope"))
add("EMS-CTRL-066","protection_control_or_handling_recorded",protection,lambda r:nz(r,"protection_control_or_handling"))
add("EMS-CTRL-066","owner_or_responsible_party_recorded",protection,lambda r:nz(r,"owner"))
add("EMS-CTRL-066","protection_validation_or_review_evidence_retained",protection,lambda r:nz(r,"validation_date","validation_result","evidence_reference"))

(out/"assertion_evidence.json").write_text(json.dumps({
    "wave":"2C.3",
    "assertions":assertions,
    "promotion_performed":False
},indent=2),encoding="utf-8")

names={
"EMS-CTRL-063":"Data Classification",
"EMS-CTRL-065":"Data Retention Compliance",
"EMS-CTRL-066":"Production Data Protection"
}

controls=[]
for cid,cname in names.items():
    aa=[x for x in assertions if x["control_id"]==cid]
    missing=[x["assertion"] for x in aa if not x["operating_evidence_sufficient"]]
    ok=not missing
    controls.append({
        "control_id":cid,
        "control_name":cname,
        "scope":"ORGANIZATION",
        "assertion_count":len(aa),
        "assertions_with_operating_evidence":len(aa)-len(missing),
        "status":"PASS" if ok else "WARNING",
        "sufficiency":"SUFFICIENT" if ok else "INSUFFICIENT",
        "promotion_eligible":ok,
        "promotion_status":"QUALIFIED_NOT_PROMOTED" if ok else "NOT_PROMOTED",
        "remediation_state":"OPEN",
        "missing_assertions":";".join(missing)
    })

(out/"qualification.json").write_text(json.dumps({
    "wave":"2C.3",
    "controls":controls,
    "promotion_performed":False
},indent=2),encoding="utf-8")

with (out/"qualification.csv").open("w",newline="",encoding="utf-8") as f:
    w=csv.DictWriter(f,fieldnames=controls[0].keys());w.writeheader();w.writerows(controls)

summary={
    "wave":"2C.3",
    "control_count":3,
    "promotion_eligible_count":sum(1 for c in controls if c["promotion_eligible"]),
    "gap_count":sum(1 for c in controls if not c["promotion_eligible"]),
    "promotion_performed":False
}
(out/"qualification_summary.json").write_text(json.dumps(summary,indent=2),encoding="utf-8")
print(json.dumps(summary,indent=2))
