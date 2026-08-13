import argparse, hashlib, json
from pathlib import Path
from jsonschema import Draft202012Validator
def load(p): return json.loads(p.read_text(encoding="utf-8-sig"))
def sha(p):
    h=hashlib.sha256()
    with p.open("rb") as f:
        for c in iter(lambda:f.read(1024*1024),b""): h.update(c)
    return h.hexdigest()
def rp(root,rel): return root/Path(rel.replace("\\","/"))
ap=argparse.ArgumentParser();ap.add_argument("--root",required=True);ap.add_argument("--spec",required=True);ap.add_argument("--schema",required=True)
a=ap.parse_args();root=Path(a.root).resolve();spec=load(Path(a.spec));schema=load(Path(a.schema))
env=load(rp(root,spec["return_envelope_output"]));errors=[]
try: Draft202012Validator(schema).validate(env)
except Exception as exc: errors.append(str(exc))
if env.get("acceptance_state")!="PENDING_EMS_ACCEPTANCE": errors.append("acceptance invalid")
if env.get("promotion_state")!="NOT_PROMOTED": errors.append("promotion invalid")
if env.get("evidence_sha256")!=sha(rp(root,spec["live_evidence"])): errors.append("evidence hash mismatch")
if env.get("result_sha256")!=sha(rp(root,spec["live_result"])): errors.append("result hash mismatch")
if env.get("certification_sha256")!=sha(rp(root,spec["certification_output"])): errors.append("certification hash mismatch")
out={"status":"PASS" if not errors else "FAIL","control_id":"EMS-CTRL-010","target_id":"REPO-001","errors":errors}
rp(root,spec["return_envelope_validation_output"]).write_text(json.dumps(out,indent=2),encoding="utf-8");print(json.dumps(out,indent=2));raise SystemExit(0 if not errors else 1)
