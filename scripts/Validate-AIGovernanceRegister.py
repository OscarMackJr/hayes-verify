import argparse,json,sys
from pathlib import Path

def validate_schema_shape(schema,obj):
    errors=[]
    if not isinstance(obj,dict): return ["Root must be object."]
    if "records" not in obj: return ["Missing records array."]
    if not isinstance(obj["records"],list): return ["records must be an array."]
    item_schema=schema["properties"]["records"]["items"]
    required=item_schema.get("required",[])
    props=item_schema.get("properties",{})
    for i,r in enumerate(obj["records"],start=1):
        if not isinstance(r,dict):
            errors.append(f"Record {i}: must be object."); continue
        for k in required:
            if k not in r:
                errors.append(f"Record {i}: missing required field {k}.")
            elif isinstance(r[k],str) and not r[k].strip():
                errors.append(f"Record {i}: field {k} is blank.")
        for k,v in r.items():
            ps=props.get(k,{})
            if "enum" in ps and v not in ps["enum"]:
                errors.append(f"Record {i}: {k}={v!r} not in {ps['enum']}.")
            if ps.get("type")=="boolean" and not isinstance(v,bool):
                errors.append(f"Record {i}: {k} must be boolean.")
            if ps.get("type")=="array":
                if not isinstance(v,list): errors.append(f"Record {i}: {k} must be array.")
                elif ps.get("minItems",0)>len(v): errors.append(f"Record {i}: {k} requires at least {ps['minItems']} item(s).")
    return errors

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--register",required=True)
    ap.add_argument("--schema",required=True)
    ap.add_argument("--report",required=True)
    a=ap.parse_args()

    reg=Path(a.register); sch=Path(a.schema)
    obj=json.loads(reg.read_text(encoding="utf-8"))
    schema=json.loads(sch.read_text(encoding="utf-8"))
    errors=validate_schema_shape(schema,obj)
    result={
        "status":"PASS" if not errors else "FAIL",
        "register":str(reg),
        "schema":str(sch),
        "record_count":len(obj.get("records",[])) if isinstance(obj,dict) else 0,
        "errors":errors
    }
    Path(a.report).write_text(json.dumps(result,indent=2),encoding="utf-8")
    print(json.dumps(result,indent=2))
    sys.exit(1 if errors else 0)

if __name__=="__main__": main()
