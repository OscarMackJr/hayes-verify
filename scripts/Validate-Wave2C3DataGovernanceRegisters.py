import argparse,csv,json
from pathlib import Path
from datetime import datetime,timezone

p=argparse.ArgumentParser()
p.add_argument("--root",required=True)
p.add_argument("--report",required=True)
a=p.parse_args()

root=Path(a.root)
reg=root/"registers"/"wave2c"/"data-governance"
errors=[]
summary=[]

cfg={
"data_classification_register.csv":{
    "key":["record_id"],
    "required":["record_id","system_or_dataset","data_classification","data_owner_or_steward","review_date","reviewer","review_outcome","evidence_reference"]
},
"data_retention_register.csv":{
    "key":["record_id"],
    "required":["record_id","data_scope_or_category","retention_period","retention_authority","owner","execution_or_disposition","execution_date","evidence_reference"]
},
"production_data_protection_register.csv":{
    "key":["record_id"],
    "required":["record_id","system_or_dataset","data_scope","protection_control_or_handling","owner","validation_date","validation_result","evidence_reference"]
}
}

for name,c in cfg.items():
    path=reg/name
    if not path.exists():
        errors.append(f"MISSING_REGISTER:{name}")
        summary.append({"register":name,"record_count":0,"qualifying_record_count":0,"status":"FAIL"})
        continue
    with path.open(encoding="utf-8-sig",newline="") as f:
        rows=list(csv.DictReader(f))
    seen=set(); qualifying=0
    for idx,row in enumerate(rows,start=2):
        missing=[k for k in c["required"] if not str(row.get(k,"")).strip()]
        if missing:
            errors.append(f"{name}:row{idx}:MISSING_REQUIRED_FIELDS:{','.join(missing)}")
            continue
        key=tuple(str(row.get(k,"")).strip().lower() for k in c["key"])
        if key in seen:
            errors.append(f"{name}:row{idx}:DUPLICATE_KEY:{key}")
            continue
        seen.add(key); qualifying+=1
    summary.append({
        "register":name,
        "record_count":len(rows),
        "qualifying_record_count":qualifying,
        "status":"PASS" if len(rows)==qualifying else ("PASS" if len(rows)==0 else "FAIL")
    })

report={
    "wave":"2C.3",
    "validated_at_utc":datetime.now(timezone.utc).isoformat(),
    "status":"PASS" if not errors else "FAIL",
    "errors":errors,
    "registers":summary,
    "promotion_performed":False
}
Path(a.report).parent.mkdir(parents=True,exist_ok=True)
Path(a.report).write_text(json.dumps(report,indent=2),encoding="utf-8")
print(json.dumps(report,indent=2))
raise SystemExit(0 if not errors else 1)
