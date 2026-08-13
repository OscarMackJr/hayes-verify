import argparse,json,sys
from pathlib import Path

ap=argparse.ArgumentParser()
ap.add_argument("--register",required=True)
ap.add_argument("--schema",required=True)
ap.add_argument("--report",required=True)
a=ap.parse_args()

obj=json.loads(Path(a.register).read_text(encoding="utf-8"))
schema=json.loads(Path(a.schema).read_text(encoding="utf-8"))
errors=[]
records=obj.get("records")

if not isinstance(records,list):
    errors.append("records must be an array.")
    records=[]
else:
    item=schema["properties"]["records"]["items"]
    required=item["required"]
    props=item["properties"]
    for i,r in enumerate(records,1):
        if not isinstance(r,dict):
            errors.append(f"Record {i}: must be an object.")
            continue
        for key in required:
            if key not in r:
                errors.append(f"Record {i}: missing required field {key}.")
            elif isinstance(r[key],str) and not r[key].strip():
                errors.append(f"Record {i}: field {key} is blank.")
        for key,val in r.items():
            p=props.get(key,{})
            if "enum" in p and val not in p["enum"]:
                errors.append(f"Record {i}: invalid {key}={val!r}.")

result={"status":"PASS" if not errors else "FAIL","record_count":len(records),"errors":errors}
Path(a.report).write_text(json.dumps(result,indent=2),encoding="utf-8")
print(json.dumps(result,indent=2))
sys.exit(1 if errors else 0)
