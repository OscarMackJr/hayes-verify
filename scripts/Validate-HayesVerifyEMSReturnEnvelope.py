import argparse, hashlib, json
from pathlib import Path
from jsonschema import Draft202012Validator

def sha256(path):
    h=hashlib.sha256()
    with path.open("rb") as f:
        for c in iter(lambda:f.read(1024*1024),b""): h.update(c)
    return h.hexdigest()

ap=argparse.ArgumentParser()
ap.add_argument("--root",required=True)
ap.add_argument("--spec",required=True)
ap.add_argument("--schema",required=True)
a=ap.parse_args()
root=Path(a.root).resolve()
spec=json.loads(Path(a.spec).read_text(encoding="utf-8"))
schema=json.loads(Path(a.schema).read_text(encoding="utf-8"))
envp=root/spec["return_envelope_output"]
certp=root/spec["certification_output"]
evidencep=root/spec["live_evidence"]
resultp=root/spec["live_result"]
env=json.loads(envp.read_text(encoding="utf-8"))
errors=[]
try:
    Draft202012Validator(schema).validate(env)
except Exception as exc:
    errors.append(f"schema validation failed: {exc}")
if env.get("acceptance_state")!="PENDING_EMS_ACCEPTANCE": errors.append("acceptance state invalid")
if env.get("promotion_state")!="NOT_PROMOTED": errors.append("promotion state invalid")
if env.get("evidence_sha256")!=sha256(evidencep): errors.append("evidence hash mismatch")
if env.get("result_sha256")!=sha256(resultp): errors.append("result hash mismatch")
if env.get("certification_sha256")!=sha256(certp): errors.append("certification hash mismatch")
val={"status":"PASS" if not errors else "FAIL","control_id":env.get("control_id"),"target_id":env.get("target_id"),
     "acceptance_state":env.get("acceptance_state"),"promotion_state":env.get("promotion_state"),"errors":errors}
out=root/spec["return_envelope_validation_output"]
out.write_text(json.dumps(val,indent=2),encoding="utf-8")
print(json.dumps(val,indent=2))
raise SystemExit(0 if not errors else 1)
