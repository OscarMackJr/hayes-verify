import argparse,csv,json
from pathlib import Path
from datetime import datetime,timezone

p=argparse.ArgumentParser()
p.add_argument("--root",required=True)
p.add_argument("--report",required=True)
a=p.parse_args()

root=Path(a.root)
path=root/"registers"/"wave2c"/"ems-review"/"annual_ems_review_register.csv"
errors=[]
rows=[]
if not path.exists():
    errors.append("MISSING_REGISTER")
else:
    with path.open(encoding="utf-8-sig",newline="") as f:
        rows=list(csv.DictReader(f))

seen=set()
qualifying=0
required=[
 "review_id","review_date","participants","findings_or_observations",
 "decisions","actions_and_owners","review_status","evidence_reference"
]

for idx,row in enumerate(rows,start=2):
    missing=[k for k in required if not str(row.get(k,"")).strip()]
    if missing:
        errors.append(f"row{idx}:MISSING_REQUIRED_FIELDS:{','.join(missing)}")
        continue
    key=row["review_id"].strip().lower()
    if key in seen:
        errors.append(f"row{idx}:DUPLICATE_REVIEW_ID:{key}")
        continue
    seen.add(key)
    if row["review_status"].strip().upper() not in {"COMPLETED","APPROVED","CLOSED"}:
        errors.append(f"row{idx}:INVALID_REVIEW_STATUS:{row['review_status']}")
        continue
    qualifying+=1

report={
 "wave":"2C.4",
 "validated_at_utc":datetime.now(timezone.utc).isoformat(),
 "status":"PASS" if not errors else "FAIL",
 "record_count":len(rows),
 "qualifying_record_count":qualifying,
 "errors":errors,
 "promotion_performed":False
}
Path(a.report).parent.mkdir(parents=True,exist_ok=True)
Path(a.report).write_text(json.dumps(report,indent=2),encoding="utf-8")
print(json.dumps(report,indent=2))
raise SystemExit(0 if not errors else 1)
