import argparse,csv,json
from pathlib import Path
from datetime import datetime,timezone

p=argparse.ArgumentParser()
p.add_argument("--root",required=True)
p.add_argument("--report",required=True)
a=p.parse_args()

root=Path(a.root)
spec=json.loads((root/"registry"/"wave2c2a_ai_governance_capture_spec.json").read_text(encoding="utf-8"))
reg=root/"registers"/"wave2c"/"ai-governance"
errors=[]
summary=[]

for name,cfg in spec["registers"].items():
    path=reg/name
    if not path.exists():
        errors.append(f"MISSING_REGISTER:{name}")
        summary.append({"register":name,"record_count":0,"qualifying_record_count":0,"status":"FAIL"})
        continue

    with path.open(encoding="utf-8-sig",newline="") as f:
        rows=list(csv.DictReader(f))

    keys=cfg["key_fields"]
    seen=set()
    q=0

    for idx,row in enumerate(rows, start=2):
        missing=[k for k in cfg["required_fields"] if not str(row.get(k,"")).strip()]
        if missing:
            errors.append(f"{name}:row{idx}:MISSING_REQUIRED_FIELDS:{','.join(missing)}")
            continue

        key=tuple(str(row.get(k,"")).strip().lower() for k in keys)
        if key in seen:
            errors.append(f"{name}:row{idx}:DUPLICATE_KEY:{key}")
            continue
        seen.add(key)
        q+=1

    summary.append({
        "register":name,
        "record_count":len(rows),
        "qualifying_record_count":q,
        "status":"PASS" if len(rows)==q else ("PASS" if len(rows)==0 else "FAIL")
    })

report={
    "wave":"2C.2a",
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
