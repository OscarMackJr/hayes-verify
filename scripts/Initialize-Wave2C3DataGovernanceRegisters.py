import argparse,csv,json
from pathlib import Path

p=argparse.ArgumentParser()
p.add_argument("--root",required=True)
a=p.parse_args()

root=Path(a.root)
reg=root/"registers"/"wave2c"/"data-governance"
reg.mkdir(parents=True,exist_ok=True)

defs={
"data_classification_register.csv":[
    "record_id","system_or_dataset","data_classification","data_owner_or_steward",
    "review_date","reviewer","review_outcome","evidence_reference"
],
"data_retention_register.csv":[
    "record_id","data_scope_or_category","retention_period","retention_authority",
    "owner","execution_or_disposition","execution_date","evidence_reference"
],
"production_data_protection_register.csv":[
    "record_id","system_or_dataset","data_scope","protection_control_or_handling",
    "owner","validation_date","validation_result","evidence_reference"
]
}

for name,headers in defs.items():
    path=reg/name
    if not path.exists():
        with path.open("w",newline="",encoding="utf-8") as f:
            csv.writer(f).writerow(headers)

print(json.dumps({
    "status":"PASS",
    "register_count":len(defs),
    "registers":list(defs.keys()),
    "promotion_performed":False
},indent=2))
